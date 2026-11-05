"""Episode loop. Owns the agent call order, per-episode seeding and per-step sanity checks.

Each episode gets a FRESH env built with its own env seed, and the global np.random is seeded with
the same value. That makes episode i identical in its random inputs for every agent (common random
numbers), even though agents produce different episode lengths (RECON risk 3).

Per-step checks (raise SlateError, never silently continue):
  * the slate has exactly k integer indices into the CURRENT candidate set;
  * the clusters RecSim reports for the shown items equal the clusters of those indices in the
    observation the agent acted on (proves the agent sees the current candidates, not stale ones).
Duplicate items within a slate are allowed by RecSim; they are counted, not hidden.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np

from slateq_study import seeding
from slateq_study.agents.base import Agent
from slateq_study.config import EnvConfig
from slateq_study.envs import make_env, true_user_state
from slateq_study.metrics import EpisodeRecord

log = logging.getLogger(__name__)


class SlateError(RuntimeError):
    """An agent produced an invalid slate, or the env and agent disagree on the candidates."""


@dataclass
class EpisodeResult:
    record: EpisodeRecord
    trace: list[dict] = field(default_factory=list)  # empty unless trace=True


def _check_slate(slate, obs, k: int) -> list[int]:
    arr = np.asarray(slate)
    n = len(obs["doc"])
    if arr.shape != (k,) or not np.issubdtype(arr.dtype, np.integer):
        raise SlateError(f"slate must be {k} integers, got {slate!r}")
    if arr.min() < 0 or arr.max() >= n:
        raise SlateError(f"slate index out of range [0, {n}): {slate!r}")
    return [int(i) for i in arr]


def _check_current_candidates(slate: list[int], obs_before, obs_after) -> None:
    docs = list(obs_before["doc"].values())
    expected = [int(np.argmax(docs[i])) for i in slate]  # doc features are one-hot clusters
    shown = [int(r["cluster_id"]) for r in obs_after["response"]]
    if expected != shown:
        raise SlateError(f"env showed clusters {shown}, agent chose clusters {expected}")


def run_episode(
    agent: Agent, env_cfg: EnvConfig, env_seed: int, episode: int = 0, trace: bool = False
) -> EpisodeResult:
    seeding.seed_global(env_seed)
    env = make_env(env_cfg, env_seed)
    obs = env.reset()
    if agent.privileged:
        agent.attach_true_state(env)
    k = env_cfg.slate_size
    slate = _check_slate(agent.begin_episode(obs), obs, k)
    total, length, clicks, duplicates, qualities, steps = 0.0, 0, 0, 0, [], []
    terminated = truncated = False
    while True:
        duplicates += int(len(set(slate)) < len(slate))
        obs_before = obs
        obs, reward, done, _ = env.step(slate)
        _check_current_candidates(slate, obs_before, obs)
        reward = float(reward)
        total += reward
        length += 1
        clicked_pos = next((i for i, r in enumerate(obs["response"]) if r["click"]), -1)
        if clicked_pos >= 0:
            clicks += 1
            qualities.append(float(obs["response"][clicked_pos]["quality"]))
        if trace:
            steps.append(
                _trace_step(episode, length - 1, slate, obs_before, obs, reward, clicked_pos, env)
            )
        terminated = bool(done)
        truncated = (not terminated) and length >= env_cfg.max_steps
        if terminated or truncated:
            agent.end_episode(reward, obs)
            break
        slate = _check_slate(agent.step(reward, obs), obs, k)
    if truncated:
        log.warning("episode %d (env_seed %d) truncated at max_steps=%d", episode, env_seed, length)
    record = EpisodeRecord(
        episode=episode,
        env_seed=env_seed,
        total_reward=total,
        length=length,
        clicks=clicks,
        mean_clicked_quality=float(np.mean(qualities)) if qualities else float("nan"),
        terminated=terminated,
        truncated=truncated,
        duplicate_slates=duplicates,
    )
    return EpisodeResult(record, steps)


def _trace_step(episode, t, slate, obs_before, obs_after, reward, clicked_pos, env) -> dict:
    """One per-step trace row for the trajectory figures. `time_budget_after` is PRIVILEGED
    (read from the simulator for plotting only); everything else is in the observation."""
    resp = obs_after["response"]
    return {
        "episode": episode,
        "t": t,
        "user_interests": [round(float(x), 6) for x in obs_before["user"]],
        "slate": slate,
        "slate_clusters": [int(r["cluster_id"]) for r in resp],
        "slate_qualities": [round(float(r["quality"]), 6) for r in resp],
        "clicked_pos": clicked_pos,
        "reward": reward,
        "time_budget_after": float(np.asarray(true_user_state(env).time_budget).item()),
    }


def evaluate(
    agent: Agent,
    env_cfg: EnvConfig,
    run_seed: int,
    n_episodes: int,
    stream: str = "eval",
    trace_episodes: int = 0,
) -> tuple[list[EpisodeRecord], list[dict]]:
    """Evaluation on a seed stream (default EVAL, shared by all agents -> paired comparisons).
    Traces are kept for the FIRST `trace_episodes` episodes (a fixed rule; PROTOCOL S5)."""
    agent.set_eval_mode(True)
    records, traces = [], []
    for ep in range(n_episodes):
        res = run_episode(
            agent,
            env_cfg,
            seeding.env_seed(stream, run_seed, ep),
            episode=ep,
            trace=ep < trace_episodes,
        )
        log.info(
            "%s episode %d: reward=%.3f length=%d",
            stream,
            ep,
            res.record.total_reward,
            res.record.length,
        )
        records.append(res.record)
        traces.extend(res.trace)
    return records, traces
