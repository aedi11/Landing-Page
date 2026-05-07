import asyncio
import os
import json

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv(override=True)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="AEDI BOM Generator", version="0.3.0")

DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://chunchreek.com",
    "https://www.chunchreek.com",
]


def get_allowed_origins() -> list[str]:
    raw_origins = os.getenv("CORS_ORIGINS", "")
    env_origins = [origin.strip().rstrip("/") for origin in raw_origins.split(",") if origin.strip()]
    return list(dict.fromkeys(DEFAULT_CORS_ORIGINS + env_origins))


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── OpenAI client ─────────────────────────────────────────────────────────────
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── Pydantic models ──────────────────────────────────────────────────────────


class ReasoningStep(BaseModel):
    step_number: int = Field(description="Sequential step number starting from 1")
    title: str = Field(description="Short title, e.g. 'Applying Knowledge Model'")
    description: str = Field(description="1-2 sentence explanation of what was analyzed or decided")


class CellSpec(BaseModel):
    manufacturer: str = Field(description="Cell manufacturer name")
    model: str = Field(description="Cell model / part number")
    form_factor: str = Field(description="pouch | cylindrical | prismatic")
    chemistry: str = Field(description="e.g. NMC811, LFP, NCA")
    nominal_voltage_v: float = Field(description="Nominal voltage in volts")
    capacity_ah: float = Field(description="Rated capacity in Ah")
    max_continuous_discharge_a: float = Field(description="Max continuous discharge current in A")
    weight_g: float = Field(description="Cell weight in grams")
    dimensions: str = Field(description="Dimensions (LxWxH or diameter x height)")


class PackConfiguration(BaseModel):
    series_count: int = Field(description="Number of cells in series (S)")
    parallel_count: int = Field(description="Number of cells in parallel (P)")
    total_cells: int = Field(description="Total number of cells")
    nominal_voltage_v: float = Field(description="Pack nominal voltage")
    total_capacity_ah: float = Field(description="Total pack capacity in Ah")
    total_energy_wh: float = Field(description="Total pack energy in Wh")
    estimated_pack_weight_kg: float = Field(description="Estimated total pack weight in kg")


class BMSSpec(BaseModel):
    topology: str = Field(description="e.g. centralized, distributed, modular")
    ic_manufacturer: str = Field(description="BMS IC manufacturer")
    ic_part_number: str = Field(description="BMS IC part number")
    cell_balancing_method: str = Field(description="passive | active")
    supported_series_cells: str = Field(description="Number of series cells supported")
    communication_protocol: str = Field(description="e.g. I2C, SPI, UART, CAN")
    protection_features: list[str] = Field(description="List of protection features")


class CoolingSpec(BaseModel):
    method: str = Field(description="passive | active-air | liquid")
    description: str = Field(description="Details of the thermal management approach")
    materials: list[str] = Field(description="Thermal interface materials used")


class BOMComponent(BaseModel):
    item_number: int
    component_name: str
    description: str
    quantity: int | str
    specifications: str
    estimated_unit_cost_usd: str = Field(description="Unit cost in USD with $ sign, e.g. '$4.50'")


class DesignChoice(BaseModel):
    topic: str = Field(description="Design area, e.g. 'Cell Selection', 'Pack Topology'")
    decision: str = Field(description="What was chosen")
    rationale: str = Field(description="Why this choice was made")


class DesignVariant(BaseModel):
    variant_name: str = Field(description="One of: 'Cost Optimized', 'Performance Optimized', 'Space Optimized'")
    variant_description: str = Field(description="One-sentence summary of this variant's approach")
    project_summary: str = Field(description="One-paragraph summary of this specific design")
    cell: CellSpec
    pack_configuration: PackConfiguration
    bms: BMSSpec
    cooling: CoolingSpec
    design_choices: list[DesignChoice]
    bom_table: list[BOMComponent]
    total_estimated_cost_usd: str = Field(description="Estimated total BOM cost with $ sign, e.g. '$1,250.00'")
    notes: list[str] = Field(description="Additional engineering notes or caveats")


class MultiDesignResponse(BaseModel):
    reasoning_steps: list[ReasoningStep] = Field(description="Exactly 6 steps showing the AI's analysis process")
    designs: list[DesignVariant] = Field(description="Exactly 3 design variants")


# ── Data loading ──────────────────────────────────────────────────────────────

DB_PATH = os.path.join(os.path.dirname(__file__), "Cell_database.csv")

# Columns to include in the LLM context (most useful for design decisions)
CSV_COLUMNS = [
    "id", "company name", "chemistry_detail", "chemistry", "format", "part",
    "cell status", "cell shape", "cycle_life", "capacity_nom", "v_max", "v_nom",
    "v_min", "i_cont", "i_peak", "weight (gr)", "volume (cc)",
    "length (mm)", "height (mm)", "width_(mm)", "diameter_(mm)",
    "r_internal", "op_temp_discharge_min_c", "t_max",
]


def load_component_data() -> str:
    """Load the CSV cell database and return a text summary for the LLM."""
    if not os.path.exists(DB_PATH):
        return (
            "[No local component database available. "
            "Use your training knowledge to select appropriate real-world components with REAL part numbers. "
            "For cells: Samsung SDI (INR21700-50E, INR18650-30Q), LG Chem (INR21700-M50T, INR18650-MJ1), "
            "CATL, EVE Energy (LF280K, LF304), Molicel (P42A, P45B), Panasonic (NCR18650GA, NCR21700A), BAK, CALB. "
            "For BMS ICs: Texas Instruments (BQ76952, BQ76942, BQ76940), Analog Devices (ADBMS1818, LTC6813), "
            "NXP (MC33771C), STMicroelectronics (L9961). "
            "For connectors, fuses, contactors, and enclosures: use real parts from TE Connectivity, Amphenol, Littelfuse, etc.]"
        )

    try:
        df = pd.read_csv(DB_PATH)
        # Keep only useful columns that exist
        cols = [c for c in CSV_COLUMNS if c in df.columns]
        df = df[cols].dropna(how="all")
        return f"--- AEDI Cell Database ({len(df)} cells) ---\n{df.to_string(index=False)}"
    except Exception as e:
        return f"[Error reading database: {e}. Fall back to training knowledge.]"


# ── Request model ─────────────────────────────────────────────────────────────

class GenerateBOMRequest(BaseModel):
    query: str = Field(description="User's design requirements in natural language")


# ── Endpoint ──────────────────────────────────────────────────────────────────

RESPONSE_SCHEMA = json.dumps(MultiDesignResponse.model_json_schema(), indent=2)

SYSTEM_PROMPT = f"""\
You are AEDI's Battery Pack Design Engineer AI specializing in 2-wheeler and light electric vehicle (LEV) applications. \
Given user requirements, generate a complete, physically feasible battery pack design analysis with multiple optimized variants.

## APPLICATION DOMAIN: 2-Wheelers & Light EVs
All designs MUST comply with these real-world 2-wheeler / LEV constraints:

### Cell Constraints
- Individual cell capacity MUST NOT exceed 100 Ah. For 2-wheelers, typical cells are 2.5–50 Ah range.
- Preferred form factors: 18650 cylindrical (2.5–3.5 Ah), 21700 cylindrical (4–5 Ah), small pouch cells (5–50 Ah), small prismatic cells (10–50 Ah).
- Do NOT use large prismatic cells (e.g. EVE LF280K 280Ah, CATL 302Ah) — these are for ESS/EV cars, NOT 2-wheelers.
- Typical chemistries for 2-wheelers: NMC811, NMC622, NCA (high energy density), LFP (cost/safety).

### MANDATORY S×P Calculation & Validation
You MUST follow this exact calculation sequence for EVERY design variant. Any mismatch is a critical error.

**Step 1: Determine Series Count (S) from target voltage**
  S = Target_Pack_Voltage / Cell_Nominal_Voltage
  - For NMC/NCA cells (3.6V nom): 48V → 13S, 60V → 17S, 72V → 20S
  - For LFP cells (3.2V nom): 48V → 16S, 60V → 19S, 72V → 24S
  - Pack_Nominal_Voltage = S × Cell_Nominal_Voltage (MUST match target ±5%)

**Step 2: Determine Parallel Count (P) from target energy**
  Required_Pack_Capacity_Ah = Target_Energy_Wh / Pack_Nominal_Voltage
  P = ceil(Required_Pack_Capacity_Ah / Cell_Capacity_Ah)
  - Pack_Capacity_Ah = P × Cell_Capacity_Ah
  - Pack_Energy_Wh = Pack_Nominal_Voltage × Pack_Capacity_Ah (MUST be within ±10% of target)

**Step 3: Total cells and weight**
  Total_Cells = S × P
  Cell_Weight_kg = Total_Cells × Cell_Weight_g / 1000
  BMS_Enclosure_Overhead = Cell_Weight_kg × 0.25 to 0.35 (25-35% overhead for BMS, nickel strips, enclosure, wiring)
  Estimated_Pack_Weight = Cell_Weight_kg + BMS_Enclosure_Overhead
  - MUST be within user's weight limit

**Step 4: Validate discharge C-rates**
  I_continuous = P_nominal_W / Pack_Nominal_Voltage
  I_per_cell_continuous = I_continuous / P
  C_rate_continuous = I_per_cell_continuous / Cell_Capacity_Ah
  - Continuous C-rate MUST be ≤ 1.5C for longevity (ideally ≤ 1C)
  I_peak = P_peak_W / Pack_Nominal_Voltage
  I_per_cell_peak = I_peak / P
  C_rate_peak = I_per_cell_peak / Cell_Capacity_Ah
  - Peak C-rate MUST be ≤ 3C for brief surges (≤5 seconds)
  - If C-rates exceed limits, INCREASE P (add more parallel strings)

**Step 5: Cross-check all values**
  - total_cells in JSON = series_count × parallel_count (EXACT)
  - nominal_voltage_v in pack_configuration = series_count × cell nominal_voltage_v (EXACT)
  - total_capacity_ah = parallel_count × cell capacity_ah (EXACT)
  - total_energy_wh = nominal_voltage_v × total_capacity_ah (EXACT)
  - estimated_pack_weight_kg = (total_cells × cell weight_g / 1000) + overhead

EXAMPLE: 72V pack, 4.0 kWh target, 4.0 kW nominal, 8.5 kW peak, <20 kg
  Cell: Samsung INR21700-50G (5.0 Ah, 3.6V nom, 70g)
  S = 72 / 3.6 = 20 → 20S
  Pack_Voltage = 20 × 3.6 = 72.0V ✓
  Required Ah = 4000 / 72 = 55.6 Ah → P = ceil(55.6 / 5.0) = 12P (but check C-rate first)
  I_continuous = 4000 / 72 = 55.6A → per cell = 55.6 / 12 = 4.6A → C-rate = 4.6/5.0 = 0.93C ✓
  I_peak = 8500 / 72 = 118.1A → per cell = 118.1 / 12 = 9.8A → C-rate = 9.8/5.0 = 1.97C ✓
  Total cells = 20 × 12 = 240, Weight = 240 × 70g = 16.8 kg, + overhead ~4 kg → ~20.8 kg (borderline)
  → Try 11P: Capacity = 55 Ah, Energy = 3960 Wh (within 1% of 4kWh ✓)
  I_cont per cell = 55.6/11 = 5.05A → C = 1.01C ✓, I_peak per cell = 118.1/11 = 10.7A → C = 2.15C ✓
  Total cells = 220, Weight = 220 × 70g = 15.4 kg + ~4.0 kg overhead = 19.4 kg ✓ (under 20 kg)
  Final: 20S11P, 220 cells, 72V, 55Ah, 3960Wh, 19.4 kg ✓

### Pack Design Rules for 2-Wheelers
- Total pack weight must be realistic for the vehicle class:
  - E-bike / delivery scooter: 5–12 kg
  - E-scooter (high-speed): 12–25 kg
  - E-motorcycle (heavy-duty): 25–40 kg
- Pack voltage ranges: 36V, 48V, 60V, or 72V nominal (matching common 2-wheeler motor controllers).
- Pack must fit within typical under-seat or floor-mount dimensions for the vehicle class.
- Include proper fusing, pre-charge circuit, and contactor/relay for safety.
- For swappable packs: must include handle, quick-disconnect connector, and compact form factor.

### BMS Rules for 2-Wheelers
- BMS must support the EXACT series count used in the design.
- For >16S configurations (e.g. 20S for 72V NMC), use stackable/daisy-chainable BMS ICs or a single IC that supports the count.
  - TI BQ76952: 3–16S (for ≤16S designs)
  - TI BQ76942: 3–10S (for small packs)
  - Analog Devices ADBMS1818: up to 18S (can daisy-chain for more)
  - Analog Devices LTC6813: up to 18S (stackable)
  - NXP MC33771C: 7–14S
  - For 20S+: use 2× stacked BQ76952, or ADBMS1818 daisy-chain, or dedicated 20S+ solutions.
- Communication: CAN bus for motorcycles/high-speed scooters; UART for delivery/light scooters; I2C for e-bikes.
- Must include: OVP (4.20V/cell NMC, 3.65V/cell LFP), UVP (2.75V/cell NMC, 2.50V/cell LFP), OCP, SCP, OTP.
- Cell balancing is required (passive for cost, active for performance).
- Specify exact protection thresholds in the design.

### Thermal Management for 2-Wheelers
- Passive cooling (thermal pads + aluminum heatsink/enclosure) for e-bikes, delivery scooters, and low-power scooters.
- Forced air cooling (12V blower fan + aluminum heatsink fins) for high-power scooters and motorcycles.
- Liquid cooling is RARE — only for racing/high-performance motorcycles.
- Cell spacing: minimum 2–3 mm air gap between cylindrical cells for passive thermal dissipation.
- Honeycomb/hexagonal packing for cylindrical cells maximizes volumetric efficiency with airflow channels.
- Operating temperature: -10°C to +55°C ambient (Indian/tropical climate consideration).
- Thermal cut-off: 60°C pack temperature to disable discharge.

### Indian Market Considerations
- Designs should consider component availability in the Indian market.
- Must comply with AIS-156 (Amendment 3) battery safety standards.
- UN 38.3 transportation safety testing required.
- IP rating: minimum IP65 for the enclosure (dust & water splash protection).
- Include appropriate connectors: Anderson SB series or XT90 for power; JST/Molex for signal.
- Nickel strip interconnects: pure nickel 0.15mm × 8mm minimum for 2-wheeler current levels.

Your response has TWO parts:

## PART 1: Reasoning Steps
Produce exactly 6 reasoning steps that show your analysis process. Use EXACTLY these titles in order:
1. step_number: 1, title: "Parsing Requirements" — Analyze the user's voltage, energy, weight, and application constraints.
2. step_number: 2, title: "Applying Knowledge Model" — Setting up constraints and applying AEDI Algorithm.
3. step_number: 3, title: "Exploring Design Space" — Evaluate multiple cell chemistries, form factors, and S/P configurations.
4. step_number: 4, title: "Selecting BMS & Thermal Architecture" — Choose BMS ICs and thermal management strategies for each variant.
5. step_number: 5, title: "Generating Optimal Designs" — Finalize 3 optimized design variants with complete specifications.
6. step_number: 6, title: "Estimating Component Costs" — Researching current market pricing for all BOM components.

Each step must have a 1-2 sentence description explaining what was analyzed or decided.

## PART 2: Three Design Variants
Generate exactly 3 complete battery pack designs, each optimized differently:

1. **Cost Optimized** — CHEAPEST feasible design. Use LFP cells or budget NMC/NCA 18650 format. Simplest BMS IC with passive balancing. Passive cooling. Basic sheet metal/ABS enclosure. This MUST have the lowest total cost.
2. **Performance Optimized** — Maximize power delivery, energy density, and cycle life. Use premium NMC811/NCA 21700 cells (e.g. Molicel P42A/P45B, Samsung 50E/50G). Advanced BMS with active balancing and CAN bus. Forced air or enhanced passive cooling. Higher cost acceptable.
3. **Space Optimized** — Minimize volume and weight for portability/swapping. Use highest energy-density cells available (high-cap 21700 or pouch). Compact BMS. Lightweight aluminum enclosure. Premium pricing acceptable.

IMPORTANT COST ORDERING: Cost Optimized < Performance Optimized AND Cost Optimized < Space Optimized.

## CRITICAL: Cost Estimation Rules
You MUST provide accurate cost estimates in US Dollars for EVERY BOM component.
- Format: "$4.50", "$12.00", "$0.85" (always with $ prefix)
- estimated_unit_cost_usd: cost per single unit
- total_estimated_cost_usd: sum of (unit_cost × quantity) for ALL BOM items
- Realistic 2024-2025 market pricing:
  - 18650 cells: $1.50–$4.00/cell (LFP $1.50–2.50, NMC $2.50–4.00)
  - 21700 cells: $3.00–$7.00/cell (budget $3–4, premium $5–7)
  - Pouch cells (5–50 Ah): NMC $0.10–0.15/Wh, LFP $0.06–0.10/Wh
  - BMS ICs: $5–$25
  - Nickel strips (pure nickel, 1 meter): $1–$3
  - Cell holders (per cell): $0.05–$0.15
  - Fuses (automotive blade): $0.50–$3
  - Pre-charge resistors: $0.50–$2
  - Contactors/relays (EV grade): $8–$35
  - Connectors (XT90/Anderson): $2–$8
  - Enclosures (sheet metal/ABS): $15–$60
  - PCB fabrication: $8–$30
  - Thermal pads: $2–$10
  - Wire harness (silicone, 10-12 AWG): $5–$15
  - 12V cooling fan (if forced air): $3–$8
- NEVER leave cost fields empty or null.

## Cell Selection Rules
- PREFER cells from the provided AEDI Cell Database when they match requirements.
- Use exact "part" and "company name" from the database.
- CRITICAL: Only cells with capacity ≤ 100 Ah. Cylindrical cells: 2.5–5 Ah per cell.
- Fallback real cells: Samsung SDI (INR21700-50E/50G, INR18650-30Q), LG Chem (INR21700-M50T, INR18650-MJ1), Molicel (P42A, P45B), Panasonic (NCR18650GA, NCR21700A), BAK, Lishen, Gotion.
- For LFP cylindrical: EVE (LF50F 18650), Headway (38120S, 40152S), CALB small-format.

## General Rules
1. Select REAL components with exact manufacturer names and part numbers.
2. ALL math must be self-consistent: V × Ah = Wh, S × P = total_cells, S × Vcell = Vpack, P × Ccell = Ah_pack.
3. The S×P configuration must achieve voltage AND energy targets within tolerance.
4. BMS IC must support the exact series count. If >16S, specify stacking/daisy-chain approach.
5. BOM must include: cells, nickel strips/busbars, cell holders, BMS IC + PCB, fuse, pre-charge circuit, contactor/relay, connectors (power + signal), enclosure, thermal pads, wire harness.
6. Be specific with part numbers — no placeholders or generic names.
7. Return ONLY valid JSON. No markdown, no explanation outside JSON.
8. Mention safety standards (AIS-156 Amendment 3, UN 38.3, IEC 62133-2) in notes.
9. Include BMS protection thresholds (OVP, UVP, OCP values) in the bms specification.

## Required JSON Schema
{RESPONSE_SCHEMA}

CRITICAL: Your response must have exactly these top-level keys: "reasoning_steps", "designs". The "designs" array must contain exactly 3 items with variant_name values: "Cost Optimized", "Performance Optimized", "Space Optimized".
"""


# ── Streaming endpoint ────────────────────────────────────────────────────────

# Predefined reasoning steps sent to frontend while the LLM works
STREAMING_STEPS = [
    {"step_number": 1, "title": "Parsing Requirements", "description": "Analyzing voltage, energy, weight, and application constraints from your query..."},
    {"step_number": 2, "title": "Applying Knowledge Model", "description": "Setting up constraints and applying AEDI Algorithm..."},
    {"step_number": 3, "title": "Exploring Design Space", "description": "Evaluating cell chemistries, form factors, and series-parallel configurations..."},
    {"step_number": 4, "title": "Selecting BMS & Thermal Architecture", "description": "Matching BMS ICs and cooling strategies to each design variant..."},
    {"step_number": 5, "title": "Generating Optimal Designs", "description": "Finalizing 3 optimized variants — Cost, Performance, and Space..."},
    {"step_number": 6, "title": "Estimating Component Costs", "description": "Researching current market pricing for all BOM components..."},
]


MAX_COMPLETION_TOKENS = 4500


def build_user_message(query: str) -> str:
    component_data = load_component_data()
    return (
        f"## User Requirements\n{query}\n\n"
        f"## Component Database\n{component_data}\n\n"
        "## Pricing Guidance\n"
        "Use the pricing ranges already provided in the system prompt and your built-in market knowledge. "
        "Do not wait for any external web search."
    )


def generate_bom_result(query: str) -> MultiDesignResponse:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_message(query)},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
        max_tokens=MAX_COMPLETION_TOKENS,
    )

    raw = response.choices[0].message.content
    if not raw:
        raise HTTPException(status_code=502, detail="LLM returned empty response.")

    parsed = json.loads(raw)
    return MultiDesignResponse(**parsed)


@app.post("/api/generate-bom-stream")
async def generate_bom_stream(request: GenerateBOMRequest):
    """Stream reasoning steps as SSE events, then the final design result."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    async def event_stream():
        for step in STREAMING_STEPS:
            yield f"data: {json.dumps({'type': 'step', 'step': step})}\n\n"
            await asyncio.sleep(0)

        try:
            result = generate_bom_result(request.query)
            yield f"data: {json.dumps({'type': 'result', 'data': result.model_dump()})}\n\n"
        except json.JSONDecodeError as e:
            yield f"data: {json.dumps({'type': 'error', 'detail': f'LLM returned invalid JSON: {e}'})}\n\n"
        except HTTPException as e:
            yield f"data: {json.dumps({'type': 'error', 'detail': e.detail})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'detail': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ── Original non-streaming endpoint (kept for compatibility) ──────────────────

@app.post("/api/generate-bom", response_model=MultiDesignResponse)
async def generate_bom(request: GenerateBOMRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        return generate_bom_result(request.query)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=502, detail=f"LLM returned invalid JSON: {e}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}
