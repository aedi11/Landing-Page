# AEDI n8n Workflow Architecture

## Overview

The n8n workflow orchestrates the 11-step battery pack configuration pipeline by calling
FastAPI endpoints hosted on your backend. Each step is a separate HTTP Request node in n8n,
allowing for conditional branching, error handling, and parallel execution where appropriate.

## n8n Cloud Instance

**URL:** `https://aedi.app.n8n.cloud`

## Architecture: Which Steps Are n8n Nodes vs FastAPI Endpoints?

| Step | Type | n8n Node | Why |
|------|------|----------|-----|
| 1. RequirementsParser | **FastAPI (HTTP Request)** | HTTP Request → `/api/v1/step1/parse-requirements` | LangChain structured output needed |
| 2. RuleQueryEngine | **FastAPI (HTTP Request)** | HTTP Request → `/api/v1/step2/query-rules` | RAG + pgvector + LLM fallback |
| 3. PackSizer | **FastAPI (HTTP Request)** | HTTP Request → `/api/v1/step3/compute-candidates` | Supabase query + deterministic math |
| 4. Validation | **FastAPI (HTTP Request)** | HTTP Request → `/api/v1/step4/validate` | Deterministic regulators |
| 5. ExpansionManager | **FastAPI (HTTP Request)** | HTTP Request → `/api/v1/step5/expand` | LLM for SOC window |
| 6. ThermalFilter | **FastAPI (HTTP Request)** | HTTP Request → `/api/v1/step6/thermal-filter` | Pure physics |
| 7. PreliminaryRanker | **FastAPI (HTTP Request)** | HTTP Request → `/api/v1/step7/rank-preliminary` | Deterministic scoring |
| 8. CAD Generation | **FastAPI (HTTP Request)** | HTTP Request → `/api/v1/step8/cad-mock` | Mock (future CAD) |
| 9. ThermalSimulation | **FastAPI (HTTP Request)** | HTTP Request → `/api/v1/step9/thermal-simulation` | Analytical physics |
| 10. FinalRanker | **FastAPI (HTTP Request)** | HTTP Request → `/api/v1/step10/rank-final` | Deterministic re-scoring |
| 11. AnswerGenerator | **FastAPI (HTTP Request)** | HTTP Request → `/api/v1/step11/generate-report` | LangChain for report |

### Native n8n Nodes Used

| Node | Purpose |
|------|---------|
| **Webhook** | Entry trigger — receives user query from frontend |
| **IF** | Branch after Step 1: check `confidence >= 0.8` |
| **Respond to Webhook** | Return follow-up questions if confidence < 0.8 |
| **SplitInBatches** | Loop over top 4 candidates for Step 9 thermal simulation |
| **Merge** | Aggregate thermal results back into single payload |
| **Supabase** (native node) | Direct DB reads (optional — can also go through FastAPI) |
| **Set** | Transform/reshape JSON between steps |
| **Error Trigger** | Global error handler for failed steps |

## Workflow Flow Diagram

```
[Webhook: POST /webhook/aedi-pipeline]
    │
    ▼
[HTTP Request: Step 1 — Parse Requirements]
    │
    ▼
[IF: confidence >= 0.8?]
    ├─ NO → [Respond to Webhook: return follow_up_questions]
    │
    ├─ YES ▼
[HTTP Request: Step 2 — Query Rules]
    │
    ▼
[HTTP Request: Step 3 — Compute Candidates]
    │
    ▼
[IF: candidates.length > 0?]
    ├─ NO → [Respond to Webhook: "No cells match"]
    │
    ├─ YES ▼
[HTTP Request: Step 4 — Validate]
    │
    ▼
[HTTP Request: Step 5 — Expand]
    │
    ▼
[HTTP Request: Step 6 — Thermal Filter]
    │
    ▼
[HTTP Request: Step 7 — Preliminary Rank]
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
[Merge: Aggregate thermal results]
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

## FastAPI Deployment Requirements

The FastAPI backend must be accessible from n8n Cloud. Options:

1. **Vercel** (current setup for main.py) — works but has cold start latency
2. **Railway.app** — recommended for always-on Python APIs
3. **Render.com** — free tier available
4. **Self-hosted** — if running n8n self-hosted too

### Environment Variables Needed on Deploy

```
OPENAI_API_KEY=sk-proj-...
SUPABASE_URL=https://ikljsphfuorarqqykzqg.supabase.co
SUPABASE_KEY=sb_secret_...
```

## n8n Webhook Configuration

**Trigger URL:** `https://aedi.app.n8n.cloud/webhook/aedi-pipeline`

**Method:** POST

**Request Body:**
```json
{
  "query": "Design a 48V 2kWh battery pack for an electric scooter, max 12kg"
}
```

**Response:** Full `FinalReport` JSON with top 3 candidates.
