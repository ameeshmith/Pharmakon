"""Phase 1 Tests: ClinicalTrials.gov tools, RxNorm normalization, caching, secret redaction, and FastAPI/MCP server."""

from __future__ import annotations

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from server.config import MEDICAL_DISCLAIMER
from server.http_client import http_client
from server.logging_utils import sanitize_text
from server.main import app
from server.mcp_server import mcp
from server.tools.trials import get_trial_details, search_trials
from tests.fixtures.clinical_trials_fixtures import (
    CT_SEARCH_RESPONSE,
    CT_STUDY_DETAIL_NCT03548935,
    RXNORM_PROPERTIES_OZEMPIC,
    RXNORM_RELATED_OZEMPIC,
    RXNORM_RXCUI_OZEMPIC,
)


@respx.mock
@pytest.mark.asyncio
async def test_search_trials_end_to_end() -> None:
    """Verify search_trials normalizes brand name via RxNorm and queries ClinicalTrials.gov API v2."""
    respx.get("https://rxnav.nlm.nih.gov/REST/rxcui.json").mock(
        return_value=httpx.Response(200, json=RXNORM_RXCUI_OZEMPIC)
    )
    respx.get("https://rxnav.nlm.nih.gov/REST/rxcui/1991302/properties.json").mock(
        return_value=httpx.Response(200, json=RXNORM_PROPERTIES_OZEMPIC)
    )
    respx.get("https://rxnav.nlm.nih.gov/REST/rxcui/1991302/related.json").mock(
        return_value=httpx.Response(200, json=RXNORM_RELATED_OZEMPIC)
    )
    ct_route = respx.get("https://clinicaltrials.gov/api/v2/studies").mock(
        return_value=httpx.Response(200, json=CT_SEARCH_RESPONSE)
    )

    result = await search_trials(
        condition="obesity",
        drug="Ozempic",
        phase="Phase 3",
        status="completed",
        location="United States",
        limit=5,
    )

    assert ct_route.called
    assert result["total_count"] == 2
    assert result["returned_count"] == 2
    assert result["query"]["normalized_drug"]["normalized_name"] == "semaglutide"
    assert result["query"]["normalized_drug"]["rxcui"] == "1991302"
    assert result["query"]["phase"] == "PHASE3"
    assert result["query"]["status"] == "COMPLETED"
    assert result["trials"][0]["nct_id"] == "NCT03548935"
    assert result["trials"][0]["lead_sponsor"] == "Novo Nordisk A/S"
    assert result["disclaimer"] == MEDICAL_DISCLAIMER


@pytest.mark.asyncio
async def test_search_trials_requires_at_least_one_filter() -> None:
    """Verify search_trials rejects empty queries cleanly."""
    result = await search_trials()
    assert result["status"] == "error"
    assert "at least one filter" in result["error"].lower()
    assert result["disclaimer"] == MEDICAL_DISCLAIMER


@respx.mock
@pytest.mark.asyncio
async def test_get_trial_details_end_to_end() -> None:
    """Verify get_trial_details fetches study protocol, eligibility, and outcomes by NCT ID."""
    respx.get("https://clinicaltrials.gov/api/v2/studies/NCT03548935").mock(
        return_value=httpx.Response(200, json=CT_STUDY_DETAIL_NCT03548935)
    )

    result = await get_trial_details("nct03548935")
    assert result["nct_id"] == "NCT03548935"
    assert result["overall_status"] == "COMPLETED"
    assert result["enrollment"] == 1961
    assert "PHASE3" in result["phases"]
    assert result["eligibility"]["minimum_age"] == "18 Years"
    assert len(result["primary_outcomes"]) == 2
    assert result["has_results"] is True
    assert result["disclaimer"] == MEDICAL_DISCLAIMER


@pytest.mark.asyncio
async def test_get_trial_details_invalid_nct_id() -> None:
    """Verify get_trial_details validates NCT ID format."""
    result = await get_trial_details("INVALID-123")
    assert result["status"] == "error"
    assert "Invalid NCT ID" in result["error"]
    assert result["disclaimer"] == MEDICAL_DISCLAIMER


@respx.mock
@pytest.mark.asyncio
async def test_http_client_caching_and_secret_redaction() -> None:
    """Verify upstream responses are cached and OPENFDA_API_KEY is scrubbed from logs/errors."""
    route = respx.get("https://clinicaltrials.gov/api/v2/studies/NCT03548935").mock(
        return_value=httpx.Response(200, json=CT_STUDY_DETAIL_NCT03548935)
    )

    await get_trial_details("NCT03548935")
    await get_trial_details("NCT03548935")
    assert route.call_count == 1
    assert http_client.stats["hits"] >= 1

    leaked_url = (
        "https://api.fda.gov/drug/event.json?api_key=test_secret_openfda_key_999999&limit=5"
    )
    cleaned = sanitize_text(leaked_url)
    assert "test_secret_openfda_key_999999" not in cleaned
    assert "api_key=[REDACTED]" in cleaned


@pytest.mark.asyncio
async def test_health_and_mcp_registered_tools() -> None:
    """Verify FastAPI /health endpoint and FastMCP tool registrations."""
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["mcp_transport"] == "streamable-http"

    tools = await mcp.list_tools()
    tool_names = {t.name for t in tools} if isinstance(tools, list) else set(tools.keys())
    assert "search_trials" in tool_names
    assert "get_trial_details" in tool_names
