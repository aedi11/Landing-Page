"""
Step 10: Final CandidateRanker
Re-scores candidates using thermal simulation data from Step 9.
Pure deterministic — NO LLM calls.
"""

from ..models.output import RankedCandidate
from ..models.thermal import ThermalResult

# Updated weights with thermal simulation data available
WEIGHTS = {
    "energy_density": 0.20,
    "weight": 0.15,
    "cost": 0.20,
    "cycle_life": 0.10,
    "c_rate_margin": 0.10,
    "thermal": 0.25,  # Higher weight now that we have simulation data
}


def _rescore_thermal(candidate: RankedCandidate, thermal: ThermalResult) -> float:
    """Compute thermal score from simulation results (0-1)."""
    if not thermal.feasible:
        return 0.0

    # Score based on thermal margin (higher margin = better)
    # 20°C margin = 1.0, 0°C margin = 0.0
    margin_score = min(thermal.thermal_margin_c / 20.0, 1.0)

    # Bonus for simpler cooling
    cooling_bonus = {"passive": 0.15, "active-air": 0.05, "liquid": 0.0}.get(
        thermal.cooling_strategy.method, 0.0
    )

    return min(round(margin_score + cooling_bonus, 3), 1.0)


def rank_final(
    candidates: list[RankedCandidate],
    thermal_results: list[ThermalResult],
) -> list[RankedCandidate]:
    """Re-rank candidates using thermal simulation data.

    Args:
        candidates: Preliminary ranked candidates from Step 7
        thermal_results: Thermal simulation results from Step 9

    Returns:
        Re-ranked list of candidates
    """
    # Map thermal results to candidates by variant label
    thermal_map = {t.variant_label: t for t in thermal_results}

    for cand in candidates:
        thermal = thermal_map.get(cand.variant.variant_label)
        if thermal:
            cand.thermal_result = thermal
            cand.score_thermal = _rescore_thermal(cand, thermal)

        # Recalculate total score with updated weights
        cand.total_score = round(
            cand.score_energy_density * WEIGHTS["energy_density"]
            + cand.score_weight * WEIGHTS["weight"]
            + cand.score_cost * WEIGHTS["cost"]
            + cand.score_cycle_life * WEIGHTS["cycle_life"]
            + cand.score_c_rate_margin * WEIGHTS["c_rate_margin"]
            + cand.score_thermal * WEIGHTS["thermal"],
            4,
        )

    # Re-sort and re-rank
    candidates.sort(key=lambda c: c.total_score, reverse=True)
    for i, cand in enumerate(candidates, start=1):
        cand.rank = i

    return candidates
