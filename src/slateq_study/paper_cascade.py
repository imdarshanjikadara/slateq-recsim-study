"""The exponential cascade user model described in the SlateQ paper (Ie et al. 2019, Section 6.3).

Used only by the Phase 6b experiment E4 (PROTOCOL 16). third_party/recsim is not modified: this is
our own subclass of RecSim's CascadeChoiceModel.

How a user picks from a slate of k items under this model:
  1. Base probability. Each item d gets the probability it would have under the ordinary
     ("conditional") choice model that SlateQ assumes: score(d) / (sum of slate scores + no-click
     score), where score = user . doc - min_normalizer. As in the paper, the no-click option is
     kept so that these probabilities stay comparable with the conditional model.
  2. Cascade. The user looks at the items from top to bottom. The item in position j
     (j = 0 for the top item) is inspected with probability BASE_INSPECTION * DECAY**j.
     If inspected, it is clicked with its base probability, and the user stops.
     Otherwise the user moves on to the next item. After the last item: no click.

So P(click item j) = [product over i < j of (1 - b_i * p_i)] * b_j * p_j,
with b_j = BASE_INSPECTION * DECAY**j and p_j the base probability.

The paper uses beta_0 = 1.0 and beta = 0.65 (Section 6.3). We read the position index j as starting
at 0, so the top item is always inspected (b_0 = 1.0). This reading is our choice and is recorded
in PROTOCOL 16.

Difference from RecSim's ProportionalCascadeChoiceModel (our RQ3 "severe" rung): RecSim inspects
every position with the same probability 0.65 and clicks with probability 0.05 * score, which makes
clicks rare. Here the click probability comes from the conditional model, so clicks stay common.

Interest Evolution also calls score_documents on a single clicked item to compute an
"expected utility", but multiplies it by user_quality_factor = 0, so it has no effect.
"""

from __future__ import annotations

from functools import cache

import numpy as np

BASE_INSPECTION = 1.0  # beta_0 in the paper
DECAY = 0.65  # beta in the paper


def cascade_click_probs(base_probs: np.ndarray) -> tuple[np.ndarray, float]:
    """Click probability of each slate position, and the no-click probability."""
    probs = np.zeros(len(base_probs))
    reach = 1.0  # probability that the user gets to position j without clicking
    for j, p in enumerate(base_probs):
        click_here = BASE_INSPECTION * DECAY**j * p
        probs[j] = reach * click_here
        reach *= 1.0 - click_here
    return probs, reach


@cache
def paper_cascade_cls():
    from recsim import choice_model as cm

    class PaperCascadeChoiceModel(cm.CascadeChoiceModel):
        def __init__(self, choice_features):
            super().__init__(choice_features)
            self._min_normalizer = choice_features.get("min_normalizer")
            self._no_click_mass = choice_features.get("no_click_mass", 0)

        def score_documents(self, user_state, doc_obs):
            raw = self._score_documents_helper(user_state, doc_obs)
            all_scores = np.append(raw, self._no_click_mass) - self._min_normalizer
            assert (all_scores >= 0.0).all(), "scores must be non-negative"
            base_probs = all_scores[:-1] / all_scores.sum()
            self._scores, self._score_no_click = cascade_click_probs(base_probs)

    return PaperCascadeChoiceModel
