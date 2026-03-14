"""
Step 7: Preliminary CandidateRanker
Pure deterministic scoring — NO LLM calls. Selects Top 4 candidates.
UPDATED: application-specific scoring weights (cycle life matters more for stationary).
"""

from ..models.candidates import ExpandedVariant
from ..models.output import RankedCandidate

# Default scoring weights for EV/mobility (sum = 1.0)
WEIGHTS_EV = {
    "energy_density": 0.25,
    "weight": 0.20,
    "cost": 0.20,
    "cycle_life": 0.15,
    "c_rate_margin": 0.10,
    "thermal": 0.10,
}

# Scoring weights for stationary/telecom applications (sum = 1.0)
WEIGHTS_STATIONARY = {
    "energy_density": 0.10,
    "weight": 0.05,        # weight matters much less for rack-mount
    "cost": 0.20,
    "cycle_life": 0.30,    # cycle life is critical for telecom/ESS (10+ year life)
    "c_rate_margin": 0.15,  # current capability matters for backup power
    "thermal": 0.20,
}

STATIONARY_APPS = {"telecom-backup", "solar-ess", "ups", "data-center-ups", "industrial-ess", "marine"}

# Approximate cost per Wh by chemistry (USD)
COST_PER_WH: dict[str, float] = {
    "NMC811": 0.13,
    "NMC622": 0.12,
    "NMC532": 0.11,
    "NMC": 0.12,
    "NCA": 0.14,
    "LFP": 0.07,
    "LTO": 0.20,
}


def _normalize(value: float, min_val: float, max_val: float, invert: bool = False) -> float:
    """Normalize value to 0-1 range. Invert for 'lower is better' metrics."""
    if max_val == min_val:
        return 0.5
    norm = (value - min_val) / (max_val - min_val)
    return 1.0 - norm if invert else norm


def _get_weights(app_type: str) -> dict[str, float]:
    """Get scoring weights based on application type."""
    app_key = app_type.lower().replace(" ", "-")
    return WEIGHTS_STATIONARY if app_key in STATIONARY_APPS else WEIGHTS_EV


def _score_candidate(variant: ExpandedVariant, all_variants: list[ExpandedVariant]) -> dict[str, float]:
    """Compute individual scores for a variant."""
    cell = variant.base_candidate.cell

    # Gather min/max across all candidates for normalization
    energies = [v.pack_energy_wh / (v.estimated_weight_kg or 1) for v in all_variants]
    weights = [v.estimated_weight_kg for v in all_variants]
    costs = [v.pack_energy_wh * COST_PER_WH.get(v.base_candidate.cell.chemistry, 0.12) for v in all_variants]
    cycles = [v.base_candidate.cell.cycles_to_80_soh or 500 for v in all_variants]

    energy_density = variant.pack_energy_wh / (variant.estimated_weight_kg or 1)
    est_cost = variant.pack_energy_wh * COST_PER_WH.get(cell.chemistry, 0.12)
    cycle_life = cell.cycles_to_80_soh or 500

    # C-rate margin: how much below the limit
    c_rate_margin = 0.5
    if variant.base_candidate.continuous_c_rate:
        c_rate_margin = max(0, 1.5 - variant.base_candidate.continuous_c_rate) / 1.5

    # Thermal: passive=1.0, active-air=0.7, liquid=0.4 (simpler is better)
    thermal_score = {"passive": 1.0, "active-air": 0.7, "liquid": 0.4}.get(
        variant.cooling_baseline, 0.5
    )

    return {
        "score_energy_density": round(_normalize(energy_density, min(energies), max(energies)), 3),
        "score_weight": round(_normalize(variant.estimated_weight_kg, min(weights), max(weights), invert=True), 3),
        "score_cost": round(_normalize(est_cost, min(costs), max(costs), invert=True), 3),
        "score_cycle_life": round(_normalize(cycle_life, min(cycles), max(cycles)), 3),
        "score_c_rate_margin": round(c_rate_margin, 3),
        "score_thermal": round(thermal_score, 3),
    }


def rank_preliminary(
    variants: list[ExpandedVariant],
    top_n: int = 4,
    app_type: str = "e-scooter",
) -> list[RankedCandidate]:
    """Score and rank candidates, return top N.

    Args:
        variants: Feasible variants from Step 6
        top_n: Number of top candidates to return
        app_type: Application type for weight selection

    Returns:
        Top N RankedCandidate sorted by total score
    """
    if not variants:
        return []

    weights = _get_weights(app_type)
    scored: list[tuple[float, ExpandedVariant, dict]] = []

    for variant in variants:
        scores = _score_candidate(variant, variants)
        total = sum(
            scores[f"score_{k}"] * weights[k]
            for k in weights
        )
        scores["total_score"] = round(total, 4)
        scored.append((total, variant, scores))

    # Sort descending by total score
    scored.sort(key=lambda x: x[0], reverse=True)

    results: list[RankedCandidate] = []
    for rank, (total, variant, scores) in enumerate(scored[:top_n], start=1):
        results.append(RankedCandidate(
            rank=rank,
            variant=variant,
            **scores,
        ))

    return results
