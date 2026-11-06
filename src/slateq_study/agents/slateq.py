"""SlateQ (Ie et al. 2019) as a PyTorch port of RecSim's SlateDecompQAgent (DEVIATIONS D3).

Faithful to the reference (third_party/recsim/recsim/agents/slate_decomp_q_agent.py):
  * item-wise Q-network on [user, doc] -> 256 ReLU -> 32 ReLU -> 1 (dopamine recsim_dqn_network),
    Glorot-uniform weights / zero biases like Keras Dense defaults;
  * the agent's ASSUMED choice model is fixed here: multinomial proportional on dot(user, doc)
    with no_click_mass=1 and min_normalizer=-1, i.e. score = dot + 1, no-click score = 2
    (score_documents / compute_probs_tf). RQ3 changes only the environment's TRUE model;
  * slate selection: top-k by score * Q ("TS"), or greedy ("GS");
  * SARSA target: r + gamma * sum_{j in A'} P(j | s', A') Q_target(s', j) * (1 - terminal),
    using the slate A' actually served next and the NEXT state's candidates; the no-click option
    is in the denominator but carries no value (DEVIATIONS D6);
  * squared loss on CLICKED transitions only (_build_train_op);
  * dopamine DQN schedule: train every `update_period` steps once the replay holds more than
    `min_replay_history` transitions; sync the target net every `target_update_period` steps.
Exploration uses the agent's own numpy Generator, never the global np.random (PROTOCOL §4).
Learned-myopic = this agent with gamma = 0.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import torch
from torch import nn

from slateq_study.agents.base import Agent, Observation

log = logging.getLogger(__name__)

NO_CLICK_MASS = 1.0
MIN_NORMALIZER = -1.0


# ----------------------------------------------------------------------------- reference maths
def score_documents(user: torch.Tensor, docs: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Unnormalised proportional scores. user (..., D), docs (..., N, D) -> (..., N), (...)."""
    s = (docs * user.unsqueeze(-2)).sum(-1) - MIN_NORMALIZER
    s_no_click = torch.full(s.shape[:-1], NO_CLICK_MASS - MIN_NORMALIZER, dtype=s.dtype)
    return s, s_no_click


def select_slate_topk(k: int, s_no_click, s: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
    """Top-k by s * q (reference select_slate_topk; no-click score unused)."""
    del s_no_click
    return torch.topk(s * q, k).indices


def select_slate_greedy(k: int, s_no_click, s: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
    """Greedy: add the item with the largest marginal slate value (paper §5.2)."""
    chosen: list[int] = []
    num = torch.zeros((), dtype=s.dtype)
    den = torch.as_tensor(s_no_click, dtype=s.dtype)
    avail = torch.ones_like(s, dtype=torch.bool)
    for _ in range(k):
        value = (num + s * q) / (den + s)
        value = torch.where(avail, value, torch.full_like(value, -torch.inf))
        i = int(torch.argmax(value))
        chosen.append(i)
        avail[i] = False
        num = num + s[i] * q[i]
        den = den + s[i]
    return torch.tensor(chosen)


SELECTORS = {"topk": select_slate_topk, "greedy": select_slate_greedy}


def sarsa_target(
    reward: torch.Tensor,
    gamma: float,
    next_slate: torch.Tensor,  # (B, k) long
    next_q: torch.Tensor,  # (B, N) target-net Q of next candidates
    next_s: torch.Tensor,  # (B, N) scores of next candidates
    next_s_no_click: torch.Tensor,  # (B,)
    terminal: torch.Tensor,  # (B,) bool
) -> torch.Tensor:
    s_sel = torch.gather(next_s, 1, next_slate)
    q_sel = torch.gather(next_q, 1, next_slate)
    p = s_sel / (s_sel.sum(1, keepdim=True) + next_s_no_click.unsqueeze(1))
    expected = (p * q_sel).sum(1)
    return reward + gamma * expected * (1.0 - terminal.float())


def linearly_decaying_epsilon(decay_period: int, step: int, warmup: int, epsilon: float) -> float:
    """dopamine.agents.dqn.dqn_agent.linearly_decaying_epsilon."""
    steps_left = decay_period + warmup - step
    bonus = (1.0 - epsilon) * steps_left / decay_period
    return epsilon + float(np.clip(bonus, 0.0, 1.0 - epsilon))


# ----------------------------------------------------------------------------- network / replay
class ItemQNetwork(nn.Module):
    def __init__(self, user_dim: int, doc_dim: int, hidden=(256, 32)):
        super().__init__()
        layers, d = [], user_dim + doc_dim
        for h in hidden:
            layers += [nn.Linear(d, h), nn.ReLU()]
            d = h
        layers.append(nn.Linear(d, 1))
        self.net = nn.Sequential(*layers)
        for m in self.net:
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                nn.init.zeros_(m.bias)

    def forward(self, user: torch.Tensor, docs: torch.Tensor) -> torch.Tensor:
        """user (B, D_u), docs (B, N, D_d) -> Q (B, N)."""
        u = user.unsqueeze(1).expand(-1, docs.shape[1], -1)
        return self.net(torch.cat([u, docs], -1)).squeeze(-1)


class ReplayBuffer:
    """Circular buffer. Interest Evolution docs are one-hot clusters, so candidates are stored as
    cluster ids (int16) and re-expanded when sampled: ~200 bytes per transition, not ~3 KB."""

    def __init__(self, capacity: int, user_dim: int, n_docs: int, doc_dim: int, k: int):
        self.capacity, self.doc_dim, self.size, self.pos, self.add_count = (
            capacity,
            doc_dim,
            0,
            0,
            0,
        )
        self.user = np.zeros((capacity, user_dim), np.float32)
        self.next_user = np.zeros((capacity, user_dim), np.float32)
        self.docs = np.zeros((capacity, n_docs), np.int16)
        self.next_docs = np.zeros((capacity, n_docs), np.int16)
        self.slate = np.zeros((capacity, k), np.int64)
        self.next_slate = np.zeros((capacity, k), np.int64)
        self.click_pos = np.full(capacity, -1, np.int8)
        self.reward = np.zeros(capacity, np.float32)
        self.terminal = np.zeros(capacity, bool)

    @staticmethod
    def encode_docs(docs: np.ndarray) -> np.ndarray:
        if not (np.isin(docs, (0.0, 1.0)).all() and (docs.sum(1) == 1).all()):
            raise ValueError("compact replay assumes one-hot document features")
        return docs.argmax(1).astype(np.int16)

    def add(
        self,
        user,
        docs_ids,
        slate,
        click_pos,
        reward,
        next_user,
        next_docs_ids,
        next_slate,
        terminal,
    ) -> None:
        i = self.pos
        self.user[i], self.docs[i], self.slate[i] = user, docs_ids, slate
        self.click_pos[i], self.reward[i] = click_pos, reward
        self.next_user[i], self.next_docs[i], self.next_slate[i] = (
            next_user,
            next_docs_ids,
            next_slate,
        )
        self.terminal[i] = terminal
        self.pos = (i + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)
        self.add_count += 1

    def sample(self, rng: np.random.Generator, batch: int) -> dict[str, torch.Tensor]:
        idx = rng.integers(0, self.size, size=batch)
        eye = np.eye(self.doc_dim, dtype=np.float32)
        t = torch.from_numpy
        return {
            "user": t(self.user[idx]),
            "docs": t(eye[self.docs[idx]]),
            "slate": t(self.slate[idx]),
            "click_pos": t(self.click_pos[idx].astype(np.int64)),
            "reward": t(self.reward[idx]),
            "next_user": t(self.next_user[idx]),
            "next_docs": t(eye[self.next_docs[idx]]),
            "next_slate": t(self.next_slate[idx]),
            "terminal": t(self.terminal[idx]),
        }


# ----------------------------------------------------------------------------- agent
class SlateQAgent(Agent):
    name = "slateq"
    learns = True

    def __init__(
        self,
        action_space,
        seed: int,
        gamma: float = 0.99,
        learning_rate: float = 2.5e-4,
        optimizer: str = "rmsprop",
        batch_size: int = 32,
        update_period: int = 4,
        target_update_period: int = 8000,
        min_replay_history: int = 20_000,
        epsilon_train: float = 0.01,
        epsilon_decay_period: int = 100_000,
        epsilon_eval: float = 0.0,
        replay_capacity: int = 1_000_000,
        selection: str = "topk",
        hidden: tuple[int, ...] | list[int] = (256, 32),
    ):
        super().__init__(action_space, seed)
        if selection not in SELECTORS:
            raise ValueError(f"selection must be one of {sorted(SELECTORS)}")
        self.gamma, self.batch_size = float(gamma), int(batch_size)
        self.update_period, self.target_update_period = (
            int(update_period),
            int(target_update_period),
        )
        self.min_replay_history = int(min_replay_history)
        self.epsilon_train, self.epsilon_decay_period = (
            float(epsilon_train),
            int(epsilon_decay_period),
        )
        self.epsilon_eval = float(epsilon_eval)
        self.select = SELECTORS[selection]
        self.rng = np.random.default_rng(seed)
        self.user_dim = self.doc_dim = 20
        with torch.random.fork_rng(devices=[]):  # init depends on the agent seed only
            torch.manual_seed(seed)
            self.online = ItemQNetwork(self.user_dim, self.doc_dim, tuple(hidden))
            self.target = ItemQNetwork(self.user_dim, self.doc_dim, tuple(hidden))
        self.target.load_state_dict(self.online.state_dict())
        if optimizer == "rmsprop":  # dopamine DQN default (centered RMSProp)
            self.opt = torch.optim.RMSprop(
                self.online.parameters(),
                lr=learning_rate,
                alpha=0.95,
                eps=1e-5,
                momentum=0.0,
                centered=True,
            )
        elif optimizer == "adam":
            self.opt = torch.optim.Adam(self.online.parameters(), lr=learning_rate)
        else:
            raise ValueError("optimizer must be 'rmsprop' or 'adam'")
        self.replay = ReplayBuffer(
            int(replay_capacity), self.user_dim, self.num_candidates, self.doc_dim, self.slate_size
        )
        self.training_steps = 0
        self.updates = 0
        self.target_syncs = 0
        self._prev: dict[str, Any] | None = None
        self.diag: list[dict] = []
        self._acc = {"loss": [], "q_clicked": [], "target": [], "grad_norm": [], "clicked_frac": []}

    # ---------------------------------------------------------------- acting
    @staticmethod
    def _tensors(obs: Observation) -> tuple[torch.Tensor, torch.Tensor]:
        user = torch.as_tensor(np.asarray(obs["user"], np.float32))
        docs = torch.as_tensor(np.stack(list(obs["doc"].values())).astype(np.float32))
        return user, docs

    @property
    def epsilon(self) -> float:
        if self.eval_mode:
            return self.epsilon_eval
        return linearly_decaying_epsilon(
            self.epsilon_decay_period,
            self.training_steps,
            self.min_replay_history,
            self.epsilon_train,
        )

    def _greedy_slate(self, user: torch.Tensor, docs: torch.Tensor) -> np.ndarray:
        with torch.no_grad():
            q = self.online(user.unsqueeze(0), docs.unsqueeze(0))[0]
            s, s0 = score_documents(user, docs)
            return self.select(self.slate_size, s0, s, q).numpy().astype(np.int64)

    def _act(self, obs: Observation) -> np.ndarray:
        if self.rng.random() <= self.epsilon:  # same comparison as the reference (<=)
            return self.rng.choice(self.num_candidates, self.slate_size, replace=False)
        return self._greedy_slate(*self._tensors(obs))

    def begin_episode(self, observation: Observation) -> np.ndarray:
        slate = self._act(observation)
        self._remember(observation, slate)
        return slate

    def step(self, reward: float, observation: Observation) -> np.ndarray:
        if not self.eval_mode:
            self.training_steps += 1
        slate = self._act(observation)
        self._store(observation, slate, terminal=False)
        self._remember(observation, slate)
        if not self.eval_mode:
            self._maybe_train()
        return slate

    def end_episode(self, reward: float, observation: Observation, truncated: bool = False) -> None:
        if not self.eval_mode:
            self.training_steps += 1
            if truncated:  # not a real terminal: bootstrap through the slate we would serve next
                self._store(observation, self._greedy_slate(*self._tensors(observation)), False)
            else:
                self._store(observation, np.zeros(self.slate_size, np.int64), terminal=True)
            self._maybe_train()
        self._prev = None

    def _remember(self, obs: Observation, slate: np.ndarray) -> None:
        if self.eval_mode:
            return
        docs = np.stack(list(obs["doc"].values()))
        self._prev = {
            "user": np.asarray(obs["user"], np.float32),
            "docs": ReplayBuffer.encode_docs(docs),
            "slate": np.asarray(slate),
        }

    def _store(self, obs: Observation, next_slate: np.ndarray, terminal: bool) -> None:
        if self.eval_mode or self._prev is None:
            return
        resp = obs["response"]
        click_pos = next((i for i, r in enumerate(resp) if r["click"]), -1)
        reward = float(resp[click_pos]["watch_time"]) if click_pos >= 0 else 0.0
        docs = np.stack(list(obs["doc"].values()))
        self.replay.add(
            self._prev["user"],
            self._prev["docs"],
            self._prev["slate"],
            click_pos,
            reward,
            np.asarray(obs["user"], np.float32),
            ReplayBuffer.encode_docs(docs),
            next_slate,
            terminal,
        )

    # ---------------------------------------------------------------- learning
    def _maybe_train(self) -> None:
        if self.replay.add_count <= self.min_replay_history:
            return
        if self.training_steps % self.update_period == 0:
            self._train_step()
        if self.training_steps % self.target_update_period == 0:
            self.target.load_state_dict(self.online.state_dict())
            self.target_syncs += 1

    def _train_step(self) -> None:
        b = self.replay.sample(self.rng, self.batch_size)
        clicked = b["click_pos"] >= 0
        self._acc["clicked_frac"].append(float(clicked.float().mean()))
        if not bool(clicked.any()):
            return
        with torch.no_grad():
            next_q = self.target(b["next_user"], b["next_docs"])
            next_s, next_s0 = score_documents(b["next_user"], b["next_docs"])
            target = sarsa_target(
                b["reward"], self.gamma, b["next_slate"], next_q, next_s, next_s0, b["terminal"]
            )
        q_all = self.online(b["user"], b["docs"])
        pos = b["click_pos"].clamp(min=0)
        item = torch.gather(b["slate"], 1, pos.unsqueeze(1)).squeeze(1)
        q_clicked = torch.gather(q_all, 1, item.unsqueeze(1)).squeeze(1)
        loss = ((q_clicked - target) ** 2)[clicked].mean()
        self.opt.zero_grad()
        loss.backward()
        gn = torch.sqrt(sum((p.grad.detach() ** 2).sum() for p in self.online.parameters()))
        self.opt.step()
        self.updates += 1
        a = self._acc
        a["loss"].append(float(loss.detach()))
        a["q_clicked"].append(float(q_clicked.detach()[clicked].mean()))
        a["target"].append(float(target[clicked].mean()))
        a["grad_norm"].append(float(gn))
        if self.updates % 1000 == 0:
            self.flush_diagnostics()

    def flush_diagnostics(self) -> None:
        a = self._acc
        if not a["loss"]:
            return
        row = {
            "training_steps": self.training_steps,
            "updates": self.updates,
            "epsilon": self.epsilon if not self.eval_mode else self.epsilon_eval,
            "replay_size": self.replay.size,
            "target_syncs": self.target_syncs,
            **{f"mean_{k}": float(np.mean(v)) for k, v in a.items() if v},
            "max_abs_q_clicked": float(np.max(np.abs(a["q_clicked"]))),
        }
        bad = [k for k, v in row.items() if isinstance(v, float) and not np.isfinite(v)]
        self.diag.append(row)
        self._acc = {k: [] for k in a}
        if bad:
            raise FloatingPointError(f"non-finite training diagnostics: {bad}")

    def state_dict(self) -> dict:
        return {
            "online": self.online.state_dict(),
            "target": self.target.state_dict(),
            "opt": self.opt.state_dict(),
            "training_steps": self.training_steps,
            "updates": self.updates,
            "gamma": self.gamma,
        }


class LearnedMyopicAgent(SlateQAgent):
    """Learned-myopic ablation: SlateQ with gamma = 0 (RecSim's myopic_slate_topk_sarsa).
    Same network, optimiser and schedule; only the horizon differs."""

    name = "learned_myopic"

    def __init__(self, action_space, seed: int, **kw):
        if kw.get("gamma", 0.0) != 0.0:
            raise ValueError("learned_myopic has gamma fixed at 0")
        kw["gamma"] = 0.0
        super().__init__(action_space, seed, **kw)
