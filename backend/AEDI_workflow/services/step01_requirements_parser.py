"""
Step 1: RequirementsParser
Uses LangChain structured output to extract user requirements into a Pydantic model.
NO raw text prompting — all outputs are strictly typed.
"""

from langchain_core.prompts import ChatPromptTemplate
from ..config import llm
from ..models.requirements import ParsedRequirements, UserRequirements

SYSTEM_PROMPT = """\
You are an expert battery systems engineer. Extract structured battery pack design \
requirements from the user's natural language query.

Supported application types (use these exact strings):
- EV/mobility: e-scooter, e-bike, e-motorcycle, e-rickshaw, e-auto, delivery
- Stationary/industrial: telecom-backup, solar-ess, ups, industrial-ess, marine, data-center-ups

Rules:
- Identify the application type from the list above
- Extract voltage, energy, power, weight, and volume targets
- Map common shorthand: "48V 2kWh scooter" → voltage=48, energy=2000, app=e-scooter
- Telecom/BTS/tower backup → application_type="telecom-backup"
- Solar/home storage → application_type="solar-ess"
- UPS/data center → application_type="ups" or "data-center-ups"
- If voltage is not specified, infer from application type:
  - e-bike=48V, e-scooter=48-60V, e-motorcycle=72V
  - telecom-backup=48V (note: -48V DC systems use 51.2V nominal LFP packs)
  - solar-ess=48V, ups=48V
- If energy is not specified but capacity (Ah) and voltage are given, compute energy = voltage × capacity
- Extract explicit cell configuration if user specifies it:
  - "16S1P" → target_series_count=16, target_parallel_count=1
  - "15S2P" → target_series_count=15, target_parallel_count=2
- Extract explicit capacity if specified: "100Ah" → target_capacity_ah=100
- Extract discharge current: "100A continuous" → target_discharge_current_a=100
- Extract peak current if specified: "200A peak" → target_peak_current_a=200
- Extract protection features: MCB (with rating), fuse, contactor, precharge circuit
- Extract monitoring features: WiFi, Bluetooth, RS485, CAN, MODBUS, LCD display, LED indicators
- Extract enclosure type: 19-inch rack-mount, wall-mount, IP65 outdoor, etc.
- For chemistry, map common names: LiFePO4/LFP/iron phosphate → "LFP", NMC/lithium nickel → "NMC"
- For form factor: prismatic, cylindrical, pouch, blade
- Set confidence < 0.8 if critical fields (voltage, energy, application) are missing
- Add follow_up_questions for any ambiguous or missing critical fields
- Do NOT hallucinate values — use None for genuinely unknown optional fields
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "Design requirements: {query}"),
])

# LangChain structured output chain — forces Pydantic schema compliance
_chain = prompt | llm.with_structured_output(ParsedRequirements)


def parse_requirements(user_input: UserRequirements) -> ParsedRequirements:
    """Parse natural language requirements into structured format.

    Args:
        user_input: Raw user query

    Returns:
        ParsedRequirements with all extracted fields
    """
    result: ParsedRequirements = _chain.invoke({"query": user_input.query})

    # Auto-derive capacity if missing but voltage and energy are present
    if result.target_capacity_ah is None and result.target_energy_wh and result.target_voltage_v:
        result.target_capacity_ah = round(result.target_energy_wh / result.target_voltage_v, 2)

    return result
