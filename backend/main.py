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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
You are AEDI's Battery Pack Design Engineer AI. Given user requirements, \
generate a complete, physically feasible battery pack design analysis with multiple optimized variants.

Your response has TWO parts:

## PART 1: Reasoning Steps
Produce exactly 6 reasoning steps that show your analysis process. Use EXACTLY these titles in order:
1. step_number: 1, title: "Parsing Requirements" — Analyze the user's voltage, energy, weight, and application constraints.
2. step_number: 2, title: "Applying Knowledge Model" — Setting up constraints and applying AEDI Algorithm.
3. step_number: 3, title: "Exploring Design Space" — Evaluate multiple cell chemistries, form factors, and S/P configurations.
4. step_number: 4, title: "Selecting BMS & Thermal Architecture" — Choose BMS ICs and thermal management strategies for each variant.
5. step_number: 5, title: "Generating Optimal Designs" — Finalize 3 optimized design variants with complete specifications.
6. step_number: 6, title: "Estimating Component Costs"

Each step must have a 1-2 sentence description explaining what was analyzed or decided.

## PART 2: Three Design Variants
Generate exactly 3 complete battery pack designs, each optimized differently:

1. **Cost Optimized** — The CHEAPEST possible design. Minimize total BOM cost above all else. Use the lowest-cost cells available (e.g. LFP chemistry, standard 18650), the simplest BMS IC, passive cooling only, basic enclosure. This variant MUST have the lowest total_estimated_cost_usd of all 3 variants.
2. **Performance Optimized** — Maximize power delivery and energy density. Use high-discharge cells (e.g. NMC/NCA, Molicel P42A), advanced BMS with active balancing, robust thermal management. Higher cost is acceptable.
3. **Space Optimized** — Minimize physical volume and weight. Use high energy-density cells (e.g. pouch or high-capacity 21700), compact BMS, lightweight materials. Premium pricing is acceptable for weight/size savings.

Each variant must be a complete, physically feasible design with real components.

IMPORTANT COST ORDERING CONSTRAINT: The total_estimated_cost_usd MUST follow this order:
  Cost Optimized < Performance Optimized AND Cost Optimized < Space Optimized.
  The Cost Optimized variant must ALWAYS be the cheapest. If your calculations show otherwise, revise your component selections until Cost Optimized is the least expensive.

## CRITICAL: Cost Estimation Rules
You MUST provide accurate cost estimates in US Dollars for EVERY component in the BOM table.
- Format all costs with a dollar sign prefix: "$4.50", "$12.00", "$0.85"
- estimated_unit_cost_usd: Cost per single unit of that component (e.g. "$3.50" per cell)
- total_estimated_cost_usd: Sum of (unit_cost × quantity) for all BOM items, formatted as "$1,250.00"
- Use realistic 2024-2025 market pricing:
  - Cylindrical cells (18650/21700): $2-$8 per cell depending on chemistry and brand
  - Pouch/prismatic cells: scale by capacity, roughly $0.10-$0.15/Wh for NMC, $0.06-$0.10/Wh for LFP
  - BMS ICs: $5-$30 depending on complexity
  - Passive components (resistors, capacitors, fuses): $0.10-$2.00
  - Connectors (Anderson, XT60/90): $1-$8
  - Contactors/relays: $15-$50
  - Enclosures: $20-$100+
  - PCB fabrication: $10-$50
  - Thermal pads/materials: $2-$15
  - Wire harness: $5-$20
- NEVER leave estimated_unit_cost_usd empty or null. Always provide a dollar value.

## Cell Selection Rules
- You are provided an AEDI Cell Database with real cell specifications. PREFER cells from this database when they match requirements.
- When selecting cells from the database, use the exact "part" and "company name" values.
- If no database cell fits, use well-known cells from: Samsung SDI, LG Chem, CATL, EVE Energy, Molicel, Panasonic, BAK, CALB.

## General Rules
1. Select REAL components with exact manufacturer names and part numbers.
2. All calculations must be physically consistent (voltage, capacity, weight, energy).
3. The pack configuration (S/P) must achieve the required voltage and energy targets.
4. Select a real BMS IC that supports the required number of series cells.
5. The BOM table must list every major component needed to build the pack.
6. Be specific with part numbers — no placeholders.
7. Return ONLY valid JSON. No markdown, no explanation outside JSON.
8. Your JSON response MUST use EXACTLY the structure shown in the schema below.

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


@app.post("/api/generate-bom-stream")
async def generate_bom_stream(request: GenerateBOMRequest):
    """Stream reasoning steps as SSE events, then the final design result."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    import asyncio

    async def event_stream():
        # Send reasoning steps progressively
        for step in STREAMING_STEPS:
            yield f"data: {json.dumps({'type': 'step', 'step': step})}\n\n"
            await asyncio.sleep(3)

        # Now call the LLM
        component_data = load_component_data()
        user_message = (
            f"## User Requirements\n{request.query}\n\n"
            f"## Component Database\n{component_data}"
        )

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=10000,
            )

            raw = response.choices[0].message.content
            if not raw:
                yield f"data: {json.dumps({'type': 'error', 'detail': 'LLM returned empty response.'})}\n\n"
                return

            parsed = json.loads(raw)
            result = MultiDesignResponse(**parsed)
            yield f"data: {json.dumps({'type': 'result', 'data': result.model_dump()})}\n\n"

        except json.JSONDecodeError as e:
            yield f"data: {json.dumps({'type': 'error', 'detail': f'LLM returned invalid JSON: {e}'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'detail': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ── Original non-streaming endpoint (kept for compatibility) ──────────────────

@app.post("/api/generate-bom", response_model=MultiDesignResponse)
async def generate_bom(request: GenerateBOMRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    component_data = load_component_data()

    user_message = (
        f"## User Requirements\n{request.query}\n\n"
        f"## Component Database\n{component_data}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=10000,
        )

        raw = response.choices[0].message.content
        if not raw:
            raise HTTPException(status_code=502, detail="LLM returned empty response.")

        parsed = json.loads(raw)
        result = MultiDesignResponse(**parsed)
        return result

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=502, detail=f"LLM returned invalid JSON: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}
