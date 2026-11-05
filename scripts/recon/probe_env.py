"""Phase 0: probe RecSim Interest Evolution on the modern stack.
Writes results/recon/env_probe.json.

Checks hypotheses H5/H6 and documents reward, termination, observation content, resampling and RNG.
"""

from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

from slateq_study import recsim_compat

recsim_compat.install()  # must precede any recsim import
import numpy as np
from recsim import choice_model
from recsim.agents import random_agent
from recsim.environments import interest_evolution as ie

OUT = Path(__file__).resolve().parents[2] / "results" / "recon" / "env_probe.json"


def make(n, k, seed):
    return ie.create_environment(
        {"num_candidates": n, "slate_size": k, "resample_documents": True, "seed": seed}
    )


def run_random_episode(env, agent_seed=0, global_seed=None, trace=False):
    if global_seed is not None:
        np.random.seed(global_seed)
    agent = random_agent.RandomAgent(env.action_space, random_seed=agent_seed)
    obs = env.reset()
    user_state = env._environment.user_model._user_state  # internal, for probing only
    budgets, steps, reward_mismatch, total = [user_state.time_budget], [], 0, 0.0
    doc_id_changes, done, r = 0, False, 0.0
    while not done:
        prev_ids = list(obs["doc"].keys())
        slate = agent.step(r, obs)
        obs, r, done, _ = env.step(slate)
        resp = obs["response"]
        recomputed = sum(float(x["watch_time"]) for x in resp if x["click"])
        reward_mismatch += int(abs(recomputed - r) > 1e-9)
        doc_id_changes += int(prev_ids != list(obs["doc"].keys()))
        total += r
        budgets.append(user_state.time_budget)
        if trace:
            steps.append({"slate": [int(s) for s in slate], "reward": float(r)})
    return {
        "length": len(budgets) - 1,
        "total_reward": total,
        "reward_mismatch_steps": reward_mismatch,
        "steps_where_candidate_ids_changed": doc_id_changes,
        "final_budget": float(np.asarray(budgets[-1]).item()),
        "budget_at_second_last_step": float(np.asarray(budgets[-2]).item()),
        "steps": steps,
    }


def main():
    out = {"tensorflow_imported": "tensorflow" in sys.modules}
    env = make(10, 3, seed=0)
    obs = env.reset()
    out["obs_keys"] = list(obs.keys())
    out["user_obs_shape"] = list(np.shape(obs["user"]))
    out["user_obs_equals_true_interests"] = bool(
        np.array_equal(obs["user"], env._environment.user_model._user_state.user_interests)
    )
    first_doc = next(iter(obs["doc"].values()))
    out["doc_obs_shape"] = list(np.shape(first_doc))
    out["doc_obs_is_one_hot"] = bool(np.isin(first_doc, [0.0, 1.0]).all() and first_doc.sum() == 1)
    out["num_docs_in_obs"] = len(obs["doc"])
    out["action_space"] = repr(env.action_space)
    out["response_fields"] = list(env.observation_space["response"][0].spaces.keys())
    out["env_true_choice_model"] = type(env._environment.user_model.choice_model).__name__
    out["choice_model_classes"] = sorted(
        n
        for n, c in inspect.getmembers(choice_model, inspect.isclass)
        if c.__module__ == choice_model.__name__ and n.endswith("ChoiceModel")
    )
    us = env._environment.user_model._user_state
    out["user_params"] = {
        k: (None if v is None else float(np.asarray(v).item()))
        for k, v in vars(us).items()
        if not isinstance(v, (set, np.ndarray, dict))
    }
    out["user_choice_features"] = us.choice_features

    ep = run_random_episode(make(10, 3, seed=0), global_seed=123)
    ep.pop("steps")
    out["random_episode_N10_k3"] = ep

    # Determinism: same env seed + same global np.random seed vs. different global seed.
    a = run_random_episode(make(10, 3, 7), global_seed=1, trace=True)["steps"]
    b = run_random_episode(make(10, 3, 7), global_seed=1, trace=True)["steps"]
    c = run_random_episode(make(10, 3, 7), global_seed=2, trace=True)["steps"]
    out["determinism"] = {
        "same_env_seed_same_global_seed_identical": a == b,
        "same_env_seed_different_global_seed_identical": a == c,
    }

    # Episode-length distribution under the random agent (20 users, N=10, k=3).
    lengths = [run_random_episode(make(10, 3, s), global_seed=s)["length"] for s in range(20)]
    out["random_lengths_20_users"] = {
        "min": min(lengths),
        "max": max(lengths),
        "mean": float(np.mean(lengths)),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
