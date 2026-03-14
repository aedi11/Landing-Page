# AEDI Battery Pack Configuration Pipeline — Complete Setup & Run Guide

> **What is this?** An 11-step AI-powered pipeline that takes a natural language query like  
> _"Design a 48V 2kWh battery pack for an electric scooter, max 12kg"_  
> and outputs a ranked list of battery pack designs with BMS recommendations, thermal analysis, and a professional technical report.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Project Structure](#2-project-structure)
3. [Environment Setup](#3-environment-setup)
4. [Database Setup (Supabase)](#4-database-setup-supabase)
5. [Upload Data](#5-upload-data)
6. [Generate Fallback Defaults](#6-generate-fallback-defaults)
7. [Run the Pipeline Server](#7-run-the-pipeline-server)
8. [Test the Pipeline](#8-test-the-pipeline)
9. [n8n Workflow Setup (Optional)](#9-n8n-workflow-setup-optional)
10. [Deploy to Production](#10-deploy-to-production)
11. [Pipeline Deep Dive — What Each Step Does](#11-pipeline-deep-dive--what-each-step-does)
12. [API Endpoints Reference](#12-api-endpoints-reference)
13. [Architecture & Design Decisions](#13-architecture--design-decisions)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. Prerequisites

Before you start, make sure you have:

| Requirement                             | Details                                                                                           |
| --------------------------------------- | ------------------------------------------------------------------------------------------------- |
| **Python 3.10+**                        | Verify with `python --version`                                                                    |
| **pip**                                 | Comes with Python                                                                                 |
| **Supabase project**                    | Free tier at [supabase.com](https://supabase.com) — you need the **URL** and **service role key** |
| **OpenAI API key**                      | From [platform.openai.com](https://platform.openai.com) — used for LLM calls and embeddings       |
| **Cell database Excel file**            | `cell-database.xlsx` placed inside `sql/` folder                                                  |
| **Design rule JSON files** _(optional)_ | `electrical_rules.json`, `thermal_rules.json`, `mechanical_rules.json` in `sql/`                  |
| **n8n Cloud** _(optional)_              | Only if you want workflow orchestration                                                           |

---

## 2. Project Structure

```
backend/
├── main.py                            # Existing BOM generator (UNTOUCHED)
├── .env                               # Environment variables (shared)
│
├── AEDI_workflow/                     # ←── THIS PIPELINE (11 steps)
│   ├── INSTRUCTIONS.md                # This file
│   ├── __init__.py
│   ├── config.py                      # Loads .env, creates Supabase + LangChain clients
│   ├── defaults.py                    # 7-level hierarchical fallback defaults
│   ├── cell_defaults.json             # Auto-generated lookup table (from Step 6)
│   ├── requirements.txt               # Python dependencies
│   │
│   ├── models/                        # Pydantic models (strict typing)
│   │   ├── __init__.py
│   │   ├── requirements.py            # UserRequirements, ParsedRequirements
│   │   ├── rules.py                   # VoltageRule, CurrentRule, DesignRules
│   │   ├── candidates.py              # CellCandidate, PackCandidate, ValidatedCandidate, ExpandedVariant
│   │   ├── thermal.py                 # ThermalResult, CoolingStrategy
│   │   └── output.py                  # RankedCandidate, CandidateReport, FinalReport, BMSRecommendation
│   │
│   ├── services/                      # Pipeline step implementations (one file per step)
│   │   ├── __init__.py
│   │   ├── step01_requirements_parser.py    # LLM → structured output
│   │   ├── step02_rule_query_engine.py      # RAG (pgvector) + LLM fallback
│   │   ├── step03_pack_sizer.py             # Pure deterministic S/P math
│   │   ├── step04_validation.py             # TopologyRegulator + CurrentRegulator
│   │   ├── step05_expansion_manager.py      # SOC window (LLM) + P expansion
│   │   ├── step06_thermal_feasibility.py    # Physics-based thermal filter
│   │   ├── step07_preliminary_ranker.py     # Weighted scoring → Top 4
│   │   ├── step08_cad_generation.py         # Mock CAD (placeholder for future)
│   │   ├── step09_thermal_simulation.py     # Analytical I²R + T_max estimation
│   │   ├── step10_final_ranker.py           # Re-rank with thermal simulation data
│   │   └── step11_answer_generator.py       # LLM technical report generation
│   │
│   ├── api/                           # FastAPI application
│   │   ├── __init__.py
│   │   └── app.py                     # All endpoints + full pipeline runner
│   │
│   ├── sql/                           # Database schemas & data upload scripts
│   │   ├── sql_queries/
│   │   │   ├── 01_cells_table.sql     # Cells table schema
│   │   │   └── 02_design_rules_table.sql  # Rules table + pgvector + RPC functions
│   │   ├── upload_cells.py            # Upload Excel → Supabase cells table
│   │   ├── upload_rules.py            # Upload JSON rules → Supabase with embeddings
│   │   ├── generate_defaults.py       # Compute group medians → cell_defaults.json
│   │   ├── important_information.md   # Column mapping, units, fallback system docs
│   │   ├── cell-database.xlsx         # Source cell database
│   │   ├── electrical_rules.json      # Electrical design rules (optional)
│   │   ├── thermal_rules.json         # Thermal design rules (optional)
│   │   └── mechanical_rules.json      # Mechanical design rules (optional)
│   │
│   └── n8n/                           # n8n workflow integration (optional)
│       ├── workflow_architecture.md   # Architecture docs
│       └── workflow_template.json     # Importable n8n workflow JSON
```

---

## 3. Environment Setup

### Step 3.1 — Install Python dependencies

```bash
cd backend/AEDI_workflow
pip install -r requirements.txt
```

This installs: `fastapi`, `uvicorn`, `pydantic`, `python-dotenv`, `supabase`, `langchain`, `langchain-openai`, `openai`, `httpx`

### Step 3.2 — Install data upload dependencies (one-time)

```bash
pip install openpyxl pandas
```

These are needed only for the upload scripts (`upload_cells.py`, `generate_defaults.py`).

### Step 3.3 — Create/verify the `.env` file

The `.env` file must be located at **`backend/.env`** (the parent of `AEDI_workflow/`).

Create it with the following variables:

```env
# Required — Pipeline will not start without these
OPENAI_API_KEY=sk-proj-your-key-here
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-service-role-key

# Optional — Defaults shown
OPENAI_MODEL=gpt-4o-mini
n8n_cloud_key=https://aedi.app.n8n.cloud
```

> **⚠️ Important:** `config.py` loads the `.env` from `../` relative to the `AEDI_workflow/` folder. Make sure it's at `backend/.env`, **not** inside `AEDI_workflow/`.

---

## 4. Database Setup (Supabase)

You need to create two tables in your Supabase project. Do this via the **Supabase Dashboard SQL Editor**.

### Step 4.1 — Create the `cells` table

1. Go to your [Supabase Dashboard](https://supabase.com/dashboard)
2. Open your project → Click **SQL Editor** in the left sidebar
3. Click **New Query**
4. Open the file `sql/sql_queries/01_cells_table.sql`, copy its **entire contents**
5. Paste into the SQL Editor and click **Run**

This creates:

- `cells` table with 50+ columns matching the Excel cell database
- Indexes on `chemistry`, `format`, `capacity`, `voltage`, `manufacturer`, `energy`, `wh_per_kg`
- A unique constraint on `(manufacturer, cell_name)` for safe re-uploads

### Step 4.2 — Create the `design_rules` table

1. Still in the SQL Editor, click **New Query**
2. Open the file `sql/sql_queries/02_design_rules_table.sql`, copy its **entire contents**
3. Paste and click **Run**

This creates:

- `design_rules` table with flat columns + pgvector `embedding` column (1536 dims)
- Enables the `vector` extension (pgvector)
- `match_design_rules()` RPC function for semantic similarity search (with filters)
- `get_rules_by_filter()` RPC function for exact-match queries (no embedding needed)
- HNSW index on the embedding column for fast cosine similarity search

> **Run these SQL files in order:** `01_cells_table.sql` first, then `02_design_rules_table.sql`.

---

## 5. Upload Data

### Step 5.1 — Upload cell database from Excel

Make sure your Excel file (`cell-database.xlsx`) is placed in the `sql/` folder.

```bash
cd backend/AEDI_workflow/sql
python upload_cells.py
```

**What this does:**

- Reads the Excel file and auto-detects the correct sheet and header row
- Normalizes column names (lowercase, underscores) and maps them to the Supabase schema via `COLUMN_MAP`
- Uploads in batches of 50 using upsert (safe to re-run — won't create duplicates)
- Handles missing/null values gracefully
- Prints a column mapping summary so you can verify matches
- Falls back to row-by-row insertion if a batch fails

**If columns don't match:** Edit the `COLUMN_MAP` dictionary in `upload_cells.py` to add your Excel's column name variants.

### Step 5.2 — Upload design rules with embeddings

Make sure your rule JSON files (`electrical_rules.json`, `thermal_rules.json`, `mechanical_rules.json`) are in the `sql/` folder.

```bash
cd backend/AEDI_workflow/sql
python upload_rules.py
```

**What this does:**

- Auto-checks that the `design_rules` table exists (gives clear instructions if not)
- Loads rules from all 3 JSON files
- Generates OpenAI embeddings (`text-embedding-3-small`) for each rule
- Builds rich embedding text combining: `[rule_type] [severity] [applies_to] Parameter: ... constraint_text`
- Uploads to Supabase in batches of 20 with embeddings included
- Prints per-type summary (Electrical, Thermal, Mechanical counts)

> **Cost:** Embedding generation costs approximately **$0.01** for ~200 rules.  
> **Requires:** `OPENAI_API_KEY` in your `backend/.env`

### Expected Rule JSON Format

Each rule JSON file should be an array of objects like:

```json
[
  {
    "rule_type": "Electrical",
    "parameter": "voltage",
    "constraint_expr": "Pack voltage must be within ±5% of target for safe BMS operation",
    "severity": "Critical",
    "applies_to": "Pack",
    "min_value": null,
    "max_value": null,
    "nominal_value": 48.0,
    "unit": "V",
    "source": "Li-Ion Battery Pack Design Handbook"
  }
]
```

---

## 6. Generate Fallback Defaults

This step computes group median values from your uploaded cell data so the pipeline can **estimate missing cell values** (mass, resistance, volume, etc.) instead of using a single hardcoded default.

```bash
cd backend/AEDI_workflow/sql
python generate_defaults.py
```

**What this does:**

- Queries all cells from Supabase
- Groups cells by: chemistry, format, manufacturer, chemistry+format, manufacturer+chemistry
- Computes median values for 24 numeric fields at each group level
- Writes `cell_defaults.json` to the `AEDI_workflow/` folder (loaded by `defaults.py` at runtime)
- Prints a summary table of medians by chemistry

**Output file:** `AEDI_workflow/cell_defaults.json`

### When to Re-run

Run `python sql/generate_defaults.py` whenever you:

- Add new cells to the database
- Update existing cell data
- Change the Excel file and re-upload

### Fallback Hierarchy

When a cell has a null value (e.g., missing `mass_kg`), the pipeline uses this **7-level hierarchy**:

| Priority | Group Key                | Example                    | Accuracy          |
| -------- | ------------------------ | -------------------------- | ----------------- |
| 1        | manufacturer + chemistry | `Samsung SDI + NMC`        | **Most accurate** |
| 2        | chemistry + format       | `NMC + cylindrical`        | Very good         |
| 3        | chemistry only           | `NMC`                      | Good              |
| 4        | format only              | `cylindrical`              | Moderate          |
| 5        | manufacturer only        | `Samsung SDI`              | Moderate          |
| 6        | global median            | All cells                  | Least accurate    |
| 7        | emergency hardcoded      | Hardcoded in `defaults.py` | Last resort       |

> See `sql/important_information.md` for full details on units, column mapping, and the fallback system.

---

## 7. Run the Pipeline Server

From the `backend/` directory (not `AEDI_workflow/`):

```bash
cd backend
uvicorn AEDI_workflow.api.app:app --host 0.0.0.0 --port 8001 --reload
```

- The server starts on **port 8001**
- The `--reload` flag enables hot-reloading during development
- The existing `main.py` BOM generator runs on its own port — they don't conflict

> **⚠️ Note:** You must run `uvicorn` from the `backend/` directory so that Python can resolve the `AEDI_workflow` package imports correctly.

---

## 8. Test the Pipeline

Once the server is running (from Step 7), you can test its endpoints. We'll provide PowerShell examples first, followed by `curl` for comparison.

### 8.1 — Health Check

Verify the server is up and running.

#### PowerShell

```powershell
Invoke-RestMethod -Uri http://localhost:8001/health
```

#### curl (Git Bash / WSL)

```bash
curl http://localhost:8001/health
```

**Expected response:**

```json
{ "status": "ok", "service": "AEDI Workflow Pipeline", "version": "1.0.0" }
```

### 8.2 — Run the Full 11-Step Pipeline

This endpoint orchestrates all 11 steps in sequence and returns a comprehensive `FinalReport` JSON.

#### PowerShell

```powershell
$body = @{ query = "Design a 48V 2kWh battery pack for an electric scooter, max 12kg" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/pipeline/run -ContentType "application/json" -Body $body
```

#### curl (Git Bash / WSL)

```bash
curl -X POST http://localhost:8001/api/v1/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{"query": "Design a 48V 2kWh battery pack for an electric scooter, max 12kg"}'
```

**Expected output:** A `FinalReport` JSON with:
- Top 3 ranked battery pack designs
- Cell specs, S/P configuration, energy, weight
- BMS IC recommendation
- Thermal simulation results
- Pros/cons for each design
- Standards compliance notes

### 8.3 — Test Individual Steps

You can also test individual steps for debugging or to understand the pipeline's flow. The output of one step often serves as the input for the next.

#### Step 1 — Parse Requirements (`/api/v1/step1/parse-requirements`)

**Input:** Natural language query.
**Output:** `ParsedRequirements` JSON object.

##### PowerShell

```powershell
$body = @{ query = "72V 4kWh electric motorcycle battery, under 25kg, NMC preferred" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step1/parse-requirements -ContentType "application/json" -Body $body
```

##### curl (Git Bash / WSL)

```bash
curl -X POST http://localhost:8001/api/v1/step1/parse-requirements \
  -H "Content-Type: application/json" \
  -d '{"query": "72V 4kWh electric motorcycle battery, under 25kg, NMC preferred"}'
```

#### Step 2 — Query Design Rules (`/api/v1/step2/query-rules`)

**Input:** `ParsedRequirements` JSON (from Step 1).
**Output:** `DesignRules` JSON object.

##### PowerShell

```powershell
# First, get ParsedRequirements from Step 1
$parsedRequirements = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step1/parse-requirements -ContentType "application/json" -Body '{"query": "72V 4kWh electric motorcycle battery, under 25kg, NMC preferred"}'

# Now, use it as input for Step 2
$body = $parsedRequirements | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step2/query-rules -ContentType "application/json" -Body $body
```

##### curl (Git Bash / WSL)

```bash
# This requires you to manually copy the output of Step 1 and paste it here.
# For example, if Step 1 output was:
# {"application_type": "Electric Motorcycle", "target_voltage_v": 72, "target_energy_wh": 4000, ...}
curl -X POST http://localhost:8001/api/v1/step2/query-rules \
  -H "Content-Type: application/json" \
  -d '{"application_type": "Electric Motorcycle", "target_voltage_v": 72, "target_energy_wh": 4000, "max_weight_kg": 25, "preferred_chemistry": "NMC", "target_capacity_ah": 55.56, "confidence": 1.0, "follow_up_questions": []}'
```

#### Step 3 — Pack Sizer (`/api/v1/step3/pack-sizer`)

**Input:** `ParsedRequirements` JSON (from Step 1) and `DesignRules` JSON (from Step 2).
**Output:** `CandidatePacks` JSON object.

##### PowerShell

```powershell
# Get ParsedRequirements (Step 1)
$parsedRequirements = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step1/parse-requirements -ContentType "application/json" -Body '{"query": "72V 4kWh electric motorcycle battery, under 25kg, NMC preferred"}'

# Get DesignRules (Step 2)
$designRules = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step2/query-rules -ContentType "application/json" -Body ($parsedRequirements | ConvertTo-Json)

# Combine inputs for Step 3
$step3Body = @{
    parsed_requirements = $parsedRequirements
    design_rules = $designRules
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step3/pack-sizer -ContentType "application/json" -Body $step3Body
```

#### Step 4 — Validate (`/api/v1/step4/validate`)

**Input:** `CandidatePacks` JSON (from Step 3) and `DesignRules` JSON (from Step 2).
**Output:** `ValidatedPacks` JSON object.

##### PowerShell

```powershell
# Get ParsedRequirements (Step 1)
$parsedRequirements = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step1/parse-requirements -ContentType "application/json" -Body '{"query": "72V 4kWh electric motorcycle battery, under 25kg, NMC preferred"}'

# Get DesignRules (Step 2)
$designRules = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step2/query-rules -ContentType "application/json" -Body ($parsedRequirements | ConvertTo-Json)

# Get CandidatePacks (Step 3)
$step3Body = @{ parsed_requirements = $parsedRequirements; design_rules = $designRules } | ConvertTo-Json
$candidatePacks = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step3/pack-sizer -ContentType "application/json" -Body $step3Body

# Combine inputs for Step 4
$step4Body = @{
    candidate_packs = $candidatePacks
    design_rules = $designRules
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step4/validate -ContentType "application/json" -Body $step4Body
```

#### Step 5 — Expand (`/api/v1/step5/expand`)

**Input:** `ValidatedPacks` JSON (from Step 4) and `ParsedRequirements` JSON (from Step 1).
**Output:** `ExpandedPacks` JSON object.

##### PowerShell

```powershell
# Get ParsedRequirements (Step 1)
$parsedRequirements = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step1/parse-requirements -ContentType "application/json" -Body '{"query": "72V 4kWh electric motorcycle battery, under 25kg, NMC preferred"}'

# Get DesignRules (Step 2)
$designRules = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step2/query-rules -ContentType "application/json" -Body ($parsedRequirements | ConvertTo-Json)

# Get CandidatePacks (Step 3)
$step3Body = @{ parsed_requirements = $parsedRequirements; design_rules = $designRules } | ConvertTo-Json
$candidatePacks = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step3/pack-sizer -ContentType "application/json" -Body $step3Body

# Get ValidatedPacks (Step 4)
$step4Body = @{ candidate_packs = $candidatePacks; design_rules = $designRules } | ConvertTo-Json
$validatedPacks = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step4/validate -ContentType "application/json" -Body $step4Body

# Combine inputs for Step 5
$step5Body = @{
    validated_packs = $validatedPacks
    parsed_requirements = $parsedRequirements
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step5/expand -ContentType "application/json" -Body $step5Body
```

#### Step 6 — Thermal Filter (`/api/v1/step6/thermal-filter`)

**Input:** `ExpandedPacks` JSON (from Step 5).
**Output:** `ThermalFilteredPacks` JSON object.

##### PowerShell

```powershell
# Get ParsedRequirements (Step 1)
$parsedRequirements = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step1/parse-requirements -ContentType "application/json" -Body '{"query": "72V 4kWh electric motorcycle battery, under 25kg, NMC preferred"}'

# Get DesignRules (Step 2)
$designRules = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step2/query-rules -ContentType "application/json" -Body ($parsedRequirements | ConvertTo-Json)

# Get CandidatePacks (Step 3)
$step3Body = @{ parsed_requirements = $parsedRequirements; design_rules = $designRules } | ConvertTo-Json
$candidatePacks = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step3/pack-sizer -ContentType "application/json" -Body $step3Body

# Get ValidatedPacks (Step 4)
$step4Body = @{ candidate_packs = $candidatePacks; design_rules = $designRules } | ConvertTo-Json
$validatedPacks = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step4/validate -ContentType "application/json" -Body $step4Body

# Get ExpandedPacks (Step 5)
$step5Body = @{ validated_packs = $validatedPacks; parsed_requirements = $parsedRequirements } | ConvertTo-Json
$expandedPacks = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step5/expand -ContentType "application/json" -Body $step5Body

# Input for Step 6
$step6Body = @{ expanded_packs = $expandedPacks } | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step6/thermal-filter -ContentType "application/json" -Body $step6Body
```

#### Step 7 — Preliminary Rank (`/api/v1/step7/preliminary-rank`)

**Input:** `ThermalFilteredPacks` JSON (from Step 6) and `ParsedRequirements` JSON (from Step 1).
**Output:** `RankedPacks` JSON object (top N).

##### PowerShell

```powershell
# Get ParsedRequirements (Step 1)
$parsedRequirements = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step1/parse-requirements -ContentType "application/json" -Body '{"query": "72V 4kWh electric motorcycle battery, under 25kg, NMC preferred"}'

# Get DesignRules (Step 2)
$designRules = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step2/query-rules -ContentType "application/json" -Body ($parsedRequirements | ConvertTo-Json)

# Get CandidatePacks (Step 3)
$step3Body = @{ parsed_requirements = $parsedRequirements; design_rules = $designRules } | ConvertTo-Json
$candidatePacks = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step3/pack-sizer -ContentType "application/json" -Body $step3Body

# Get ValidatedPacks (Step 4)
$step4Body = @{ candidate_packs = $candidatePacks; design_rules = $designRules } | ConvertTo-Json
$validatedPacks = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step4/validate -ContentType "application/json" -Body $step4Body

# Get ExpandedPacks (Step 5)
$step5Body = @{ validated_packs = $validatedPacks; parsed_requirements = $parsedRequirements } | ConvertTo-Json
$expandedPacks = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step5/expand -ContentType "application/json" -Body $step5Body

# Get ThermalFilteredPacks (Step 6)
$step6Body = @{ expanded_packs = $expandedPacks } | ConvertTo-Json
$thermalFilteredPacks = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step6/thermal-filter -ContentType "application/json" -Body $step6Body

# Combine inputs for Step 7
$step7Body = @{
    thermal_filtered_packs = $thermalFilteredPacks
    parsed_requirements = $parsedRequirements
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step7/preliminary-rank -ContentType "application/json" -Body $step7Body
```

#### Step 8 — CAD Mock (`/api/v1/step8/cad-mock`)

**Input:** A single `RankedPack` JSON (from Step 7).
**Output:** `CADMockResult` JSON object.

##### PowerShell

```powershell
# Get ParsedRequirements (Step 1)
$parsedRequirements = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step1/parse-requirements -ContentType "application/json" -Body '{"query": "72V 4kWh electric motorcycle battery, under 25kg, NMC preferred"}'

# Get DesignRules (Step 2)
$designRules = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step2/query-rules -ContentType "application/json" -Body ($parsedRequirements | ConvertTo-Json)

# Get CandidatePacks (Step 3)
$step3Body = @{ parsed_requirements = $parsedRequirements; design_rules = $designRules } | ConvertTo-Json
$candidatePacks = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step3/pack-sizer -ContentType "application/json" -Body $step3Body

# Get ValidatedPacks (Step 4)
$step4Body = @{ candidate_packs = $candidatePacks; design_rules = $designRules } | ConvertTo-Json
$validatedPacks = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step4/validate -ContentType "application/json" -Body $step4Body

# Get ExpandedPacks (Step 5)
$step5Body = @{ validated_packs = $validatedPacks; parsed_requirements = $parsedRequirements } | ConvertTo-Json
$expandedPacks = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step5/expand -ContentType "application/json" -Body $step5Body

# Get ThermalFilteredPacks (Step 6)
$step6Body = @{ expanded_packs = $expandedPacks } | ConvertTo-Json
$thermalFilteredPacks = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step6/thermal-filter -ContentType "application/json" -Body $step6Body

# Get RankedPacks (Step 7) - take the first one for CAD mock
$step7Body = @{ thermal_filtered_packs = $thermalFilteredPacks; parsed_requirements = $parsedRequirements } | ConvertTo-Json
$rankedPacks = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step7/preliminary-rank -ContentType "application/json" -Body $step7Body
$topPack = $rankedPacks.ranked_packs[0] # Assuming ranked_packs is an array

# Input for Step 8
$step8Body = @{ ranked_pack = $topPack } | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step8/cad-mock -ContentType "application/json" -Body $step8Body
```

#### Step 9 — Thermal Simulation (`/api/v1/step9/thermal-simulation`)

**Input:** A single `RankedPack` JSON (from Step 7).
**Output:** `ThermalSimulationResult` JSON object.

##### PowerShell

```powershell
# ... (previous steps to get $topPack from Step 7, as in Step 8) ...

# Input for Step 9
$step9Body = @{ ranked_pack = $topPack } | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step9/thermal-simulation -ContentType "application/json" -Body $step9Body
```

#### Step 10 — Final Rank (`/api/v1/step10/final-rank`)

**Input:** `RankedPacks` JSON (from Step 7) and an array of `ThermalSimulationResult` JSON objects (from Step 9 for each pack).
**Output:** `FinalRankedPacks` JSON object.

##### PowerShell

```powershell
# ... (previous steps to get $rankedPacks from Step 7) ...

# Simulate thermal results for each pack (in a real scenario, this would be a loop)
# For this example, let's assume we have thermal results for all packs in $rankedPacks
# In a real scenario, you'd run Step 9 for each pack and collect the results.
# For simplicity, we'll create a dummy array of thermal results.
$thermalResults = @()
foreach ($pack in $rankedPacks.ranked_packs) {
    # In a real workflow, you'd call Step 9 here for each $pack
    # For this example, we'll just create a placeholder result
    $thermalResult = @{
        pack_id = $pack.pack_id
        max_temp_c = (Get-Random -Minimum 30 -Maximum 50)
        avg_temp_c = (Get-Random -Minimum 25 -Maximum 45)
        # ... other thermal simulation data
    }
    $thermalResults += $thermalResult
}

# Combine inputs for Step 10
$step10Body = @{
    ranked_packs = $rankedPacks
    thermal_simulation_results = $thermalResults
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step10/final-rank -ContentType "application/json" -Body $step10Body
```

#### Step 11 — Generate Report (`/api/v1/step11/generate-report`)

**Input:** `FinalRankedPacks` JSON (from Step 10) and `ParsedRequirements` JSON (from Step 1).
**Output:** `FinalReport` JSON object.

##### PowerShell

```powershell
# Get ParsedRequirements (Step 1)
$parsedRequirements = Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step1/parse-requirements -ContentType "application/json" -Body '{"query": "72V 4kWh electric motorcycle battery, under 25kg, NMC preferred"}'

# ... (previous steps to get $finalRankedPacks from Step 10) ...

# Combine inputs for Step 11
$step11Body = @{
    final_ranked_packs = $finalRankedPacks
    parsed_requirements = $parsedRequirements
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://localhost:8001/api/v1/step11/generate-report -ContentType "application/json" -Body $step11Body
```

> **Note:** For `curl` with individual steps, you'll often need to manually copy the JSON output from a previous step and paste it into the `-d` argument for the next step. PowerShell's object handling makes this easier.

### 8.4 — Using the Swagger UI (Recommended for Interactive Testing)

Once the server is running, open your web browser and navigate to:

```
http://localhost:8001/docs
```

This will open the **interactive FastAPI Swagger UI**. Here, you can:
- See all available API endpoints.
- View the expected input and output schemas for each endpoint.
- Directly test any endpoint by clicking "Try it out", filling in the parameters, and clicking "Execute".
- The UI automatically formats JSON requests and responses, making it ideal for exploring the API without manual `curl` or PowerShell commands.

---

## 9. n8n Workflow Setup — Connecting Local Backend to n8n Cloud

> **Scenario:** Your FastAPI pipeline is running **locally** on port `8001`, and your n8n instance is **on the cloud**. Since n8n Cloud cannot reach `localhost` directly, you need to expose your local server via a **tunnel** first.

---

### Step 9.1 — Expose your local backend with ngrok

Make sure your virtual environment (`bms`) is active. Then in a **separate terminal**:

```powershell
# Activate the venv first (if not already active)
& "c:/Users/Divyansh Kumar/Desktop/Code/BMS-priv/AEDI/LP/bms/Scripts/Activate.ps1"

# Start the tunnel on port 8001
ngrok http 8001
```

ngrok will display output like this:

```
Session Status    online
Account           your-email@gmail.com
...
Forwarding        https://a1b2-c3d4-5e6f.ngrok-free.app -> http://localhost:8001
```

**Copy the `https://...ngrok-free.app` URL** — you will use this in n8n.

> ⚠️ **Keep both terminals running:** one for `uvicorn` (backend) and one for `ngrok` (tunnel).  
> The tunnel URL changes every time you restart ngrok (on the free plan).

---

### Step 9.2 — Import the Workflow into n8n Cloud

1. Go to **`https://aedi.app.n8n.cloud`**
2. Click **Add workflow** → **Import from file**
3. Select the file: `n8n/workflow_template.json`
4. Click **Import**

---

### Step 9.3 — Set the Backend URL Variable in n8n

1. In n8n, go to **Settings** (bottom-left gear icon) → **Variables**
2. Click **Add Variable**
3. Set:
   - **Name:** `FASTAPI_BASE_URL`
   - **Value:** `https://a1b2-c3d4-5e6f.ngrok-free.app` ← your ngrok URL (no trailing slash)
4. Click **Save**

> Every time you restart ngrok and get a new URL, update this variable with the new URL.

---

### Step 9.4 — Activate and Test the Workflow

1. Open the imported workflow in n8n
2. Click the **Activate** toggle (top-right) to turn it on
3. Find the **Webhook** node (first node) and click it to see your webhook URL. It will look like:
   ```
   https://aedi.app.n8n.cloud/webhook/aedi-pipeline
   ```

---

### Step 9.5 — Send a Test Request

#### PowerShell (Windows):

```powershell
$body = @{ query = "Design a 48V 2kWh battery pack for an electric scooter, max 12kg" } | ConvertTo-Json
Invoke-RestMethod -Method Post `
  -Uri "https://aedi.app.n8n.cloud/webhook/aedi-pipeline" `
  -ContentType "application/json" `
  -Body $body
```

#### curl (Git Bash / WSL):

```bash
curl -X POST https://aedi.app.n8n.cloud/webhook/aedi-pipeline \
  -H "Content-Type: application/json" \
  -d '{"query": "Design a 48V 2kWh battery pack for an electric scooter, max 12kg"}'
```

---

### Step 9.6 — Verify it's Working

1. **n8n Execution Log:** In n8n, click **Executions** (left sidebar) — you should see a new execution appear. Click into it to see data flowing through each of the 11 steps.

2. **Backend terminal:** Your `uvicorn` terminal should show incoming requests for each step:
   ```
   INFO:     POST /api/v1/step1/parse-requirements  200 OK
   INFO:     POST /api/v1/step2/query-rules          200 OK
   ...
   INFO:     POST /api/v1/step11/generate-report     200 OK
   ```

3. **ngrok dashboard:** Open `http://localhost:4040` in your browser to see all HTTP requests being tunneled in real time.

4. **Result:** The command should return a full `FinalReport` JSON containing top 3 battery pack designs with BMS recommendations.

---

### n8n Workflow Architecture (Flow Diagram)

```
[Webhook: POST /webhook/aedi-pipeline]
    │
    ▼
[HTTP Request: Step 1 — Parse Requirements → FASTAPI_BASE_URL/api/v1/step1/parse-requirements]
    │
    ▼
[IF: confidence >= 0.8?]
    ├─ NO  → [Respond: return follow_up_questions to user]
    │
    └─ YES ▼
[HTTP Request: Step 2 — Query Rules]
    │
    ▼
[HTTP Request: Step 3 — Compute Candidates]
    │
    ▼
[IF: candidates.length > 0?]
    ├─ NO  → [Respond: "No matching cells found"]
    │
    └─ YES ▼
[HTTP Request: Step 4 — Validate]
    │
    ▼
[HTTP Request: Step 5 — Expand]
    │
    ▼
[HTTP Request: Step 6 — Thermal Filter]
    │
    ▼
[HTTP Request: Step 7 — Preliminary Rank → Top 4]
    │
    ▼
[HTTP Request: Step 8 — CAD Mock (top candidate only)]
    │
    ▼
[SplitInBatches: Loop over top 4 candidates]
    │
    ▼
[HTTP Request: Step 9 — Thermal Simulation (per candidate)]
    │
    ▼
[Merge: Aggregate all thermal results]
    │
    ▼
[HTTP Request: Step 10 — Final Rank]
    │
    ▼
[HTTP Request: Step 11 — Generate Report]
    │
    ▼
[Respond to Webhook: Return FinalReport JSON]
```

> **Timeout setting:** In each HTTP Request node in n8n, set the timeout to **60 seconds** for LLM steps (Steps 1, 2, 5, 11) to avoid premature failures.

---

## 10. Deploy to Production

### Option 1: Railway.app (Recommended)

```bash
cd backend/AEDI_workflow
railway init
railway up
```

Add environment variables (`OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`) in the Railway dashboard.

### Option 2: Render.com

1. Connect your GitHub repo
2. Build command: `pip install -r AEDI_workflow/requirements.txt`
3. Start command: `uvicorn AEDI_workflow.api.app:app --host 0.0.0.0 --port $PORT`
4. Add environment variables in the Render dashboard

### Option 3: Vercel (with limitations)

Update `vercel.json` to add the workflow app. **Note:** Vercel has cold starts and a **10-second timeout** on the free tier, which may not work for LLM-heavy steps (Steps 1, 2, 5, 11).

---

## 11. Pipeline Deep Dive — What Each Step Does

### Step 1: Requirements Parser `LLM`

**File:** `services/step01_requirements_parser.py`  
**Type:** LLM (OpenAI `gpt-4o-mini`)  
**Input:** Natural language query (e.g., `"48V 2kWh e-scooter battery, max 12kg"`)  
**Output:** `ParsedRequirements` — structured fields: application_type, target_voltage, target_energy, max_weight, preferred_chemistry, etc.  
**Key Behavior:**

- Uses `llm.with_structured_output(ParsedRequirements)` — no raw text, all Pydantic-typed
- Sets `confidence < 0.8` if critical fields (voltage, energy, application) are missing
- Auto-derives `target_capacity_ah` from voltage and energy if missing
- Generates `follow_up_questions` for ambiguous inputs

### Step 2: Rule Query Engine `LLM + RAG`

**File:** `services/step02_rule_query_engine.py`  
**Type:** Hybrid RAG — pgvector semantic search + LLM fallback  
**Input:** `ParsedRequirements`  
**Output:** `DesignRules` — voltage rules, current rules, thermal/safety/BMS rules  
**Key Behavior:**

- Fetches voltage and current rules via `match_design_rules()` RPC (semantic search)
- Falls back to LLM-generated rules if RAG returns nothing
- Also fetches thermal, safety, and BMS rules via semantic search
- Fetches all `Critical` severity rules via exact filter (`get_rules_by_filter()`)

### Step 3: Pack Sizer `DETERMINISTIC`

**File:** `services/step03_pack_sizer.py`  
**Type:** Pure deterministic math — **no LLM**  
**Input:** `ParsedRequirements` + `DesignRules`  
**Output:** `list[PackCandidate]` — all possible S/P configurations  
**Key Behavior:**

- Queries Supabase `cells` table filtered by chemistry (based on application type)
- Computes `S = round(target_voltage / cell_voltage_nom)`
- Computes `P = ceil(required_Ah / cell_capacity_Ah)`
- Estimates pack weight with 30% overhead for BMS, wiring, enclosure
- Computes continuous/peak current and C-rates if power targets are specified

### Step 4: Validation `DETERMINISTIC`

**File:** `services/step04_validation.py`  
**Type:** Pure deterministic — **no LLM**  
**Input:** `list[PackCandidate]` + `ParsedRequirements` + `DesignRules`  
**Output:** `list[ValidatedCandidate]` — candidates that passed all checks  
**Key Behavior:**

- **TopologyRegulator:** Checks pack voltage within ±5% of target; auto-adjusts S by ±1 if needed
- **CurrentRegulator:** Checks C-rate limits; auto-increases P if continuous/peak C-rate exceeds limits
- Filters out candidates that exceed weight limit
- Records all adjustments in `topology_notes`

### Step 5: Expansion Manager `LLM`

**File:** `services/step05_expansion_manager.py`  
**Type:** LLM (for SOC window) + deterministic expansion  
**Input:** `list[ValidatedCandidate]` + application type  
**Output:** `list[ExpandedVariant]` — up to 3x the input candidates  
**Key Behavior:**

- LLM recommends optimal SOC operating window (min/max SOC as 0–1 fractions) based on chemistry and application
- Generates P, P+1, P+2 variants for each candidate (more parallel = more capacity/safety margin)
- Assigns cooling baseline (passive/active-air/liquid) based on estimated heat generation
- Calculates usable energy = pack_energy × (SOC_max − SOC_min)

### Step 6: Thermal Feasibility Filter `DETERMINISTIC`

**File:** `services/step06_thermal_feasibility.py`  
**Type:** Pure physics — **no LLM**  
**Input:** `list[ExpandedVariant]` + `ParsedRequirements`  
**Output:** `list[ExpandedVariant]` — thermally feasible variants only  
**Key Behavior:**

- Volume check: rejects if pack exceeds `max_volume_l`
- Heat generation: `Q = I² × R × N_cells`
- Temperature estimate: `T_max = T_ambient (40°C) + Q / (h × A_eff)` with cooling method-specific h values
- Rejects variants where `T_max ≥ 60°C` even with liquid cooling
- **ThermalCoolingOptimizer:** Downgrades cooling (liquid → active-air → passive) if thermal margin allows (saves cost)

### Step 7: Preliminary Ranker `DETERMINISTIC`

**File:** `services/step07_preliminary_ranker.py`  
**Type:** Pure deterministic scoring — **no LLM**  
**Input:** `list[ExpandedVariant]`  
**Output:** `list[RankedCandidate]` — **Top 4** candidates  
**Key Behavior:** Weighted scoring across 6 dimensions:

| Dimension              | Weight | Higher is Better?                   |
| ---------------------- | ------ | ----------------------------------- |
| Energy density (Wh/kg) | 25%    | Yes                                 |
| Weight                 | 20%    | No (lighter = better)               |
| Estimated cost         | 20%    | No (cheaper = better)               |
| Cycle life             | 15%    | Yes                                 |
| C-rate margin          | 10%    | Yes (more margin = safer)           |
| Thermal simplicity     | 10%    | Yes (passive > active-air > liquid) |

### Step 8: CAD Generation `PLACEHOLDER`

**File:** `services/step08_cad_generation.py`  
**Type:** Mock (placeholder for future CAD engine integration)  
**Input:** `RankedCandidate` (top candidate only)  
**Output:** Dictionary with estimated pack dimensions and packing method  
**Future:** Integrate with OpenSCAD or FreeCAD for real 3D pack layout generation

### Step 9: Thermal Simulation `DETERMINISTIC`

**File:** `services/step09_thermal_simulation.py`  
**Type:** Analytical physics — **no LLM**  
**Input:** `RankedCandidate` (runs for each top candidate)  
**Output:** `ThermalResult` — heat generation, T_max, thermal margin, feasibility  
**Key Behavior:**

- Continuous I²R heat generation with per-cell granularity
- Includes radiative cooling (Stefan-Boltzmann) for passive scenarios
- Cooling capacity = `h × A_eff × ΔT_max` (h varies by method: natural conv 10, forced air 50, liquid 500 W/m²·K)
- Generates detailed `CoolingStrategy` with thermal pad conductivity, fan power, or coolant flow rate
- Provides actionable recommendations if thermal margin is low

### Step 10: Final Ranker `DETERMINISTIC`

**File:** `services/step10_final_ranker.py`  
**Type:** Pure deterministic — **no LLM**  
**Input:** `list[RankedCandidate]` + `list[ThermalResult]`  
**Output:** Re-ranked `list[RankedCandidate]` with updated scores  
**Key Behavior:**

- Re-scores thermal dimension using actual simulation data: `margin_score = min(margin / 20, 1.0) + cooling_bonus`
- Thermal weight increases from 10% → **25%** (since simulation data is now available)
- Re-sorts and re-assigns ranks

### Step 11: Answer Generator `LLM`

**File:** `services/step11_answer_generator.py`  
**Type:** LLM (OpenAI `gpt-4o-mini`)  
**Input:** `list[RankedCandidate]` + `ParsedRequirements`  
**Output:** `FinalReport` — top 3 candidate reports with BMS, pros/cons, safety notes  
**Key Behavior:**

- Assigns variant names: "Performance Optimized", "Cost Optimized", "Space Optimized"
- Selects BMS IC from lookup table based on series count (BQ76942, BQ76952, MC33771C, ADBMS1818)
- Handles stacking for high S counts (>16S → distributed topology, >32S → daisy-chained ICs)
- LLM generates summary, pros, cons for each design
- Includes safety standards: AIS-156 Amendment 3, UN 38.3, IEC 62133-2

---

## 12. API Endpoints Reference

| Endpoint                           | Method | Input                                 | Output                     |
| ---------------------------------- | ------ | ------------------------------------- | -------------------------- |
| `/health`                          | GET    | —                                     | Health check JSON          |
| `/api/v1/pipeline/run`             | POST   | `{ "query": "..." }`                  | Full `FinalReport`         |
| `/api/v1/step1/parse-requirements` | POST   | `{ "query": "..." }`                  | `ParsedRequirements`       |
| `/api/v1/step2/query-rules`        | POST   | `ParsedRequirements`                  | `DesignRules`              |
| `/api/v1/step3/compute-candidates` | POST   | `{ requirements, rules }`             | `list[PackCandidate]`      |
| `/api/v1/step4/validate`           | POST   | `{ candidates, requirements, rules }` | `list[ValidatedCandidate]` |
| `/api/v1/step5/expand`             | POST   | `{ candidates, app_type }`            | `list[ExpandedVariant]`    |
| `/api/v1/step6/thermal-filter`     | POST   | `{ variants, requirements }`          | `list[ExpandedVariant]`    |
| `/api/v1/step7/rank-preliminary`   | POST   | `list[ExpandedVariant]`               | `list[RankedCandidate]`    |
| `/api/v1/step8/cad-mock`           | POST   | `RankedCandidate`                     | CAD metadata dict          |
| `/api/v1/step9/thermal-simulation` | POST   | `RankedCandidate`                     | `ThermalResult`            |
| `/api/v1/step10/rank-final`        | POST   | `{ candidates, thermal_results }`     | `list[RankedCandidate]`    |
| `/api/v1/step11/generate-report`   | POST   | `{ candidates, requirements }`        | `FinalReport`              |

> **Tip:** Open `http://localhost:8001/docs` for the interactive Swagger UI — the best way to explore and test endpoints.

---

## 13. Architecture & Design Decisions

### LLM vs Deterministic Step Split

| Step Type                             | Steps             | Why                                                   |
| ------------------------------------- | ----------------- | ----------------------------------------------------- |
| **LLM** (structured output)           | 1, 2, 5, 11       | Require natural language understanding or generation  |
| **Deterministic** (pure math/physics) | 3, 4, 6, 7, 9, 10 | **No LLM can hallucinate physics** — ensures accuracy |
| **Placeholder**                       | 8                 | Future CAD engine integration                         |

### Key Principles

1. **Structured outputs only** — Steps 1, 2, 5, 11 use `llm.with_structured_output(PydanticModel)` — no raw text, no parsing
2. **RAG with fallback** — Step 2 queries pgvector first, falls back to LLM if no rules match
3. **Modular API** — Each step is a separate endpoint, enabling n8n to orchestrate with branching/retries
4. **Full pipeline endpoint** — `/api/v1/pipeline/run` runs all steps in sequence for direct API usage
5. **Hierarchical fallback defaults** — Missing cell values are estimated using group medians (not a single hardcoded number)
6. **Physics-first thermal** — Steps 6 and 9 use real thermodynamic equations (I²R, Newton's law of cooling, Stefan-Boltzmann radiation)

---

## 14. Troubleshooting

| Issue                                 | Cause                             | Solution                                                           |
| ------------------------------------- | --------------------------------- | ------------------------------------------------------------------ |
| `OPENAI_API_KEY not set`              | `.env` not found                  | Ensure `backend/.env` exists (not inside `AEDI_workflow/`)         |
| `SUPABASE_URL / SUPABASE_KEY not set` | Missing env vars                  | Add both to `backend/.env`                                         |
| `match_design_rules` RPC fails        | Table not created                 | Run `02_design_rules_table.sql` in Supabase SQL Editor             |
| No cells returned in Step 3           | Empty cells table                 | Run `python sql/upload_cells.py`                                   |
| `upload_cells.py` column mismatch     | Excel headers differ              | Update `COLUMN_MAP` variants in the script                         |
| `upload_rules.py` fails               | Missing OPENAI_API_KEY            | Ensure API key is in `backend/.env`                                |
| Embeddings are NULL                   | Rules uploaded without embeddings | Re-run `python sql/upload_rules.py`                                |
| `cell_defaults.json` missing          | Not generated yet                 | Run `python sql/generate_defaults.py`                              |
| Inaccurate weight/thermal estimates   | Stale defaults                    | Re-run `python sql/generate_defaults.py` after adding cells        |
| `ModuleNotFoundError` on import       | Wrong working directory           | Run `uvicorn` from `backend/` directory, not `AEDI_workflow/`      |
| `design_rules table does not exist`   | SQL not executed                  | Run `02_design_rules_table.sql` in Supabase SQL Editor             |
| n8n timeout on LLM steps              | Default 5s timeout too short      | Increase HTTP Request node timeout to 60s in n8n                   |
| Import errors                         | Missing pip packages              | Run `pip install -r AEDI_workflow/requirements.txt`                |
| Pipeline returns 422                  | Low confidence in Step 1          | Query is too vague — provide voltage, energy, and application type |
| Pipeline returns 404                  | No matching cells                 | Check if cells exist for the requested chemistry in Supabase       |

---

## Quick Reference: Complete Setup in 7 Commands

```bash
# 1. Install dependencies
cd backend/AEDI_workflow
pip install -r requirements.txt
pip install openpyxl pandas

# 2. Create Supabase tables (do this in Supabase Dashboard SQL Editor)
#    → Paste sql/sql_queries/01_cells_table.sql → Run
#    → Paste sql/sql_queries/02_design_rules_table.sql → Run

# 3. Upload cell data
cd sql
python upload_cells.py

# 4. Upload design rules (with embeddings)
python upload_rules.py

# 5. Generate fallback defaults
python generate_defaults.py

# 6. Start the server
cd ../..
uvicorn AEDI_workflow.api.app:app --host 0.0.0.0 --port 8001 --reload

# 7. Test it!
# Open http://localhost:8001/docs in your browser
```
