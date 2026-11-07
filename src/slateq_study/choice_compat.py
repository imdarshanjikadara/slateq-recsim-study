"""numpy-2 compatibility for one RecSim choice model (third_party/recsim stays unmodified).

RecSim's ProportionalCascadeChoiceModel.score_documents checks
    assert not scores[scores < 0.0]
Under numpy 1 an empty array was falsy (with a deprecation warning); under numpy 2 the truth value
of an empty array raises ValueError, so every call fails. The subclass below performs the SAME
check written for numpy 2 (`not (scores < 0.0).any()`) and is otherwise identical (same class name,
same attributes, RecSim's own _positional_normalization). Used only for RQ3's cascade condition.
"""

from __future__ import annotations

from functools import cache


@cache
def proportional_cascade_cls():
    from recsim import choice_model as cm

    class ProportionalCascadeChoiceModel(cm.ProportionalCascadeChoiceModel):
        def score_documents(self, user_state, doc_obs):
            scores = self._score_documents_helper(user_state, doc_obs)
            scores = scores - self._min_normalizer
            assert not (scores < 0.0).any(), "Normalized scores have non-positive elements."
            self._positional_normalization(scores)

    return ProportionalCascadeChoiceModel
