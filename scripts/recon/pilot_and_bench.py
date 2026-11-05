"""Phase 0 PILOT (not a result): random vs oracle-myopic (GreedyPCTR) + throughput benchmarks.

Writes results/recon/pilot_and_bench.json. Every number in it is labelled PILOT / BENCH.
Common random numbers: episode i of seed s uses env seed = 1000*s + i and np.random.seed(same)
for BOTH agents, so each agent faces the same sequence of users at episode start.
"""

from __future__ import annotations

import itertools
import json
import math
import time
from pathlib import Path

from slateq_study import recsim_compat

recsim_compat.install()  # must precede any recsim import
import numpy as np
import torch
from recsim.agents import greedy_pctr_agent, random_agent
from recsim.environments import interest_evolution as ie

OUT = Path(__file__).resolve().parents[2] / "results" / "recon" / "pilot_and_bench.json"
CELLS = [(5, 2), (10, 3), (20, 5)]
SEEDS = [0, 1]
EPISODES = 100


def episode(agent_name, n, k, env_seed):
    np.random.seed(env_seed)
    env = ie.create_environment(
        {"num_candidates": n, "slate_size": k, "resample_documents": True, "seed": env_seed}
    )
    obs = env.reset()
    if agent_name == "random":
        agent = random_agent.RandomAgent(env.action_space, random_seed=env_seed)
    else:  # oracle myopic: given the TRUE user state object (privileged access)
        agent = greedy_pctr_agent.GreedyPCTRAgent(
            env.action_space, belief_state=env._environment.user_model._user_state
        )
    total, length, clicks, qual, r, done = 0.0, 0, 0, [], 0.0, False
    t0 = time.perf_counter()
    while not done:
        slate = agent.step(r, obs)
        obs, r, done, _ = env.step(slate)
        total += r
        length += 1
        for resp in obs["response"]:
            if resp["click"]:
                clicks += 1
                qual.append(float(resp["quality"]))
    dt = time.perf_counter() - t0
    return total, length, clicks, (float(np.mean(qual)) if qual else float("nan")), dt


def pilot():
    rows = []
    for (n, k), seed, agent in itertools.product(CELLS, SEEDS, ["random", "oracle_myopic"]):
        res = [episode(agent, n, k, 1000 * seed + i) for i in range(EPISODES)]
        tot, ln, cl, q, dt = map(np.array, zip(*res, strict=True))
        rows.append(
            {
                "label": "PILOT",
                "agent": agent,
                "N": n,
                "k": k,
                "seed": seed,
                "episodes": EPISODES,
                "mean_total_reward": float(tot.mean()),
                "std_total_reward": float(tot.std(ddof=1)),
                "mean_length": float(ln.mean()),
                "mean_clicks": float(cl.mean()),
                "mean_clicked_quality": float(np.nanmean(q)),
                "env_steps_per_sec": float(ln.sum() / dt.sum()),
                "_totals": tot.tolist(),
            }
        )
    # Paired (CRN) difference oracle - random per cell/seed.
    paired = []
    for (n, k), seed in itertools.product(CELLS, SEEDS):
        a = next(
            r
            for r in rows
            if (r["agent"], r["N"], r["k"], r["seed"]) == ("oracle_myopic", n, k, seed)
        )
        b = next(
            r for r in rows if (r["agent"], r["N"], r["k"], r["seed"]) == ("random", n, k, seed)
        )
        d = np.array(a["_totals"]) - np.array(b["_totals"])
        paired.append(
            {
                "label": "PILOT",
                "N": n,
                "k": k,
                "seed": seed,
                "mean_diff_oracle_minus_random": float(d.mean()),
                "se_diff": float(d.std(ddof=1) / math.sqrt(len(d))),
            }
        )
    for r in rows:
        r.pop("_totals")
    return rows, paired


class QNet(
    torch.nn.Module
):  # same shape as RecSim's recsim_dqn_network: [user,doc] -> 256 -> 32 -> 1
    def __init__(self, d=40):
        super().__init__()
        self.f = torch.nn.Sequential(
            torch.nn.Linear(d, 256),
            torch.nn.ReLU(),
            torch.nn.Linear(256, 32),
            torch.nn.ReLU(),
            torch.nn.Linear(32, 1),
        )

    def forward(self, x):
        return self.f(x).squeeze(-1)


def bench_torch(n, threads, iters=300, batch=32):
    torch.set_num_threads(threads)
    online, target = QNet(), QNet()
    opt = torch.optim.Adam(online.parameters(), lr=1e-3)
    x = torch.randn(batch, n, 40)
    xn = torch.randn(batch, n, 40)
    probs = torch.softmax(torch.randn(batch, n), -1)
    for _ in range(20):  # warm-up
        online(x)
    t0 = time.perf_counter()
    for _ in range(iters):  # one SlateQ-style update: target over next candidates + online loss
        with torch.no_grad():
            tgt = 1.0 + 0.99 * (probs * target(xn)).sum(-1)
        q = online(x)[:, 0]
        loss = ((q - tgt) ** 2).mean()
        opt.zero_grad()
        loss.backward()
        opt.step()
    upd = iters / (time.perf_counter() - t0)
    single = torch.randn(n, 40)
    t0 = time.perf_counter()
    with torch.no_grad():
        for _ in range(iters):
            online(single)
    act = iters / (time.perf_counter() - t0)
    return {
        "label": "BENCH",
        "N": n,
        "torch_threads": threads,
        "updates_per_sec_batch32": upd,
        "action_selections_per_sec": act,
    }


def main():
    rows, paired = pilot()
    bench = [bench_torch(n, t) for n in (5, 10, 20) for t in (1, 4)]
    fsq = [
        {
            "N": n,
            "k": k,
            "ordered_slates_N_perm_k": math.perm(n, k),
            "unordered_slates_N_choose_k": math.comb(n, k),
        }
        for n, k in CELLS + [(10, 2), (20, 3)]
    ]
    out = {
        "pilot": rows,
        "pilot_paired": paired,
        "torch_bench": bench,
        "fullslateq_action_counts": fsq,
        "torch_version": torch.__version__,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
