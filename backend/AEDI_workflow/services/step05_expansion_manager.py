"""
Step 5: ExpansionManager
Expands candidates with SOC windows (RAG -> LLM), P variants, and cooling baselines.
UPDATED: skips P expansion when user specified exact config, handles stationary apps.
"""

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from ..config import llm
from ..defaults import get_fallback_for_cell
from ..models.requirements import ParsedRequirements
from ..models.candidates import ValidatedCandidate, ExpandedVariant


class SOCWindowOutput(BaseModel):
    """LLM output for SOC window recommendation."""
    soc_min: float = Field(description="Minimum SOC (0-1), e.g. 0.10 for 10%")
    soc_max: float = Field(description="Maximum SOC (0-1), e.g. 0.90 for 90%")
    rationale: str = Field(description="Why this SOC window was chosen")


_soc_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a battery engineer. Recommend the optimal SOC operating window "
     "(min and max SOC as fractions 0-1) for the given application and chemistry "
     "to maximize cycle life while maintaining usability."),
    ("human",
     "Application: {app_type}, Chemistry: {chemistry}, Cycle life target: {cycle_life} cycles"),
])
_soc_chain = _soc_prompt | llm.with_structured_output(SOCWindowOutput)

# Module-level cache: keyed by "{app_type}|{chemistry}" -> (soc_min, soc_max)
_soc_cache: dict[str, tuple[float, float]] = {}

# Application-specific SOC defaults (used when LLM fails)
SOC_DEFAULTS: dict[str, dict[str, tuple[float, float]]] = {
    "telecom-backup": {"LFP": (0.10, 1.00), "NMC": (0.10, 0.95)},  # telecom needs max usable capacity
    "solar-ess": {"LFP": (0.10, 0.95), "NMC": (0.15, 0.90)},
    "ups": {"LFP": (0.05, 1.00), "NMC": (0.10, 0.95)},  # UPS needs max available energy
}


def _get_soc_window(app_type: str, chemistry: str, cycle_life: int | None) -> tuple[float, float]:
    """Get recommended SOC window from LLM -- cached per (app_type, chemistry)."""
    cache_key = f"{app_type}|{chemistry}"
    if cache_key in _soc_cache:
        return _soc_cache[cache_key]

    try:
        result: SOCWindowOutput = _soc_chain.invoke({
            "app_type": app_type,
            "chemistry": chemistry,
            "cycle_life": cycle_life or 1000,
        })
        _soc_cache[cache_key] = (result.soc_min, result.soc_max)
    except Exception:
        # Application-specific defaults, then chemistry defaults
        app_key = app_type.lower().replace(" ", "-")
        app_defaults = SOC_DEFAULTS.get(app_key, {})
        if chemistry in app_defaults:
            _soc_cache[cache_key] = app_defaults[chemistry]
        elif "LFP" in chemistry:
            _soc_cache[cache_key] = (0.05, 0.95)
        else:
            _soc_cache[cache_key] = (0.10, 0.90)

    return _soc_cache[cache_key]


def _assign_cooling_baseline(candidate: ValidatedCandidate) -> str:
    """Assign cooling method based on power density and cell count."""
    r_ohm = candidate.cell.dcir_10s_ohms or get_fallback_for_cell("dcir_10s_ohms", candidate.cell)
    if candidate.continuous_current_a and r_ohm:
        i_per_cell = candidate.continuous_current_a / candidate.parallel_count
        heat_per_cell_w = i_per_cell ** 2 * r_ohm
        total_heat_w = heat_per_cell_w * candidate.total_cells

        if total_heat_w > 100:
            return "liquid"
        elif total_heat_w > 30:
            return "active-air"
    return "passive"


def expand_candidates(
    candidates: list[ValidatedCandidate],
    app_type: str,
    requirements: ParsedRequirements | None = None,
) -> list[ExpandedVariant]:
    """Expand each candidate into variants with SOC windows.

    If user specified exact P (target_parallel_count), only generate the base variant (no P+1, P+2).
    Otherwise, generate P, P+1, P+2 variants.

    LLM is called at most once per unique chemistry (cached), not once per candidate.

    Args:
        candidates: Validated candidates from Step 4
        app_type: Application type for SOC window lookup
        requirements: Original parsed requirements (optional, for checking user-specified P)

    Returns:
        List of ExpandedVariant
    """
    variants: list[ExpandedVariant] = []
    user_specified_p = requirements and requirements.target_parallel_count is not None

    for cand in candidates:
        chemistry = cand.cell.chemistry or "NMC"
        soc_min, soc_max = _get_soc_window(app_type, chemistry, cand.cell.cycles_to_80_soh)
        cooling = _assign_cooling_baseline(cand)

        # If user specified exact P, only generate base variant
        if user_specified_p:
            p_variants = [(0, "P")]
        else:
            p_variants = [(0, "P"), (1, "P+1"), (2, "P+2")]

        for delta, label in p_variants:
            p = cand.parallel_count + delta
            total = cand.series_count * p
            capacity = p * (cand.cell.capacity_ah_nom or 0)
            energy = cand.pack_voltage_v * capacity
            usable = energy * (soc_max - soc_min)
            cell_weight_kg = total * (cand.cell.mass_kg or get_fallback_for_cell("mass_kg", cand.cell))
            weight = cell_weight_kg * 1.30

            variants.append(ExpandedVariant(
                base_candidate=cand,
                variant_label=f"{cand.cell.cell_name}_{cand.series_count}S{p}{label}",
                parallel_count=p,
                total_cells=total,
                pack_capacity_ah=round(capacity, 2),
                pack_energy_wh=round(energy, 2),
                estimated_weight_kg=round(weight, 2),
                soc_window_min=soc_min,
                soc_window_max=soc_max,
                usable_energy_wh=round(usable, 2),
                cooling_baseline=cooling,
            ))

    return variants
