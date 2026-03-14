"""
AEDI Workflow — FastAPI Application
Exposes endpoints for n8n to call each pipeline step or the full pipeline.
"""

import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..models.requirements import UserRequirements, ParsedRequirements
from ..models.rules import DesignRules
from ..models.candidates import PackCandidate, ValidatedCandidate, ExpandedVariant
from ..models.thermal import ThermalResult
from ..models.output import RankedCandidate, FinalReport

from ..services.step01_requirements_parser import parse_requirements
from ..services.step02_rule_query_engine import query_design_rules
from ..services.step03_pack_sizer import compute_candidates
from ..services.step04_validation import validate_candidates
from ..services.step05_expansion_manager import expand_candidates
from ..services.step06_thermal_feasibility import filter_thermal_feasibility
from ..services.step07_preliminary_ranker import rank_preliminary
from ..services.step08_cad_generation import mock_cad_generation
from ..services.step09_thermal_simulation import run_thermal_simulation
from ..services.step10_final_ranker import rank_final
from ..services.step11_answer_generator import generate_report

# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AEDI Battery Pack Configuration Pipeline",
    version="1.0.0",
    description="11-step deterministic battery pack design pipeline for n8n orchestration",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Individual Step Endpoints (for n8n granular orchestration) ───────────────

@app.post("/api/v1/step1/parse-requirements", response_model=ParsedRequirements)
async def step1_parse(input: UserRequirements):
    """Step 1: Parse natural language requirements into structured format."""
    try:
        return parse_requirements(input)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Step 1 failed: {e}")


@app.post("/api/v1/step2/query-rules", response_model=DesignRules)
async def step2_rules(requirements: ParsedRequirements):
    """Step 2: Fetch design rules via RAG + LLM fallback."""
    try:
        return query_design_rules(requirements)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Step 2 failed: {e}")


class Step3Input(BaseModel):
    requirements: ParsedRequirements
    rules: DesignRules


@app.post("/api/v1/step3/compute-candidates", response_model=list[PackCandidate])
async def step3_size(input: Step3Input):
    """Step 3: Compute S/P candidates from cells database."""
    try:
        return compute_candidates(input.requirements, input.rules)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Step 3 failed: {e}")


class Step4Input(BaseModel):
    candidates: list[PackCandidate]
    requirements: ParsedRequirements
    rules: DesignRules


@app.post("/api/v1/step4/validate", response_model=list[ValidatedCandidate])
async def step4_validate(input: Step4Input):
    """Step 4: Validate candidates with TopologyRegulator + CurrentRegulator."""
    try:
        return validate_candidates(input.candidates, input.requirements, input.rules)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Step 4 failed: {e}")


class Step5Input(BaseModel):
    candidates: list[ValidatedCandidate]
    app_type: str
    requirements: ParsedRequirements | None = None


@app.post("/api/v1/step5/expand", response_model=list[ExpandedVariant])
async def step5_expand(input: Step5Input):
    """Step 5: Expand candidates with SOC windows and P variants."""
    try:
        return expand_candidates(input.candidates, input.app_type, input.requirements)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Step 5 failed: {e}")


class Step6Input(BaseModel):
    variants: list[ExpandedVariant]
    requirements: ParsedRequirements


@app.post("/api/v1/step6/thermal-filter", response_model=list[ExpandedVariant])
async def step6_thermal(input: Step6Input):
    """Step 6: Filter by thermal feasibility."""
    try:
        return filter_thermal_feasibility(input.variants, input.requirements)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Step 6 failed: {e}")


class Step7Input(BaseModel):
    variants: list[ExpandedVariant]
    app_type: str = "e-scooter"


@app.post("/api/v1/step7/rank-preliminary", response_model=list[RankedCandidate])
async def step7_rank(input: Step7Input):
    """Step 7: Preliminary ranking — select top 4."""
    try:
        return rank_preliminary(input.variants, top_n=4, app_type=input.app_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Step 7 failed: {e}")


@app.post("/api/v1/step8/cad-mock")
async def step8_cad(candidate: RankedCandidate):
    """Step 8: Mock CAD generation for top candidate."""
    try:
        return mock_cad_generation(candidate)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Step 8 failed: {e}")


@app.post("/api/v1/step9/thermal-simulation", response_model=ThermalResult)
async def step9_sim(candidate: RankedCandidate):
    """Step 9: Analytical thermal simulation."""
    try:
        return run_thermal_simulation(candidate)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Step 9 failed: {e}")


class Step10Input(BaseModel):
    candidates: list[RankedCandidate]
    thermal_results: list[ThermalResult]


@app.post("/api/v1/step10/rank-final", response_model=list[RankedCandidate])
async def step10_rerank(input: Step10Input):
    """Step 10: Final ranking with thermal data."""
    try:
        return rank_final(input.candidates, input.thermal_results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Step 10 failed: {e}")


class Step11Input(BaseModel):
    candidates: list[RankedCandidate]
    requirements: ParsedRequirements


@app.post("/api/v1/step11/generate-report", response_model=FinalReport)
async def step11_report(input: Step11Input):
    """Step 11: Generate final technical report."""
    try:
        return generate_report(input.candidates, input.requirements)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Step 11 failed: {e}")


# ── Full Pipeline Endpoint (single call) ─────────────────────────────────────

@app.post("/api/v1/pipeline/run", response_model=FinalReport)
async def run_full_pipeline(input: UserRequirements):
    """Run the complete 11-step pipeline in one call.

    This endpoint is useful for direct API calls without n8n orchestration.
    """
    try:
        # Step 1
        requirements = parse_requirements(input)
        if requirements.confidence < 0.8:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Insufficient requirements. Please provide more details.",
                    "follow_up_questions": requirements.follow_up_questions,
                },
            )

        # Step 2
        rules = query_design_rules(requirements)

        # Step 3
        candidates = compute_candidates(requirements, rules)
        if not candidates:
            raise HTTPException(status_code=404, detail="No matching cells found in database.")

        # Step 4
        validated = validate_candidates(candidates, requirements, rules)
        if not validated:
            raise HTTPException(status_code=404, detail="No candidates passed validation.")

        # Step 5
        expanded = expand_candidates(validated, requirements.application_type, requirements)

        # Step 6
        feasible = filter_thermal_feasibility(expanded, requirements)
        if not feasible:
            raise HTTPException(status_code=404, detail="No thermally feasible candidates.")

        # Step 7
        preliminary = rank_preliminary(feasible, top_n=4, app_type=requirements.application_type)

        # Step 8 (mock CAD for top candidate)
        if preliminary:
            mock_cad_generation(preliminary[0])

        # Step 9 (thermal simulation for all top candidates)
        thermal_results = [run_thermal_simulation(c) for c in preliminary]

        # Step 10
        final_ranked = rank_final(preliminary, thermal_results)

        # Step 11
        report = generate_report(final_ranked, requirements)

        return report

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {e}")


# ── Health Check ─────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "AEDI Workflow Pipeline", "version": "1.0.0"}
