"""Canonical tool catalog, JSON schemas, and execution dispatcher for all 6 Pharmakon MCP tools."""

from __future__ import annotations

import time
from typing import Any

from server.rate_limit import record_tool_usage
from server.tools.openfda import adverse_event_summary, drug_label_lookup
from server.tools.pubmed import literature_search
from server.tools.safety_brief import drug_safety_brief
from server.tools.trials import get_trial_details, search_trials

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "search_trials",
        "title": "Search Clinical Trials",
        "category": "ClinicalTrials.gov API v2",
        "description": (
            "Search ClinicalTrials.gov (API v2) for clinical studies by condition, drug "
            "(normalized via RxNorm), trial phase, recruitment status, or geographic location."
        ),
        "parameters": [
            {
                "name": "condition",
                "type": "string",
                "required": False,
                "placeholder": "type 2 diabetes",
                "description": "Disease or medical condition (maps to query.cond).",
            },
            {
                "name": "drug",
                "type": "string",
                "required": False,
                "placeholder": "Ozempic",
                "description": "Drug or intervention name, brand or generic (normalized via RxNorm).",
            },
            {
                "name": "phase",
                "type": "string",
                "required": False,
                "enum": ["", "EARLY_PHASE1", "PHASE1", "PHASE2", "PHASE3", "PHASE4"],
                "placeholder": "PHASE3",
                "description": "Clinical trial phase filter (AREA[Phase]).",
            },
            {
                "name": "status",
                "type": "string",
                "required": False,
                "enum": [
                    "",
                    "RECRUITING",
                    "ACTIVE_NOT_RECRUITING",
                    "COMPLETED",
                    "NOT_YET_RECRUITING",
                    "TERMINATED",
                ],
                "placeholder": "RECRUITING",
                "description": "Recruitment status filter (filter.overallStatus).",
            },
            {
                "name": "location",
                "type": "string",
                "required": False,
                "placeholder": "United States",
                "description": "Country, state, city, or facility (maps to query.locn).",
            },
            {
                "name": "limit",
                "type": "integer",
                "required": False,
                "default": 5,
                "min": 1,
                "max": 50,
                "description": "Maximum number of clinical trials to return (1-50).",
            },
        ],
        "example_args": {
            "condition": "obesity",
            "drug": "semaglutide",
            "phase": "PHASE3",
            "status": "COMPLETED",
            "limit": 5,
        },
    },
    {
        "name": "get_trial_details",
        "title": "Get Trial Details",
        "category": "ClinicalTrials.gov API v2",
        "description": (
            "Retrieve full protocol summary, eligibility criteria, study arms, interventions, "
            "primary/secondary outcomes, and site locations for a single trial by NCT ID."
        ),
        "parameters": [
            {
                "name": "nct_id",
                "type": "string",
                "required": True,
                "placeholder": "NCT03548935",
                "description": "ClinicalTrials.gov study identifier in NCT######## format.",
            }
        ],
        "example_args": {"nct_id": "NCT03548935"},
    },
    {
        "name": "adverse_event_summary",
        "title": "Adverse Event Summary (FAERS)",
        "category": "openFDA FAERS + RxNorm",
        "description": (
            "Aggregate top reported MedDRA adverse event reactions, report counts, and seriousness "
            "breakdown from openFDA FAERS (/drug/event.json) with RxNorm drug normalization."
        ),
        "parameters": [
            {
                "name": "drug",
                "type": "string",
                "required": True,
                "placeholder": "semaglutide",
                "description": "Brand or generic drug name (normalized via RxNorm).",
            },
            {
                "name": "limit",
                "type": "integer",
                "required": False,
                "default": 10,
                "min": 1,
                "max": 50,
                "description": "Number of top MedDRA Preferred Term reactions to return (1-50).",
            },
        ],
        "example_args": {"drug": "semaglutide", "limit": 10},
    },
    {
        "name": "drug_label_lookup",
        "title": "FDA Drug Label Lookup (SPL)",
        "category": "openFDA SPL + RxNorm",
        "description": (
            "Fetch structured FDA product labeling (/drug/label.json) including boxed warnings, "
            "warnings & cautions, contraindications, dosage & administration, and indications."
        ),
        "parameters": [
            {
                "name": "drug",
                "type": "string",
                "required": True,
                "placeholder": "warfarin",
                "description": "Brand or generic drug name.",
            },
            {
                "name": "sections",
                "type": "array",
                "required": False,
                "placeholder": "boxed_warning, warnings, contraindications, dosage_and_administration",
                "description": (
                    "Optional list of SPL label sections to extract (defaults to boxed_warning, "
                    "warnings_and_cautions, contraindications, dosage_and_administration, adverse_reactions)."
                ),
            },
        ],
        "example_args": {
            "drug": "warfarin",
            "sections": [
                "boxed_warning",
                "warnings",
                "contraindications",
                "dosage_and_administration",
            ],
        },
    },
    {
        "name": "literature_search",
        "title": "PubMed Literature Search",
        "category": "NCBI PubMed E-utilities",
        "description": (
            "Search peer-reviewed biomedical literature via NCBI PubMed E-utilities (esearch + efetch) "
            "filtering by drug, condition, publication window (years), and result limit."
        ),
        "parameters": [
            {
                "name": "drug",
                "type": "string",
                "required": False,
                "placeholder": "pembrolizumab",
                "description": "Drug or active ingredient name.",
            },
            {
                "name": "condition",
                "type": "string",
                "required": False,
                "placeholder": "melanoma",
                "description": "Condition, indication, or safety topic (e.g. 'myocarditis').",
            },
            {
                "name": "years",
                "type": "integer",
                "required": False,
                "default": 5,
                "min": 1,
                "max": 50,
                "description": "Lookback window in years (e.g. 5 for last 5 years).",
            },
            {
                "name": "limit",
                "type": "integer",
                "required": False,
                "default": 5,
                "min": 1,
                "max": 25,
                "description": "Maximum number of PubMed articles with abstracts to return (1-25).",
            },
        ],
        "example_args": {
            "drug": "pembrolizumab",
            "condition": "melanoma",
            "years": 5,
            "limit": 5,
        },
    },
    {
        "name": "drug_safety_brief",
        "title": "Comprehensive Drug Safety Brief",
        "category": "Composite (openFDA + PubMed + RxNorm)",
        "description": (
            "Generate a unified drug safety intelligence report combining RxNorm normalization, "
            "openFDA FAERS adverse events, FDA SPL label warnings/contraindications, openFDA recall "
            "enforcement reports, and recent PubMed safety literature in one parallel call."
        ),
        "parameters": [
            {
                "name": "drug",
                "type": "string",
                "required": True,
                "placeholder": "metformin",
                "description": "Brand or generic drug name to generate a full safety brief for.",
            }
        ],
        "example_args": {"drug": "metformin"},
    },
]


async def execute_tool_by_name(
    tool_name: str,
    arguments: dict[str, Any],
    *,
    api_key_id: int | None = None,
) -> dict[str, Any]:
    """Execute one of the 6 MCP tools by name and record latency/status in usage_logs."""
    started = time.perf_counter()
    status_str = "success"
    err_msg: str | None = None
    try:
        if tool_name == "search_trials":
            res = await search_trials(
                condition=arguments.get("condition"),
                drug=arguments.get("drug"),
                phase=arguments.get("phase"),
                status=arguments.get("status"),
                location=arguments.get("location"),
                limit=int(arguments.get("limit") or 10),
            )
        elif tool_name == "get_trial_details":
            res = await get_trial_details(
                nct_id=str(arguments.get("nct_id") or ""),
            )
        elif tool_name == "adverse_event_summary":
            res = await adverse_event_summary(
                drug=str(arguments.get("drug") or ""),
                limit=int(arguments.get("limit") or 10),
            )
        elif tool_name == "drug_label_lookup":
            raw_sections = arguments.get("sections")
            if isinstance(raw_sections, str):
                sections_list = [s.strip() for s in raw_sections.split(",") if s.strip()]
            elif isinstance(raw_sections, list):
                sections_list = [str(s).strip() for s in raw_sections if str(s).strip()]
            else:
                sections_list = None
            res = await drug_label_lookup(
                drug=str(arguments.get("drug") or ""),
                sections=sections_list,
            )
        elif tool_name == "literature_search":
            res = await literature_search(
                drug=arguments.get("drug"),
                condition=arguments.get("condition"),
                years=arguments.get("years", 5),
                limit=int(arguments.get("limit") or 10),
            )
        elif tool_name == "drug_safety_brief":
            res = await drug_safety_brief(
                drug=str(arguments.get("drug") or ""),
            )
        else:
            status_str = "error"
            err_msg = f"Unknown tool '{tool_name}'."
            return {"status": "error", "error": err_msg}

        if isinstance(res, dict) and res.get("status") in {"error", "upstream_error"}:
            status_str = str(res.get("status"))
            err_msg = str(res.get("error") or "")
        return res
    except Exception as exc:
        status_str = "error"
        err_msg = str(exc)
        raise
    finally:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        record_tool_usage(
            api_key_id=api_key_id,
            tool_name=tool_name,
            latency_ms=elapsed_ms,
            status=status_str,
            error_message=err_msg,
        )
