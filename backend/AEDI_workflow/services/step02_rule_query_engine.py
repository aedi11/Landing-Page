"""
Step 2: RuleQueryEngine
Hybrid RAG: fetch rules from Supabase pgvector, with LLM fallback if no rules found.
UPDATED to match new design_rules schema (flat columns, not JSONB parameters).
"""

from langchain_core.prompts import ChatPromptTemplate
from ..config import llm, embeddings, supabase
from ..models.requirements import ParsedRequirements
from ..models.rules import VoltageRule, CurrentRule, DesignRules


def _embed_query(text: str) -> list[float]:
    """Generate embedding vector for a query string."""
    return embeddings.embed_query(text)


def _fetch_rules_from_supabase(
    query_text: str,
    rule_type: str | None = None,
    parameter: str | None = None,
    match_count: int = 10,
    threshold: float = 0.55,
) -> list[dict]:
    """Fetch design rules from Supabase pgvector via the match_design_rules RPC.

    Uses the updated schema with flat columns:
    - rule_type: Electrical, Thermal, Mechanical, Safety, etc.
    - parameter: voltage, current, temperature, etc.
    - constraint_expr: The actual rule text
    - min_value, max_value, nominal_value, unit
    """
    query_embedding = _embed_query(query_text)

    try:
        result = supabase.rpc("match_design_rules", {
            "query_embedding": query_embedding,
            "match_count": match_count,
            "match_threshold": threshold,
            "filter_rule_type": rule_type,
            "filter_parameter": parameter,
        }).execute()
        return result.data or []
    except Exception:
        return []


def _fetch_rules_by_filter(
    rule_type: str | None = None,
    parameter: str | None = None,
    severity: str | None = None,
    applies_to: str | None = None,
) -> list[dict]:
    """Fetch rules by exact filters (no embedding needed)."""
    try:
        result = supabase.rpc("get_rules_by_filter", {
            "filter_rule_type": rule_type,
            "filter_severity": severity,
            "filter_applies_to": applies_to,
            "filter_parameter": parameter,
        }).execute()
        return result.data or []
    except Exception:
        return []


def _fallback_voltage_rules(requirements: ParsedRequirements) -> list[VoltageRule]:
    """LLM fallback: generate voltage rules when RAG returns nothing."""
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a battery systems engineer. Given an application type, provide the "
         "standard voltage rules including recommended pack voltages and series count "
         "mapping for NMC and LFP chemistries."),
        ("human", "Application: {app_type}, Target voltage: {voltage}V"),
    ])
    chain = prompt | llm.with_structured_output(VoltageRule)
    rule = chain.invoke({
        "app_type": requirements.application_type,
        "voltage": requirements.target_voltage_v,
    })
    return [rule]


def _fallback_current_rules(requirements: ParsedRequirements) -> list[CurrentRule]:
    """LLM fallback: generate current/C-rate rules when RAG returns nothing."""
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a battery systems engineer. Given an application type, provide "
         "the standard C-rate limits for continuous and peak discharge."),
        ("human", "Application: {app_type}, Nominal power: {power}W"),
    ])
    chain = prompt | llm.with_structured_output(CurrentRule)
    rule = chain.invoke({
        "app_type": requirements.application_type,
        "power": requirements.nominal_power_w or 1500,
    })
    return [rule]


def _parse_rag_voltage_rules(raw_rules: list[dict]) -> list[VoltageRule]:
    """Convert raw Supabase rows (flat schema) into VoltageRule models."""
    results = []
    for row in raw_rules:
        min_v = row.get("min_value")
        max_v = row.get("max_value")
        nom_v = row.get("nominal_value")

        recommended = []
        if nom_v:
            recommended.append(nom_v)
        if min_v and max_v:
            recommended.extend([min_v, max_v])

        results.append(VoltageRule(
            application=row.get("applies_to", "unknown"),
            recommended_voltages=recommended if recommended else [48.0],
            series_map=[],
            source=row.get("source"),
        ))
    return results


def _parse_rag_current_rules(raw_rules: list[dict]) -> list[CurrentRule]:
    """Convert raw Supabase rows (flat schema) into CurrentRule models."""
    results = []
    for row in raw_rules:
        max_val = row.get("max_value")
        nom_val = row.get("nominal_value")

        results.append(CurrentRule(
            application=row.get("applies_to", "unknown"),
            max_continuous_c_rate=nom_val or 1.5,
            max_peak_c_rate=max_val or 3.0,
            peak_duration_s=5.0,
            ideal_continuous_c_rate=(nom_val or 1.5) * 0.67,
            source=row.get("source"),
        ))
    return results


def _extract_rule_dict(row: dict) -> dict:
    """Convert a flat rule row into a clean dict."""
    return {
        "constraint": row.get("constraint_expr", ""),
        "parameter": row.get("parameter"),
        "min_value": row.get("min_value"),
        "max_value": row.get("max_value"),
        "nominal_value": row.get("nominal_value"),
        "unit": row.get("unit"),
        "severity": row.get("severity"),
        "source": row.get("source"),
    }


def query_design_rules(requirements: ParsedRequirements) -> DesignRules:
    """Fetch voltage + current rules via RAG, falling back to LLM if needed.

    Args:
        requirements: Parsed user requirements from Step 1

    Returns:
        DesignRules with voltage, current, thermal, safety, and BMS rules
    """
    search_text = f"{requirements.application_type} {requirements.target_voltage_v}V battery pack"

    # RAG: fetch voltage rules (Electrical type, voltage parameter)
    raw_voltage = _fetch_rules_from_supabase(
        search_text, rule_type="Electrical", parameter="voltage"
    )
    voltage_rules = _parse_rag_voltage_rules(raw_voltage) if raw_voltage else _fallback_voltage_rules(requirements)

    # RAG: fetch current rules (Electrical type, current parameter)
    raw_current = _fetch_rules_from_supabase(
        search_text, rule_type="Electrical", parameter="current"
    )
    current_rules = _parse_rag_current_rules(raw_current) if raw_current else _fallback_current_rules(requirements)

    # RAG: fetch supplementary rules — no LLM fallback needed
    raw_thermal = _fetch_rules_from_supabase(search_text, rule_type="Thermal")
    raw_safety = _fetch_rules_from_supabase(search_text, rule_type="Safety")
    raw_bms = _fetch_rules_from_supabase(search_text, parameter="bms")

    # Also fetch all critical rules by exact filter
    critical_rules = _fetch_rules_by_filter(severity="Critical")

    return DesignRules(
        voltage_rules=voltage_rules,
        current_rules=current_rules,
        thermal_rules=[_extract_rule_dict(r) for r in raw_thermal],
        safety_rules=[_extract_rule_dict(r) for r in (raw_safety + critical_rules)],
        bms_rules=[_extract_rule_dict(r) for r in raw_bms],
    )
