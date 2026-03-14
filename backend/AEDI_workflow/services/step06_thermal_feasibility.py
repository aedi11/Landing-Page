"""
Step 6: ThermalFeasibilityFilter
Pure physics — NO LLM calls. Volume fit, heat generation, cooling surface assessment.
Includes ThermalCoolingOptimizer to downgrade cooling if margin allows.
"""

import math
from ..defaults import get_fallback_for_cell
from ..models.candidates import ExpandedVariant
from ..models.requirements import ParsedRequirements

# Thermal cutoff temperature (°C)
T_CUTOFF = 60.0
T_AMBIENT = 40.0  # Worst-case ambient for Indian climate

# Cooling capacity estimates (W/m² per method)
COOLING_CAPACITY: dict[str, float] = {
    "passive": 50.0,        # W/m² — natural convection + thermal pads
    "active-air": 200.0,    # W/m² — forced air with heatsink
    "liquid": 1000.0,       # W/m² — liquid cooling plate
}

# Cell surface area estimates (m²) by format
CELL_SURFACE_AREA_M2: dict[str, float] = {
    "18650": 0.0038,    # pi x 18.6mm x 65mm
    "21700": 0.0046,    # pi x 21mm x 70mm
    "26700": 0.0059,    # pi x 26mm x 70mm
    "38120": 0.0143,
    "40152": 0.0191,
    "prismatic": 0.060,  # typical 100Ah prismatic ~173x72x220mm -> 2*(173*220+72*220+173*72)/1e6
    "blade": 0.080,      # BYD blade cells are long and thin
    "pouch": 0.025,
}


def _estimate_heat_generation(variant: ExpandedVariant) -> tuple[float, float]:
    """Calculate I²R heat generation.

    Returns:
        (total_heat_w, heat_per_cell_w)
    """
    cell = variant.base_candidate.cell
    r_ohm = cell.dcir_10s_ohms or get_fallback_for_cell("dcir_10s_ohms", cell)

    # Use continuous current if available, else estimate from energy
    if variant.base_candidate.continuous_current_a:
        i_per_cell = variant.base_candidate.continuous_current_a / variant.parallel_count
    else:
        # Fallback: assume 1C discharge
        i_per_cell = cell.capacity_ah_nom or get_fallback_for_cell("capacity_ah_nom", cell)

    heat_per_cell = i_per_cell ** 2 * r_ohm
    total_heat = heat_per_cell * variant.total_cells

    return round(total_heat, 2), round(heat_per_cell, 4)


def _estimate_cooling_surface(variant: ExpandedVariant) -> float:
    """Estimate total cooling surface area in m²."""
    cell = variant.base_candidate.cell
    fmt = cell.format or "cylindrical"
    per_cell_area = CELL_SURFACE_AREA_M2.get(fmt, 0.005)
    # Effective cooling surface ≈ 40% of total cell surface (contact area)
    return variant.total_cells * per_cell_area * 0.40


def _estimate_tmax(
    total_heat_w: float,
    cooling_surface_m2: float,
    cooling_method: str,
) -> float:
    """Estimate T_max using simple thermal resistance model.

    T_max = T_ambient + Q / (h × A)
    """
    h = COOLING_CAPACITY.get(cooling_method, 50.0)
    if cooling_surface_m2 <= 0:
        return T_AMBIENT + 100  # effectively infeasible
    delta_t = total_heat_w / (h * cooling_surface_m2)
    return round(T_AMBIENT + delta_t, 1)


def _optimize_cooling(
    variant: ExpandedVariant,
    total_heat_w: float,
    cooling_surface_m2: float,
) -> str:
    """ThermalCoolingOptimizer: downgrade cooling if margin allows."""
    current = variant.cooling_baseline
    downgrade_order = ["liquid", "active-air", "passive"]

    idx = downgrade_order.index(current) if current in downgrade_order else 0

    # Try downgrading
    for i in range(idx + 1, len(downgrade_order)):
        cheaper = downgrade_order[i]
        t_max = _estimate_tmax(total_heat_w, cooling_surface_m2, cheaper)
        if t_max < T_CUTOFF - 5.0:  # 5°C safety margin
            return cheaper

    return current


def _check_volume_fit(variant: ExpandedVariant, max_volume_l: float | None) -> bool:
    """Check if the pack fits within volume constraints."""
    if not max_volume_l:
        return True

    cell = variant.base_candidate.cell
    # Estimate cell volume in liters
    if cell.volume_l:
        cell_vol_l = cell.volume_l
    elif cell.width_diameter_mm and cell.height_mm:
        cell_vol_l = math.pi * (cell.width_diameter_mm / 2) ** 2 * cell.height_mm / 1e6
    elif cell.length_mm and cell.width_diameter_mm and cell.height_mm:
        cell_vol_l = cell.length_mm * cell.width_diameter_mm * cell.height_mm / 1e6
    else:
        cell_vol_l = get_fallback_for_cell("volume_l", cell) or 0.050

    # Pack volume = cells + 40% overhead (holders, BMS, wiring, gaps)
    pack_vol_l = cell_vol_l * variant.total_cells * 1.40

    return pack_vol_l <= max_volume_l


def filter_thermal_feasibility(
    variants: list[ExpandedVariant],
    requirements: ParsedRequirements,
) -> list[ExpandedVariant]:
    """Filter variants by thermal feasibility and optimize cooling.

    Args:
        variants: Expanded variants from Step 5
        requirements: Parsed requirements (for volume constraints)

    Returns:
        Thermally feasible variants with optimized cooling assignments
    """
    feasible: list[ExpandedVariant] = []

    for variant in variants:
        # Volume check
        if not _check_volume_fit(variant, requirements.max_volume_l):
            continue

        total_heat, _ = _estimate_heat_generation(variant)
        cooling_surface = _estimate_cooling_surface(variant)

        # Check feasibility with current cooling
        t_max = _estimate_tmax(total_heat, cooling_surface, variant.cooling_baseline)
        if t_max >= T_CUTOFF:
            # Try upgrading cooling
            for method in ["active-air", "liquid"]:
                t_max = _estimate_tmax(total_heat, cooling_surface, method)
                if t_max < T_CUTOFF:
                    variant.cooling_baseline = method
                    break
            else:
                continue  # reject — no cooling method works

        # Optimize: try downgrading if margin allows
        variant.cooling_baseline = _optimize_cooling(variant, total_heat, cooling_surface)

        feasible.append(variant)

    return feasible
