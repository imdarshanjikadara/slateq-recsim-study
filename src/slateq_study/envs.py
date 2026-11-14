"""Environment factory: RecSim Interest Evolution, built from RecSim's own classes.

`make_env` wires the same RecSim classes, in the same order, as
`recsim.environments.interest_evolution.create_environment`. The only difference is that the user's
TRUE choice model is a parameter (needed for RQ3). With the default choice model the trajectory is
identical to RecSim's factory; tests/test_envs.py checks this step by step.

Mapping to the proposal: "catalog size" = num_candidates (N, redrawn every step when
resample_documents=True; DEVIATIONS D5); "slate size" = slate_size (k).
OLD gym API (kept on purpose): reset() -> obs dict; step(slate) -> (obs, reward, done, info).
"""

from __future__ import annotations

from typing import Any

from slateq_study import recsim_compat
from slateq_study.config import CHOICE_MODELS, EnvConfig

DEFAULT_CHOICE_MODEL = "multinomial_proportional"  # RecSim's choice in create_environment


def _choice_model_class(name: str):
    recsim_compat.install()
    from recsim import choice_model

    if name == "proportional_cascade":  # RecSim's version fails under numpy 2 (choice_compat)
        from slateq_study.choice_compat import proportional_cascade_cls

        return proportional_cascade_cls()
    if name == "paper_cascade":  # SlateQ paper's cascade, our own class (Phase 6b E4)
        from slateq_study.paper_cascade import paper_cascade_cls

        return paper_cascade_cls()
    return getattr(choice_model, CHOICE_MODELS[name])


def make_env(env_cfg: EnvConfig, seed: int) -> Any:
    """Build one RecSim Interest Evolution env.

    `seed` seeds RecSim's user and document samplers. RecSim's choice model and interest updates
    also draw from the GLOBAL np.random, which the harness seeds per episode (seeding.seed_global).
    """
    env_cfg.validate()
    recsim_compat.install()
    from recsim import utils
    from recsim.environments import interest_evolution as ie
    from recsim.simulator import environment, recsim_gym

    user_model = ie.IEvUserModel(
        env_cfg.slate_size,
        choice_model_ctor=_choice_model_class(env_cfg.choice_model),
        response_model_ctor=ie.IEvResponse,
        user_state_ctor=ie.IEvUserState,
        no_click_mass=float(env_cfg.no_click_mass),
        seed=int(seed),
    )
    document_sampler = ie.UtilityModelVideoSampler(doc_ctor=ie.IEvVideo, seed=int(seed))
    ievenv = environment.Environment(
        user_model,
        document_sampler,
        env_cfg.num_candidates,
        env_cfg.slate_size,
        resample_documents=env_cfg.resample_documents,
    )
    return recsim_gym.RecSimGymEnv(
        ievenv,
        ie.clicked_watchtime_reward,
        utils.aggregate_video_cluster_metrics,
        utils.write_video_cluster_metrics,
    )


def user_model(env: Any) -> Any:
    """PRIVILEGED: RecSim's internal user model. Only the oracle baseline and trace logging
    (for figures) may use this; learned agents never see it."""
    return env._environment.user_model


def true_user_state(env: Any) -> Any:
    """PRIVILEGED: the current user's true state object (interests, time budget, ...)."""
    return user_model(env)._user_state
