"""
Step 9: Analytical Thermal Simulation (Ansys fallback)
Pure physics — NO LLM calls. Robust I²R heat generation and T_max estimation.
"""

import math
from ..defaults import get_fallback_for_cell
from ..models.output import RankedCandidate
from ..models.thermal import ThermalResult, CoolingStrategy

# Physical constants and material properties
T_AMBIENT = 40.0       # Worst-case ambient (°C) — Indian tropical climate
T_CUTOFF = 60.0        # Pack thermal cutoff (°C)
STEFAN_BOLTZMANN = 5.67e-8  # W/(m²·K⁴)
EMISSIVITY_AL = 0.09   # Polished aluminum
EMISSIVITY_PAINTED = 0.90  # Painted/anodized aluminum

# Convective heat transfer coefficients (W/(m²·K))
H_NATURAL_CONV = 10.0      # Natural convection (passive)
H_FORCED_AIR = 50.0        # Forced air (12V blower)
H_LIQUID = 500.0           # Liquid cooling plate

# Cell surface area by format (m²)
CELL_AREA: dict[str, float] = {
    "18650": 0.0038,
    "21700": 0.0046,
    "26700": 0.0059,
    "38120": 0.0143,
    "40152": 0.0191,
    "prismatic": 0.060,  # typical 100Ah prismatic ~173x72x220mm
    "blade": 0.080,
    "pouch": 0.025,
}


def _calc_heat_generation(candidate: RankedCandidate) -> tuple[float, float]:
    """Calculate continuous I²R heat generation.

    Returns:
        (total_heat_w, heat_per_cell_w)
    """
    cell = candidate.variant.base_candidate.cell
    p = candidate.variant.parallel_count
    total_cells = candidate.variant.total_cells

    r_ohm = cell.dcir_10s_ohms or get_fallback_for_cell("dcir_10s_ohms", cell)

    if candidate.variant.base_candidate.continuous_current_a:
        i_total = candidate.variant.base_candidate.continuous_current_a
        i_per_cell = i_total / p
    else:
        i_per_cell = cell.capacity_ah_nom or get_fallback_for_cell("capacity_ah_nom", cell)  # Assume 1C

    heat_per_cell = i_per_cell ** 2 * r_ohm
    total_heat = heat_per_cell * total_cells

    return round(total_heat, 3), round(heat_per_cell, 5)


def _calc_cooling_surface(candidate: RankedCandidate) -> float:
    """Estimate effective cooling surface area in m²."""
    cell = candidate.variant.base_candidate.cell
    fmt = cell.format or "cylindrical"
    per_cell = CELL_AREA.get(fmt, 0.005)

    # Effective surface: ~50% of total (contact with heatsink/thermal pad)
    return candidate.variant.total_cells * per_cell * 0.50


def _calc_cooling_capacity(surface_m2: float, method: str) -> float:
    """Calculate cooling capacity in watts for given method and surface area."""
    h_map = {
        "passive": H_NATURAL_CONV,
        "active-air": H_FORCED_AIR,
        "liquid": H_LIQUID,
    }
    h = h_map.get(method, H_NATURAL_CONV)
    # Q_cool = h × A × ΔT_max (using max allowable ΔT = T_cutoff - T_ambient)
    delta_t_max = T_CUTOFF - T_AMBIENT
    return round(h * surface_m2 * delta_t_max, 2)


def _estimate_tmax(total_heat_w: float, surface_m2: float, method: str) -> float:
    """Estimate steady-state T_max using lumped thermal model.

    T_max = T_ambient + Q_gen / (h × A_eff)

    Includes radiation for passive cooling.
    """
    h_map = {
        "passive": H_NATURAL_CONV,
        "active-air": H_FORCED_AIR,
        "liquid": H_LIQUID,
    }
    h_conv = h_map.get(method, H_NATURAL_CONV)

    if surface_m2 <= 0:
        return T_AMBIENT + 100.0  # infeasible

    # Convective cooling
    delta_t_conv = total_heat_w / (h_conv * surface_m2)

    # Add radiative cooling benefit for passive (reduces T_max slightly)
    if method == "passive":
        # Linearized radiation: h_rad ≈ 4 × ε × σ × T_avg³
        t_avg_k = 273.15 + T_AMBIENT + delta_t_conv / 2
        h_rad = 4 * EMISSIVITY_PAINTED * STEFAN_BOLTZMANN * t_avg_k ** 3
        h_total = h_conv + h_rad
        delta_t = total_heat_w / (h_total * surface_m2)
    else:
        delta_t = delta_t_conv

    return round(T_AMBIENT + delta_t, 1)


def run_thermal_simulation(candidate: RankedCandidate) -> ThermalResult:
    """Run analytical thermal simulation for a single candidate.

    Args:
        candidate: A ranked candidate from Step 7

    Returns:
        ThermalResult with heat generation, T_max, and feasibility
    """
    total_heat, heat_per_cell = _calc_heat_generation(candidate)
    surface = _calc_cooling_surface(candidate)
    method = candidate.variant.cooling_baseline

    cooling_cap = _calc_cooling_capacity(surface, method)
    t_max = _estimate_tmax(total_heat, surface, method)
    margin = T_CUTOFF - t_max
    feasible = t_max < T_CUTOFF

    # Build cooling strategy details
    cooling_strat = CoolingStrategy(method=method)
    if method == "passive":
        cooling_strat.thermal_pad_conductivity_w_mk = 4.0
    elif method == "active-air":
        cooling_strat.fan_power_w = 5.0
        cooling_strat.heatsink_area_cm2 = round(surface * 1e4, 1)
    elif method == "liquid":
        cooling_strat.coolant_flow_rate_lpm = 2.0

    recommendation = None
    if not feasible:
        recommendation = f"T_max ({t_max}°C) exceeds cutoff ({T_CUTOFF}°C). Upgrade cooling or reduce power."
    elif margin < 5:
        recommendation = f"Low thermal margin ({margin:.1f}°C). Consider upgrading cooling for reliability."

    return ThermalResult(
        variant_label=candidate.variant.variant_label,
        cell_model=candidate.variant.base_candidate.cell.cell_name,
        heat_generation_w=total_heat,
        heat_per_cell_w=heat_per_cell,
        cooling_capacity_w=cooling_cap,
        t_ambient_c=T_AMBIENT,
        t_max_estimated_c=t_max,
        thermal_margin_c=round(margin, 1),
        feasible=feasible,
        cooling_strategy=cooling_strat,
        recommendation=recommendation,
    )
