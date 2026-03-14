"""
Step 4: Validation + Feedback (TopologyRegulator / CurrentRegulator)
Pure deterministic — NO LLM calls. Validates and fixes S/P configurations.
UPDATED: handles explicit discharge current, wider tolerance for stationary apps,
respects user-specified S/P configurations.
"""

import math
from ..defaults import get_fallback_for_cell
from ..models.requirements import ParsedRequirements
from ..models.rules import DesignRules
from ..models.candidates import PackCandidate, ValidatedCandidate

# Voltage tolerance: pack voltage must be within ±5% of target (±10% for stationary)
VOLTAGE_TOLERANCE_EV = 0.05
VOLTAGE_TOLERANCE_STATIONARY = 0.10

# Stationary application types that get wider voltage tolerance
STATIONARY_APPS = {"telecom-backup", "solar-ess", "ups", "data-center-ups", "industrial-ess", "marine"}

# Energy tolerance: pack energy must be within ±15% of target
ENERGY_TOLERANCE = 0.15


def _get_voltage_tolerance(app_type: str) -> float:
    """Get voltage tolerance based on application type."""
    app_key = app_type.lower().replace(" ", "-")
    return VOLTAGE_TOLERANCE_STATIONARY if app_key in STATIONARY_APPS else VOLTAGE_TOLERANCE_EV


def _validate_voltage(candidate: PackCandidate, target_v: float, tolerance: float,
                      user_specified_s: bool) -> tuple[bool, list[str]]:
    """Check if pack voltage is within tolerance of target.

    If user explicitly specified S count, skip voltage adjustment — trust their config.
    """
    notes = []

    if user_specified_s:
        # User explicitly chose S — don't adjust, just note the actual voltage
        if abs(candidate.pack_voltage_v - target_v) / target_v > tolerance:
            notes.append(
                f"User-specified {candidate.series_count}S gives {candidate.pack_voltage_v:.1f}V "
                f"(target {target_v}V, {abs(candidate.pack_voltage_v - target_v)/target_v*100:.1f}% deviation)"
            )
        return True, notes

    ratio = abs(candidate.pack_voltage_v - target_v) / target_v

    if ratio > tolerance:
        # TopologyRegulator: try adjusting S by +/- 1
        cell_v = candidate.cell.voltage_nom_v
        s_low = math.floor(target_v / cell_v)
        s_high = math.ceil(target_v / cell_v)

        v_low = s_low * cell_v
        v_high = s_high * cell_v

        best_s = s_low if abs(v_low - target_v) < abs(v_high - target_v) else s_high
        best_v = best_s * cell_v

        if abs(best_v - target_v) / target_v <= tolerance:
            notes.append(
                f"TopologyRegulator: adjusted S from {candidate.series_count} to {best_s} "
                f"(voltage {candidate.pack_voltage_v:.1f}V -> {best_v:.1f}V)"
            )
            candidate.series_count = best_s
            candidate.pack_voltage_v = round(best_v, 2)
            candidate.total_cells = best_s * candidate.parallel_count
            candidate.pack_energy_wh = round(best_v * candidate.pack_capacity_ah, 2)
            return True, notes
        else:
            notes.append(f"Voltage {candidate.pack_voltage_v:.1f}V exceeds +/-{tolerance*100:.0f}% of target {target_v}V")
            return False, notes

    return True, notes


def _validate_current(
    candidate: PackCandidate,
    max_cont_c: float,
    max_peak_c: float,
    requirements: ParsedRequirements,
    user_specified_p: bool,
) -> tuple[bool, list[str]]:
    """Check C-rate limits, increase P if needed (CurrentRegulator).

    If user specified P explicitly, do NOT auto-increase P — just warn.
    """
    notes = []
    ok = True

    if candidate.continuous_c_rate and candidate.continuous_c_rate > max_cont_c:
        if user_specified_p:
            # User chose P — warn but don't adjust
            notes.append(
                f"Warning: continuous C-rate {candidate.continuous_c_rate:.2f}C exceeds limit {max_cont_c:.2f}C "
                f"with user-specified {candidate.parallel_count}P"
            )
        else:
            # CurrentRegulator: increase P to bring C-rate within limits
            cont_current = requirements.target_discharge_current_a
            if not cont_current and requirements.nominal_power_w:
                cont_current = requirements.nominal_power_w / candidate.pack_voltage_v

            if cont_current:
                required_p = math.ceil(
                    cont_current / (max_cont_c * candidate.cell.capacity_ah_nom)
                )
                notes.append(
                    f"CurrentRegulator: increased P from {candidate.parallel_count} to {required_p} "
                    f"(continuous C-rate {candidate.continuous_c_rate:.2f}C -> "
                    f"{(cont_current / required_p / candidate.cell.capacity_ah_nom):.2f}C)"
                )
                candidate.parallel_count = required_p
                candidate.total_cells = candidate.series_count * required_p
                candidate.pack_capacity_ah = round(required_p * candidate.cell.capacity_ah_nom, 2)
                candidate.pack_energy_wh = round(candidate.pack_voltage_v * candidate.pack_capacity_ah, 2)
                candidate.continuous_c_rate = round(
                    cont_current / required_p / candidate.cell.capacity_ah_nom, 3
                )
                # Recalculate weight
                cell_weight_kg = candidate.total_cells * (candidate.cell.mass_kg or get_fallback_for_cell("mass_kg", candidate.cell))
                candidate.estimated_weight_kg = round(cell_weight_kg * 1.30, 2)

    if candidate.peak_c_rate and candidate.peak_c_rate > max_peak_c:
        if user_specified_p:
            notes.append(
                f"Warning: peak C-rate {candidate.peak_c_rate:.2f}C exceeds limit {max_peak_c:.2f}C "
                f"with user-specified {candidate.parallel_count}P"
            )
        elif requirements.target_peak_current_a or requirements.peak_power_w:
            peak_current = requirements.target_peak_current_a
            if not peak_current and requirements.peak_power_w:
                peak_current = requirements.peak_power_w / candidate.pack_voltage_v

            if peak_current:
                required_p = math.ceil(
                    peak_current / (max_peak_c * candidate.cell.capacity_ah_nom)
                )
                if required_p > candidate.parallel_count:
                    notes.append(
                        f"CurrentRegulator: increased P to {required_p} for peak C-rate compliance"
                    )
                    candidate.parallel_count = required_p
                    candidate.total_cells = candidate.series_count * required_p
                    candidate.pack_capacity_ah = round(required_p * candidate.cell.capacity_ah_nom, 2)
                    candidate.pack_energy_wh = round(candidate.pack_voltage_v * candidate.pack_capacity_ah, 2)
                    cell_weight_kg = candidate.total_cells * (candidate.cell.mass_kg or get_fallback_for_cell("mass_kg", candidate.cell))
                    candidate.estimated_weight_kg = round(cell_weight_kg * 1.30, 2)

    return ok, notes


def _validate_weight(candidate: PackCandidate, max_weight: float | None) -> tuple[bool, list[str]]:
    """Check if pack weight is within limit."""
    if max_weight and candidate.estimated_weight_kg > max_weight:
        return False, [f"Weight {candidate.estimated_weight_kg:.1f}kg exceeds limit {max_weight}kg"]
    return True, []


def validate_candidates(
    candidates: list[PackCandidate],
    requirements: ParsedRequirements,
    rules: DesignRules,
) -> list[ValidatedCandidate]:
    """Validate all candidates against voltage, current, and weight constraints.

    Args:
        candidates: Raw candidates from Step 3
        requirements: Parsed requirements
        rules: Design rules with C-rate limits

    Returns:
        List of ValidatedCandidate that passed all checks
    """
    # Extract C-rate limits from rules (use first rule or defaults)
    max_cont_c = 1.5
    max_peak_c = 3.0
    if rules.current_rules:
        max_cont_c = rules.current_rules[0].max_continuous_c_rate
        max_peak_c = rules.current_rules[0].max_peak_c_rate

    voltage_tolerance = _get_voltage_tolerance(requirements.application_type)
    user_specified_s = requirements.target_series_count is not None
    user_specified_p = requirements.target_parallel_count is not None

    validated: list[ValidatedCandidate] = []

    for cand in candidates:
        all_notes: list[str] = []

        v_ok, v_notes = _validate_voltage(cand, requirements.target_voltage_v, voltage_tolerance, user_specified_s)
        all_notes.extend(v_notes)

        c_ok, c_notes = _validate_current(cand, max_cont_c, max_peak_c, requirements, user_specified_p)
        all_notes.extend(c_notes)

        w_ok, w_notes = _validate_weight(cand, requirements.max_weight_kg)
        all_notes.extend(w_notes)

        if v_ok and w_ok:
            validated.append(ValidatedCandidate(
                **cand.model_dump(),
                voltage_ok=v_ok,
                current_ok=c_ok,
                weight_ok=w_ok,
                topology_notes=all_notes,
            ))

    return validated
