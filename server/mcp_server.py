"""FastMCP server instance and MCP tool registrations over Streamable HTTP."""

from __future__ import annotations

from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from server.tools.trials import (
    get_trial_details as _get_trial_details,
)
from server.tools.trials import (
    search_trials as _search_trials,
)

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
    return await _search_trials(
        condition=condition,
        drug=drug,
        phase=phase,
        status=status,
        location=location,
        limit=limit,
    )


@mcp.tool(
    name="get_trial_details",
    description=(
        "Retrieve comprehensive protocol, eligibility criteria, study arms, interventions, "
        "primary/secondary outcomes, and site locations for a specific clinical trial by its NCT ID (e.g. 'NCT04280705')."
    ),
)
async def tool_get_trial_details(
    nct_id: Annotated[
        str,
        Field(
            description="ClinicalTrials.gov identifier in 'NCT########' format (e.g., 'NCT04280705')."
        ),
    ],
) -> dict[str, Any]:
    return await _get_trial_details(nct_id=nct_id)
