"""FastMCP server instance and all 6 MCP tool registrations over Streamable HTTP."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from server.tool_registry import execute_tool_by_name

# Context variable set by MCPAuthMiddleware so MCP tool calls log against the caller's APIKey
current_mcp_api_key_id: ContextVar[int | None] = ContextVar("current_mcp_api_key_id", default=None)

mcp = FastMCP(
    name="Pharmakon — Drug Safety & Clinical Trials MCP",
    instructions=(
        "Pharmakon is an authoritative biomedical data retrieval server for clinical trials "
        "(ClinicalTrials.gov API v2), drug adverse events & recalls (openFDA FAERS/SPL/Enforcement), "
        "peer-reviewed literature (PubMed E-utilities), and drug normalization (RxNorm). "
        "All tool outputs are informational only and never constitute medical advice."
    ),
)


@mcp.tool(
    name="search_trials",
    description=(
        "Search ClinicalTrials.gov (API v2) for clinical studies filtering by condition/disease, "
        "drug/intervention (automatically normalized via RxNorm), trial phase (PHASE1..PHASE4), "
        "recruitment status (RECRUITING, COMPLETED, ACTIVE_NOT_RECRUITING, etc.), and geographic location. "
        "Returns compact trial summaries with NCT IDs, phases, enrollment, sponsors, and interventions."
    ),
)
async def tool_search_trials(
    condition: Annotated[
        str | None,
        Field(
            default=None,
            description="Disease or medical condition (e.g., 'type 2 diabetes', 'non-small cell lung cancer').",
        ),
    ] = None,
    drug: Annotated[
        str | None,
        Field(
            default=None,
            description="Drug or intervention name, brand or generic (e.g., 'semaglutide', 'Ozempic', 'pembrolizumab').",
        ),
    ] = None,
    phase: Annotated[
        str | None,
        Field(
            default=None,
            description="Clinical trial phase filter: PHASE1, PHASE2, PHASE3, PHASE4, or EARLY_PHASE1.",
        ),
    ] = None,
    status: Annotated[
        str | None,
        Field(
            default=None,
            description="Recruitment status: RECRUITING, COMPLETED, ACTIVE_NOT_RECRUITING, NOT_YET_RECRUITING, TERMINATED.",
        ),
    ] = None,
    location: Annotated[
        str | None,
        Field(
            default=None,
            description="Country, state, city, or facility name (e.g., 'United States', 'Boston').",
        ),
    ] = None,
    limit: Annotated[
        int,
        Field(
            default=10,
            ge=1,
            le=50,
            description="Maximum number of clinical trials to return (1-50, default 10).",
        ),
    ] = 10,
) -> dict[str, Any]:
    return await execute_tool_by_name(
        "search_trials",
        {
            "condition": condition,
            "drug": drug,
            "phase": phase,
            "status": status,
            "location": location,
            "limit": limit,
        },
        api_key_id=current_mcp_api_key_id.get(),
    )


@mcp.tool(
    name="get_trial_details",
    description=(
        "Retrieve comprehensive protocol, eligibility criteria, study arms, interventions, "
        "primary/secondary outcomes, and site locations for a specific clinical trial by its NCT ID (e.g. 'NCT03548935')."
    ),
)
async def tool_get_trial_details(
    nct_id: Annotated[
        str,
        Field(
            description="ClinicalTrials.gov identifier in 'NCT########' format (e.g., 'NCT03548935')."
        ),
    ],
) -> dict[str, Any]:
    return await execute_tool_by_name(
        "get_trial_details",
        {"nct_id": nct_id},
        api_key_id=current_mcp_api_key_id.get(),
    )


@mcp.tool(
    name="adverse_event_summary",
    description=(
        "Query openFDA FAERS (/drug/event.json) for a drug's top reported MedDRA adverse reactions, "
        "total report counts, and seriousness breakdown (serious vs. non-serious percentages). "
        "Normalizes brand/generic drug names via RxNorm before querying."
    ),
)
async def tool_adverse_event_summary(
    drug: Annotated[
        str,
        Field(
            description="Drug name (brand or generic, e.g. 'semaglutide', 'Ozempic', 'atorvastatin')."
        ),
    ],
    limit: Annotated[
        int,
        Field(
            default=10,
            ge=1,
            le=50,
            description="Maximum number of top MedDRA reaction terms to return (1-50, default 10).",
        ),
    ] = 10,
) -> dict[str, Any]:
    return await execute_tool_by_name(
        "adverse_event_summary",
        {"drug": drug, "limit": limit},
        api_key_id=current_mcp_api_key_id.get(),
    )


@mcp.tool(
    name="drug_label_lookup",
    description=(
        "Retrieve official FDA Structured Product Labeling (/drug/label.json) sections for a drug, "
        "including boxed warnings, warnings and cautions, contraindications, dosage and administration, "
        "indications, and adverse reactions."
    ),
)
async def tool_drug_label_lookup(
    drug: Annotated[
        str,
        Field(description="Drug name (brand or generic, e.g. 'warfarin', 'lisinopril')."),
    ],
    sections: Annotated[
        list[str] | None,
        Field(
            default=None,
            description=(
                "Optional list of label section names to extract (e.g. ['boxed_warning', 'warnings', "
                "'contraindications', 'dosage_and_administration']). Omit for default safety sections."
            ),
        ),
    ] = None,
) -> dict[str, Any]:
    return await execute_tool_by_name(
        "drug_label_lookup",
        {"drug": drug, "sections": sections},
        api_key_id=current_mcp_api_key_id.get(),
    )


@mcp.tool(
    name="literature_search",
    description=(
        "Search peer-reviewed biomedical literature on PubMed via NCBI E-utilities (esearch + efetch) "
        "for a drug and/or clinical condition within a recent publication window, returning PMIDs, "
        "titles, journals, publication dates, DOIs, and abstract snippets."
    ),
)
async def tool_literature_search(
    drug: Annotated[
        str | None,
        Field(
            default=None,
            description="Drug or active ingredient name (e.g. 'pembrolizumab', 'metformin').",
        ),
    ] = None,
    condition: Annotated[
        str | None,
        Field(
            default=None,
            description="Disease, clinical condition, or safety topic (e.g. 'melanoma', 'lactic acidosis').",
        ),
    ] = None,
    years: Annotated[
        int | str | None,
        Field(
            default=5,
            description="Lookback window in years (e.g. 5 for last 5 years, or range '2020-2025').",
        ),
    ] = 5,
    limit: Annotated[
        int,
        Field(
            default=10,
            ge=1,
            le=25,
            description="Maximum number of PubMed articles to return (1-25, default 10).",
        ),
    ] = 10,
) -> dict[str, Any]:
    return await execute_tool_by_name(
        "literature_search",
        {"drug": drug, "condition": condition, "years": years, "limit": limit},
        api_key_id=current_mcp_api_key_id.get(),
    )


@mcp.tool(
    name="drug_safety_brief",
    description=(
        "Compile a comprehensive, compact Drug Safety Brief combining RxNorm drug normalization, "
        "openFDA FAERS adverse event summary, FDA SPL label warnings/contraindications/dosage, "
        "openFDA drug recall enforcement reports, and recent PubMed safety literature in one report."
    ),
)
async def tool_drug_safety_brief(
    drug: Annotated[
        str,
        Field(
            description="Brand or generic drug name to generate a complete safety brief for (e.g. 'metformin', 'Ozempic')."
        ),
    ],
) -> dict[str, Any]:
    return await execute_tool_by_name(
        "drug_safety_brief",
        {"drug": drug},
        api_key_id=current_mcp_api_key_id.get(),
    )
