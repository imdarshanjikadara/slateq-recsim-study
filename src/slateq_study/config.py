"""Typed run configuration: dataclasses, YAML loading, validation and a canonical hash.

The seed is NOT part of the config: one config is run under several seeds, and all of them share
the same config_hash (results/raw/<experiment>/<config_hash>/seed<k>/).
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised for any invalid configuration."""


# Config name -> RecSim class in recsim/choice_model.py (the user's TRUE choice model).
# RecSim's CascadeChoiceModel is abstract (no score_documents); only its two subclasses are usable.
CHOICE_MODELS = {
    "multinomial_proportional": "MultinomialProportionalChoiceModel",  # RecSim default
    "multinomial_logit": "MultinomialLogitChoiceModel",
    "exponential_cascade": "ExponentialCascadeChoiceModel",
    "proportional_cascade": "ProportionalCascadeChoiceModel",
}


@dataclass(frozen=True)
class EnvConfig:
    """RecSim Interest Evolution settings.

    num_candidates: N, the "catalog size" of the proposal (candidates per step; DEVIATIONS D5).
    slate_size: k, items shown per step.
    max_steps: safeguard against unbounded episodes (RecSim itself only stops on time budget).
    choice_model: the user's TRUE choice model (varied only in RQ3 / Phase 5).
    no_click_mass: the user's TRUE no-click mass (RecSim IEvUserModel argument; default 1.0 is
        RecSim's and what SlateQ assumes; varied only in RQ3).
    """

    num_candidates: int = 10
    slate_size: int = 3
    resample_documents: bool = True
    max_steps: int = 1000
    choice_model: str = "multinomial_proportional"
    no_click_mass: float = 1.0

    def validate(self) -> None:
        if not isinstance(self.no_click_mass, int | float) or not 0 <= self.no_click_mass < 1e6:
            raise ConfigError(f"no_click_mass must be a number >= 0, got {self.no_click_mass!r}")
        if self.choice_model not in CHOICE_MODELS:
            raise ConfigError(
                f"unknown choice_model {self.choice_model!r}; known: {sorted(CHOICE_MODELS)}"
            )
        if not isinstance(self.num_candidates, int) or self.num_candidates < 2:
            raise ConfigError(f"num_candidates must be an int >= 2, got {self.num_candidates!r}")
        if not isinstance(self.slate_size, int) or self.slate_size < 1:
            raise ConfigError(f"slate_size must be an int >= 1, got {self.slate_size!r}")
        if self.slate_size > self.num_candidates:
            raise ConfigError(
                f"slate_size ({self.slate_size}) > num_candidates ({self.num_candidates})"
            )
        if not isinstance(self.max_steps, int) or self.max_steps < 1:
            raise ConfigError(f"max_steps must be an int >= 1, got {self.max_steps!r}")

    @property
    def degenerate(self) -> bool:
        """k == N: no selection problem. Allowed, but flagged in metadata."""
        return self.slate_size == self.num_candidates


@dataclass(frozen=True)
class AgentConfig:
    name: str = "random"
    params: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        from slateq_study.agents import AGENTS

        if self.name not in AGENTS:
            raise ConfigError(f"unknown agent {self.name!r}; known: {sorted(AGENTS)}")
        if not isinstance(self.params, dict):
            raise ConfigError("agent.params must be a mapping")


@dataclass(frozen=True)
class RunConfig:
    experiment: str
    env: EnvConfig = field(default_factory=EnvConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    train_steps: int = 0
    eval_episodes: int = 10
    trace_episodes: int = 0  # per-step traces for the FIRST n eval episodes (PROTOCOL S5)
    eval_every: int = 0  # learning-curve point every n training steps (0 = no curve)
    curve_episodes: int = 200  # episodes per curve point (tune stream)
    eval_stream: str = "eval"  # final evaluation stream: "eval" (results) or "tune" (tuning)

    def validate(self) -> None:
        if not re.fullmatch(r"[A-Za-z0-9_\-]+", self.experiment or ""):
            raise ConfigError(f"experiment must match [A-Za-z0-9_-]+, got {self.experiment!r}")
        self.env.validate()
        self.agent.validate()
        if self.eval_stream not in ("eval", "tune"):
            raise ConfigError(f"eval_stream must be 'eval' or 'tune', got {self.eval_stream!r}")
        for name in ("eval_every", "curve_episodes"):
            v = getattr(self, name)
            if not isinstance(v, int) or v < 0:
                raise ConfigError(f"{name} must be an int >= 0, got {v!r}")
        from slateq_study.agents import AGENTS

        learns = AGENTS[self.agent.name].learns
        if learns and self.train_steps == 0:
            raise ConfigError(f"agent {self.agent.name!r} learns: train_steps must be > 0")
        if not learns and (self.train_steps or self.eval_every):
            raise ConfigError(f"agent {self.agent.name!r} does not learn: no training settings")
        if not isinstance(self.trace_episodes, int) or self.trace_episodes < 0:
            raise ConfigError(f"trace_episodes must be an int >= 0, got {self.trace_episodes!r}")
        if not isinstance(self.train_steps, int) or self.train_steps < 0:
            raise ConfigError(f"train_steps must be an int >= 0, got {self.train_steps!r}")
        if not isinstance(self.eval_episodes, int) or self.eval_episodes < 1:
            raise ConfigError(f"eval_episodes must be an int >= 1, got {self.eval_episodes!r}")

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    def canonical_json(self) -> str:
        """Fields added after Phase 2 are omitted while at their defaults, so earlier run
        directories (smoke, baselines) keep their config_hash."""
        d = self.to_dict()
        for name, default in _HASH_OPTIONAL.items():
            if d.get(name) == default:
                d.pop(name)
        for name, default in _ENV_HASH_OPTIONAL.items():
            if d["env"].get(name) == default:
                d["env"].pop(name)
        return json.dumps(d, sort_keys=True, separators=(",", ":"))

    @property
    def config_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode()).hexdigest()[:12]


_HASH_OPTIONAL = {"eval_every": 0, "curve_episodes": 200, "eval_stream": "eval"}
_ENV_HASH_OPTIONAL = {"no_click_mass": 1.0}  # added in Phase 5


def _build(cls, data: Any, where: str):
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ConfigError(f"{where} must be a mapping, got {type(data).__name__}")
    known = {f.name for f in dataclasses.fields(cls)}
    unknown = set(data) - known
    if unknown:
        raise ConfigError(f"unknown keys in {where}: {sorted(unknown)}")
    return cls(**data)


def from_dict(data: dict[str, Any]) -> RunConfig:
    if not isinstance(data, dict):
        raise ConfigError("config root must be a mapping")
    data = dict(data)
    env = _build(EnvConfig, data.pop("env", None), "env")
    agent = _build(AgentConfig, data.pop("agent", None), "agent")
    cfg = _build(RunConfig, {**data, "env": env, "agent": agent}, "config")
    cfg.validate()
    return cfg


def load_config(path: str | Path) -> RunConfig:
    with Path(path).open(encoding="utf-8") as f:
        return from_dict(yaml.safe_load(f))
