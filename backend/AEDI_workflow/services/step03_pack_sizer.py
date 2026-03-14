"""
Step 3: PackSizer
Pure deterministic math — NO LLM calls. Computes S/P configurations from cells DB.
UPDATED: supports telecom/ESS applications, explicit S/P configs, capacity-based P,
discharge current targets, and cell sanity filtering.
"""

import math
from ..config import supabase
from ..defaults import get_fallback_for_cell
from ..models.requirements import ParsedRequirements
from ..models.rules import DesignRules
from ..models.candidates import CellCandidate, PackCandidate

# Chemistry -> application suitability mapping
CHEMISTRY_APP_MAP: dict[str, list[str]] = {
    # EV / mobility
    "e-bike": ["NMC", "NCA", "LFP"],
    "e-scooter": ["NMC", "NCA", "LFP"],
    "e-motorcycle": ["NMC", "NCA"],
    "e-rickshaw": ["LFP", "NMC"],
    "e-auto": ["LFP", "NMC"],
    "delivery": ["LFP", "NMC"],
    # Stationary / industrial
    "telecom-backup": ["LFP"],
    "solar-ess": ["LFP"],
    "ups": ["LFP", "NMC"],
    "data-center-ups": ["LFP"],
    "industrial-ess": ["LFP"],
    "marine": ["LFP", "NMC"],
}

# Overhead factor for BMS, wiring, enclosure by application category
WEIGHT_OVERHEAD: dict[str, float] = {
    "telecom-backup": 0.20,  # rack-mount packs have lighter overhead ratio
    "solar-ess": 0.20,
    "ups": 0.20,
    "data-center-ups": 0.20,
    "industrial-ess": 0.25,
    "marine": 0.25,
}
DEFAULT_WEIGHT_OVERHEAD = 0.30  # EV / mobility default

# Cell sanity limits — reject cells with absurd values
MAX_CELL_CAPACITY_AH = 400   # Largest real prismatic cells are ~300Ah (CATL 314Ah)
MAX_CELL_VOLTAGE_V = 4.5     # No li-ion cell exceeds ~4.4V
MIN_CELL_VOLTAGE_V = 1.5     # LTO is ~2.3V, nothing lower in li-ion
MAX_CELL_WEIGHT_KG = 10.0    # Largest prismatic cells ~5-6kg


def _fetch_cells(chemistries: list[str]) -> list[CellCandidate]:
    """Query Supabase cells table filtered by chemistry.

    Uses ilike for flexible matching (e.g. 'NMC' matches 'NMC811', 'NMC622').
    """
    try:
        # First try exact match
        result = supabase.table("cells").select("*").in_("chemistry", chemistries).execute()
        cells = [CellCandidate(**row) for row in (result.data or [])]

        # If no exact matches, try partial match via chemistry_family or broader chemistry
        if not cells:
            for chem in chemistries:
                result = supabase.table("cells").select("*").ilike(
                    "chemistry", f"%{chem}%"
                ).execute()
                cells.extend([CellCandidate(**row) for row in (result.data or [])])

        # Deduplicate by id
        seen = set()
        unique = []
        for c in cells:
            if c.id not in seen:
                seen.add(c.id)
                unique.append(c)
        return unique
    except Exception:
        return []


def _sanity_check_cell(cell: CellCandidate) -> bool:
    """Reject cells with absurd or clearly erroneous database values."""
    if not cell.voltage_nom_v or not cell.capacity_ah_nom:
        return False
    if cell.capacity_ah_nom <= 0 or cell.capacity_ah_nom > MAX_CELL_CAPACITY_AH:
        return False
    if cell.voltage_nom_v < MIN_CELL_VOLTAGE_V or cell.voltage_nom_v > MAX_CELL_VOLTAGE_V:
        return False
    if cell.mass_kg and cell.mass_kg > MAX_CELL_WEIGHT_KG:
        return False
    # Cross-check: energy density should be reasonable (50-400 Wh/kg)
    if cell.mass_kg and cell.mass_kg > 0:
        energy_wh = cell.voltage_nom_v * cell.capacity_ah_nom
        wh_per_kg = energy_wh / cell.mass_kg
        if wh_per_kg > 400 or wh_per_kg < 30:
            return False
    return True


def _compute_series(target_voltage: float, cell_voltage: float) -> int:
    """Compute series count S = round(target_voltage / cell_nominal_voltage)."""
    return round(target_voltage / cell_voltage)


def _compute_parallel_from_capacity(target_capacity_ah: float, cell_capacity_ah: float) -> int:
    """Compute parallel count P = ceil(target_capacity / cell_capacity)."""
    return math.ceil(target_capacity_ah / cell_capacity_ah)


def _compute_parallel_from_energy(target_energy_wh: float, pack_voltage: float, cell_capacity_ah: float) -> int:
    """Compute parallel count P = ceil(required_Ah / cell_Ah)."""
    required_ah = target_energy_wh / pack_voltage
    return math.ceil(required_ah / cell_capacity_ah)


def _compute_parallel_from_current(target_current_a: float, cell_discharge_cont_a: float) -> int:
    """Compute parallel count P = ceil(target_current / cell_max_discharge_current)."""
    if cell_discharge_cont_a and cell_discharge_cont_a > 0:
        return math.ceil(target_current_a / cell_discharge_cont_a)
    return 1


def _build_candidate(
    cell: CellCandidate,
    series: int,
    parallel: int,
    requirements: ParsedRequirements,
) -> PackCandidate:
    """Build a PackCandidate from cell + S/P configuration."""
    cell_v = cell.voltage_nom_v or 3.6
    cell_ah = cell.capacity_ah_nom or 0

    total_cells = series * parallel
    pack_voltage = series * cell_v
    pack_capacity = parallel * cell_ah
    pack_energy = pack_voltage * pack_capacity
    cell_weight_kg = total_cells * (cell.mass_kg or get_fallback_for_cell("mass_kg", cell))
    app_key = requirements.application_type.lower().replace(" ", "-")
    overhead = WEIGHT_OVERHEAD.get(app_key, DEFAULT_WEIGHT_OVERHEAD)
    estimated_weight = cell_weight_kg * (1 + overhead)

    # Current calculations — use explicit discharge current if available
    continuous_current = None
    peak_current = None
    continuous_c_rate = None
    peak_c_rate = None

    if requirements.target_discharge_current_a and cell_ah > 0:
        continuous_current = requirements.target_discharge_current_a
        per_cell_cont = continuous_current / parallel
        continuous_c_rate = per_cell_cont / cell_ah
    elif requirements.nominal_power_w and cell_ah > 0:
        continuous_current = requirements.nominal_power_w / pack_voltage
        per_cell_cont = continuous_current / parallel
        continuous_c_rate = per_cell_cont / cell_ah

    if requirements.target_peak_current_a and cell_ah > 0:
        peak_current = requirements.target_peak_current_a
        per_cell_peak = peak_current / parallel
        peak_c_rate = per_cell_peak / cell_ah
    elif requirements.peak_power_w and cell_ah > 0:
        peak_current = requirements.peak_power_w / pack_voltage
        per_cell_peak = peak_current / parallel
        peak_c_rate = per_cell_peak / cell_ah

    return PackCandidate(
        cell=cell,
        series_count=series,
        parallel_count=parallel,
        total_cells=total_cells,
        pack_voltage_v=round(pack_voltage, 2),
        pack_capacity_ah=round(pack_capacity, 2),
        pack_energy_wh=round(pack_energy, 2),
        estimated_weight_kg=round(estimated_weight, 2),
        continuous_current_a=round(continuous_current, 2) if continuous_current else None,
        peak_current_a=round(peak_current, 2) if peak_current else None,
        continuous_c_rate=round(continuous_c_rate, 3) if continuous_c_rate else None,
        peak_c_rate=round(peak_c_rate, 3) if peak_c_rate else None,
    )


def compute_candidates(
    requirements: ParsedRequirements,
    rules: DesignRules,
) -> list[PackCandidate]:
    """Compute all S/P candidates from matching cells.

    Priority logic for S/P computation:
    1. If user specified both target_series_count AND target_parallel_count, use exact config
    2. If user specified target_series_count only, compute P from capacity/energy/current
    3. If user specified target_capacity_ah, compute P from capacity (not energy)
    4. If user specified target_discharge_current_a, ensure P meets current requirement
    5. Fallback: compute S from voltage, P from energy (original behavior)

    Args:
        requirements: Parsed requirements from Step 1
        rules: Design rules from Step 2

    Returns:
        List of PackCandidate with computed configurations
    """
    # Determine chemistries to consider
    app_key = requirements.application_type.lower().replace(" ", "-")
    chemistries = CHEMISTRY_APP_MAP.get(app_key, ["NMC", "LFP", "NCA"])
    if requirements.preferred_chemistry:
        chemistries = [requirements.preferred_chemistry] + [
            c for c in chemistries if c != requirements.preferred_chemistry
        ]

    # Fetch cells from Supabase
    cells = _fetch_cells(chemistries)
    if not cells:
        return []

    # Filter by form factor preference if specified
    if requirements.preferred_form_factor:
        preferred = [c for c in cells if c.format and
                     requirements.preferred_form_factor.lower() in c.format.lower()]
        if preferred:
            cells = preferred

    # Sanity filter — remove cells with absurd or erroneous data
    cells = [c for c in cells if _sanity_check_cell(c)]

    if not cells:
        return []

    candidates: list[PackCandidate] = []

    for cell in cells:
        cell_v = cell.voltage_nom_v
        cell_ah = cell.capacity_ah_nom

        # --- Determine S ---
        if requirements.target_series_count:
            s = requirements.target_series_count
        else:
            s = _compute_series(requirements.target_voltage_v, cell_v)

        if s < 1:
            continue

        # --- Determine P ---
        if requirements.target_parallel_count:
            # User explicitly specified P
            p = requirements.target_parallel_count
        elif requirements.target_capacity_ah:
            # Compute P from target capacity (preferred over energy)
            p = _compute_parallel_from_capacity(requirements.target_capacity_ah, cell_ah)
        else:
            # Fallback: compute P from target energy
            pack_voltage = s * cell_v
            p = _compute_parallel_from_energy(requirements.target_energy_wh, pack_voltage, cell_ah)

        if p < 1:
            continue

        # If discharge current target is set, ensure P is high enough
        if requirements.target_discharge_current_a and cell.discharge_amps_cont:
            p_for_current = _compute_parallel_from_current(
                requirements.target_discharge_current_a, cell.discharge_amps_cont
            )
            p = max(p, p_for_current)

        candidate = _build_candidate(cell, s, p, requirements)
        candidates.append(candidate)

    return candidates
