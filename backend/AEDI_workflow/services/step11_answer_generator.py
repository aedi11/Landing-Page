"""
Step 11: AnswerGenerator
Uses LangChain structured output to generate professional technical datasheets.
UPDATED: application-specific standards, expanded BMS IC database,
telecom/ESS-grade BMS recommendations, includes user-specified features.
"""

from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from ..config import llm
from ..models.output import RankedCandidate, CandidateReport, FinalReport, BMSRecommendation
from ..models.requirements import ParsedRequirements

SYSTEM_PROMPT = """\
You are a senior battery systems engineer generating a professional technical report \
for a battery pack design. Based on the ranked candidates and their specifications, \
generate a complete CandidateReport for each candidate.

Rules:
- Assign variant names: Rank 1 = best overall, Rank 2 = runner-up, Rank 3 = alternative
- Recommend appropriate BMS IC based on series count (see BMS IC database in context)
- List realistic pros and cons for each design
- Include safety standards compliance notes appropriate to the application
- Be specific with part numbers and specifications
- For telecom/ESS applications, emphasize: cycle life, reliability, remote monitoring, wide temp range
- For EV applications, emphasize: energy density, weight, C-rate capability, safety
"""

VARIANT_NAMES = [
    "Performance Optimized",
    "Cost Optimized",
    "Space Optimized",
]

# Application-specific safety standards
STANDARDS_BY_APP: dict[str, list[str]] = {
    # EV / mobility -- Indian standards
    "e-bike": ["AIS-156 Amendment 3", "UN 38.3", "IEC 62133-2"],
    "e-scooter": ["AIS-156 Amendment 3", "UN 38.3", "IEC 62133-2"],
    "e-motorcycle": ["AIS-156 Amendment 3", "UN 38.3", "IEC 62133-2"],
    "e-rickshaw": ["AIS-156 Amendment 3", "UN 38.3", "IEC 62133-2"],
    "e-auto": ["AIS-156 Amendment 3", "UN 38.3", "IEC 62133-2"],
    "delivery": ["AIS-156 Amendment 3", "UN 38.3", "IEC 62133-2"],
    # Stationary / telecom / ESS
    "telecom-backup": ["IEC 62619", "UL 1973", "UN 38.3", "IEC 62040 (UPS)", "TL 9000 (Telecom)"],
    "solar-ess": ["IEC 62619", "UL 1973", "UL 9540", "UN 38.3"],
    "ups": ["IEC 62619", "UL 1973", "IEC 62040", "UN 38.3"],
    "data-center-ups": ["IEC 62619", "UL 1973", "UL 9540A", "NFPA 855", "UN 38.3"],
    "industrial-ess": ["IEC 62619", "UL 1973", "UL 9540", "UN 38.3"],
    "marine": ["IEC 62619", "DNV GL", "UN 38.3"],
}
DEFAULT_STANDARDS = ["IEC 62619", "UN 38.3", "IEC 62133-2"]

# Expanded BMS IC lookup table
# (min_series, max_series) -> {ic, mfr, comm, notes}
BMS_IC_DB = {
    (3, 10): {"ic": "BQ76942", "mfr": "Texas Instruments", "comm": "I2C",
              "notes": "3-10S AFE with integrated protector FETs driver"},
    (3, 16): {"ic": "BQ76952", "mfr": "Texas Instruments", "comm": "UART",
              "notes": "3-16S AFE, industry standard for EV/ESS"},
    (7, 14): {"ic": "MC33771C", "mfr": "NXP", "comm": "SPI",
              "notes": "Automotive-grade, ISO 26262 ASIL-D"},
    (6, 18): {"ic": "ADBMS1818", "mfr": "Analog Devices", "comm": "SPI",
              "notes": "18-cell monitor, isoSPI daisy-chain for high-S stacking"},
    (6, 14): {"ic": "ISL94216", "mfr": "Renesas", "comm": "I2C",
              "notes": "6-14S, integrated cell balancing"},
    (8, 16): {"ic": "MAX17853", "mfr": "Analog Devices/Maxim", "comm": "UART",
              "notes": "8-16S, ASIL-D, used in automotive and ESS"},
}

# Telecom-grade BMS systems (complete solutions, not just ICs)
TELECOM_BMS_DB = {
    (14, 16): {"ic": "BQ76952", "mfr": "Texas Instruments", "comm": "UART/RS485",
               "notes": "16S LFP standard, with external MCU for WiFi/MODBUS"},
    (14, 17): {"ic": "AFE+MCU (custom)", "mfr": "TI BQ76952 + STM32",
               "comm": "RS485/MODBUS/WiFi",
               "notes": "Telecom-grade BMS with remote monitoring, SNMP/MODBUS support"},
}

# Stationary application types
STATIONARY_APPS = {"telecom-backup", "solar-ess", "ups", "data-center-ups", "industrial-ess", "marine"}


def _select_bms(series_count: int, app_type: str, requirements: ParsedRequirements) -> BMSRecommendation:
    """Select appropriate BMS IC based on series count and application."""
    stacking_notes = None
    app_key = app_type.lower().replace(" ", "-")
    is_stationary = app_key in STATIONARY_APPS

    # For telecom/stationary apps, try telecom-specific BMS first
    selected = None
    if is_stationary:
        for (s_min, s_max), ic_info in TELECOM_BMS_DB.items():
            if s_min <= series_count <= s_max:
                selected = ic_info
                break

    # Fallback to general BMS IC DB
    if not selected:
        for (s_min, s_max), ic_info in BMS_IC_DB.items():
            if s_min <= series_count <= s_max:
                selected = ic_info
                break

    if not selected:
        # Series count exceeds single IC -- need stacking
        if series_count <= 32:
            selected = {"ic": "BQ76952", "mfr": "Texas Instruments", "comm": "UART"}
            stacking_notes = f"2x {selected['ic']} stacked for {series_count}S support"
        else:
            selected = {"ic": "ADBMS1818", "mfr": "Analog Devices", "comm": "SPI"}
            n_ics = (series_count + 17) // 18
            stacking_notes = f"{n_ics}x {selected['ic']} daisy-chained"

    # Communication protocol based on application
    comm = selected["comm"]
    if is_stationary:
        # Stationary apps typically use RS485/MODBUS or CAN
        if requirements.monitoring_features:
            features_str = " ".join(requirements.monitoring_features).lower()
            if "wifi" in features_str:
                comm = "UART + WiFi (ESP32)"
            elif "modbus" in features_str or "rs485" in features_str:
                comm = "RS485/MODBUS"
            elif "can" in features_str:
                comm = "CAN"
            else:
                comm = "RS485/MODBUS"
        else:
            comm = "RS485/MODBUS"
    elif "motorcycle" in app_type.lower():
        comm = "CAN"
    elif "bike" in app_type.lower():
        comm = "I2C"

    # Balancing: active for stationary (longer life), passive for EV (simpler)
    balancing = "active" if is_stationary else "passive"

    return BMSRecommendation(
        ic_manufacturer=selected["mfr"],
        ic_part_number=selected["ic"],
        topology="centralized" if series_count <= 16 else "distributed",
        supported_series=f"{series_count}S" + (f" ({stacking_notes})" if stacking_notes else ""),
        balancing=balancing,
        communication=comm,
        stacking_notes=stacking_notes,
    )


def _get_standards(app_type: str) -> list[str]:
    """Get safety/compliance standards for the application type."""
    app_key = app_type.lower().replace(" ", "-")
    return STANDARDS_BY_APP.get(app_key, DEFAULT_STANDARDS)


def _build_notes(requirements: ParsedRequirements) -> list[str]:
    """Build compliance and feature notes for the report."""
    notes = []

    # Standards compliance
    standards = _get_standards(requirements.application_type)
    for std in standards:
        notes.append(f"Compliant with {std}")

    # Protection features
    for feature in requirements.protection_features:
        notes.append(f"Protection: {feature}")

    # Monitoring features
    for feature in requirements.monitoring_features:
        notes.append(f"Monitoring: {feature}")

    # Enclosure
    if requirements.enclosure_type:
        notes.append(f"Enclosure: {requirements.enclosure_type}")

    return notes


def _build_report_context(candidates: list[RankedCandidate]) -> str:
    """Build context string for LLM report generation."""
    lines = []
    for cand in candidates:
        cell = cand.variant.base_candidate.cell
        lines.append(
            f"Rank {cand.rank}: {cell.manufacturer} {cell.cell_name} ({cell.chemistry} {cell.format})\n"
            f"  Config: {cand.variant.base_candidate.series_count}S{cand.variant.parallel_count}P "
            f"({cand.variant.total_cells} cells)\n"
            f"  Voltage: {cand.variant.base_candidate.pack_voltage_v}V, "
            f"Capacity: {cand.variant.pack_capacity_ah}Ah, "
            f"Energy: {cand.variant.pack_energy_wh}Wh\n"
            f"  Weight: {cand.variant.estimated_weight_kg}kg, "
            f"Cooling: {cand.variant.cooling_baseline}\n"
            f"  Score: {cand.total_score}"
        )
        if cand.thermal_result:
            lines.append(
                f"  Thermal: T_max={cand.thermal_result.t_max_estimated_c}C, "
                f"margin={cand.thermal_result.thermal_margin_c}C"
            )
    return "\n".join(lines)


class LLMReportOutput(BaseModel):
    """LLM output for generating pros/cons/summary."""
    summary: str
    pros: list[str]
    cons: list[str]
    recommendation_note: str


_report_prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human",
     "Generate a report summary, pros, and cons for this battery pack design:\n\n"
     "Cell: {cell_info}\n"
     "Configuration: {config}\n"
     "Application: {app_type}\n"
     "Cooling: {cooling}\n"
     "Thermal: {thermal_info}\n"
     "Special features: {features}"),
])
_report_chain = _report_prompt | llm.with_structured_output(LLMReportOutput)


def generate_report(
    candidates: list[RankedCandidate],
    requirements: ParsedRequirements,
) -> FinalReport:
    """Generate the final technical report with top 3 candidates.

    Args:
        candidates: Final ranked candidates from Step 10
        requirements: Original parsed requirements

    Returns:
        FinalReport with candidate datasheets and recommendation
    """
    top_3 = candidates[:3]
    reports: list[CandidateReport] = []
    standards = _get_standards(requirements.application_type)
    notes_template = _build_notes(requirements)

    for i, cand in enumerate(top_3):
        cell = cand.variant.base_candidate.cell
        bms = _select_bms(
            cand.variant.base_candidate.series_count,
            requirements.application_type,
            requirements,
        )

        # LLM: generate summary, pros, cons
        thermal_info = "No simulation data"
        if cand.thermal_result:
            thermal_info = (
                f"T_max={cand.thermal_result.t_max_estimated_c}C, "
                f"margin={cand.thermal_result.thermal_margin_c}C, "
                f"heat={cand.thermal_result.heat_generation_w}W"
            )

        # Build features string from requirements
        features_parts = []
        if requirements.protection_features:
            features_parts.append(f"Protection: {', '.join(requirements.protection_features)}")
        if requirements.monitoring_features:
            features_parts.append(f"Monitoring: {', '.join(requirements.monitoring_features)}")
        if requirements.enclosure_type:
            features_parts.append(f"Enclosure: {requirements.enclosure_type}")
        features_str = "; ".join(features_parts) if features_parts else "Standard"

        try:
            llm_report = _report_chain.invoke({
                "cell_info": f"{cell.manufacturer} {cell.cell_name} ({cell.chemistry}, "
                             f"{cell.capacity_ah_nom}Ah, {cell.format})",
                "config": (
                    f"{cand.variant.base_candidate.series_count}S{cand.variant.parallel_count}P, "
                    f"{cand.variant.pack_energy_wh}Wh, {cand.variant.estimated_weight_kg}kg"
                ),
                "app_type": requirements.application_type,
                "cooling": cand.variant.cooling_baseline,
                "thermal_info": thermal_info,
                "features": features_str,
            })
            summary = llm_report.summary
            pros = llm_report.pros
            cons = llm_report.cons
        except Exception:
            summary = f"{cell.manufacturer} {cell.cell_name} based design"
            pros = ["Feasible configuration"]
            cons = ["Requires further validation"]

        variant_name = VARIANT_NAMES[i] if i < len(VARIANT_NAMES) else f"Variant {i+1}"

        reports.append(CandidateReport(
            rank=cand.rank,
            variant_name=variant_name,
            summary=summary,
            cell_manufacturer=cell.manufacturer,
            cell_model=cell.cell_name,
            chemistry=cell.chemistry,
            form_factor=cell.format,
            series_count=cand.variant.base_candidate.series_count,
            parallel_count=cand.variant.parallel_count,
            total_cells=cand.variant.total_cells,
            pack_voltage_v=cand.variant.base_candidate.pack_voltage_v,
            pack_capacity_ah=cand.variant.pack_capacity_ah,
            pack_energy_wh=cand.variant.pack_energy_wh,
            usable_energy_wh=cand.variant.usable_energy_wh,
            estimated_weight_kg=cand.variant.estimated_weight_kg,
            continuous_c_rate=cand.variant.base_candidate.continuous_c_rate,
            peak_c_rate=cand.variant.base_candidate.peak_c_rate,
            cooling_method=cand.variant.cooling_baseline,
            t_max_c=cand.thermal_result.t_max_estimated_c if cand.thermal_result else None,
            bms=bms,
            pros=pros,
            cons=cons,
            notes=notes_template,
        ))

    # Generate final recommendation
    if reports:
        top = reports[0]
        recommendation = (
            f"Recommended: {top.variant_name} -- {top.cell_manufacturer} {top.cell_model} "
            f"({top.series_count}S{top.parallel_count}P, {top.pack_energy_wh}Wh, "
            f"{top.estimated_weight_kg}kg, {top.cooling_method} cooling)"
        )
    else:
        recommendation = "No feasible candidates found. Please adjust requirements."

    return FinalReport(
        request_summary=(
            f"{requirements.application_type} -- {requirements.target_voltage_v}V, "
            f"{requirements.target_energy_wh}Wh target"
        ),
        candidates=reports,
        recommendation=recommendation,
        standards_compliance=standards,
    )
