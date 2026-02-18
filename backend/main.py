import os
import json
from typing import Optional

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv(override=True)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="AEDI BOM Generator", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── OpenAI client ─────────────────────────────────────────────────────────────
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── Pydantic models ──────────────────────────────────────────────────────────


class ReasoningStep(BaseModel):
    step_number: int = Field(description="Sequential step number starting from 1")
    title: str = Field(description="Short title, e.g. 'Analyzing Voltage Requirements'")
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
    estimated_unit_cost_usd: Optional[str] = None


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
    total_estimated_cost_usd: Optional[str] = Field(None, description="Estimated total BOM cost")
    notes: list[str] = Field(description="Additional engineering notes or caveats")


class MultiDesignResponse(BaseModel):
    reasoning_steps: list[ReasoningStep] = Field(description="4-6 steps showing the AI's analysis process")
    designs: list[DesignVariant] = Field(description="Exactly 3 design variants")


# ── Data loading ──────────────────────────────────────────────────────────────

DB_PATH = os.path.join(os.path.dirname(__file__), "components_database.xlsx")


def load_component_data() -> str:
    """Load the Excel database and return a text summary for the LLM."""
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
        xls = pd.ExcelFile(DB_PATH)
        summaries: list[str] = []
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            summaries.append(f"--- Sheet: {sheet} ---\n{df.to_string(index=False)}")
        return "\n\n".join(summaries)
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
Produce 4-6 reasoning steps that show your analysis process. Each step should have:
- step_number (sequential from 1)
- title (short, e.g. "Analyzing Voltage Requirements")
- description (1-2 sentences of what you analyzed or decided)

These steps should cover: requirement parsing, cell chemistry selection, S/P configuration calculation, BMS IC selection, thermal analysis, and trade-off considerations.

## PART 2: Three Design Variants
Generate exactly 3 complete battery pack designs, each optimized differently:

1. **Cost Optimized** — Minimize total BOM cost. Use budget-friendly cells (e.g. LFP chemistry, standard cylindrical), simpler BMS, passive cooling where possible.
2. **Performance Optimized** — Maximize power delivery and energy density. Use high-discharge cells (e.g. NMC/NCA, Molicel P42A), advanced BMS with active balancing, robust thermal management.
3. **Space Optimized** — Minimize physical volume and weight. Use high energy-density cells (e.g. pouch or high-capacity 21700), compact BMS, lightweight materials.

Each variant must be a complete, physically feasible design with real components.

## Rules
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
