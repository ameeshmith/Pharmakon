"""Phase 2 Tests: openFDA & PubMed tools, drug_safety_brief, JWT auth, hashed API keys, rate limiting (429 + Retry-After), and usage logging."""

from __future__ import annotations

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from server.config import MEDICAL_DISCLAIMER, get_settings
from server.main import app
from server.mcp_server import mcp
from server.tools.openfda import adverse_event_summary, drug_label_lookup
from server.tools.pubmed import literature_search
from server.tools.safety_brief import drug_safety_brief
from tests.fixtures.clinical_trials_fixtures import (
    RXNORM_PROPERTIES_OZEMPIC,
    RXNORM_RELATED_OZEMPIC,
    RXNORM_RXCUI_OZEMPIC,
)
from tests.fixtures.openfda_pubmed_fixtures import (
    OPENFDA_ENFORCEMENT_SEMAGLUTIDE,
    OPENFDA_EVENT_REACTIONS_SEMAGLUTIDE,
    OPENFDA_EVENT_SERIOUS_SEMAGLUTIDE,
    OPENFDA_LABEL_SEMAGLUTIDE,
    PUBMED_EFETCH_XML,
    PUBMED_ESEARCH_RESPONSE,
)


def _mock_rxnorm_ozempic() -> None:
    respx.get("https://rxnav.nlm.nih.gov/REST/rxcui.json").mock(
        return_value=httpx.Response(200, json=RXNORM_RXCUI_OZEMPIC)
    )
    respx.get("https://rxnav.nlm.nih.gov/REST/rxcui/1991302/properties.json").mock(
        return_value=httpx.Response(200, json=RXNORM_PROPERTIES_OZEMPIC)
    )
    respx.get("https://rxnav.nlm.nih.gov/REST/rxcui/1991302/related.json").mock(
        return_value=httpx.Response(200, json=RXNORM_RELATED_OZEMPIC)
    )


def _mock_openfda_and_pubmed() -> None:
    _mock_rxnorm_ozempic()

    def event_side_effect(request: httpx.Request) -> httpx.Response:
        count_param = request.url.params.get("count", "")
        if "reactionmeddrapt" in count_param:
            return httpx.Response(200, json=OPENFDA_EVENT_REACTIONS_SEMAGLUTIDE)
        if count_param == "serious":
            return httpx.Response(200, json=OPENFDA_EVENT_SERIOUS_SEMAGLUTIDE)
        return httpx.Response(200, json={"results": []})

    respx.get("https://api.fda.gov/drug/event.json").mock(side_effect=event_side_effect)
    respx.get("https://api.fda.gov/drug/label.json").mock(
        return_value=httpx.Response(200, json=OPENFDA_LABEL_SEMAGLUTIDE)
    )
    respx.get("https://api.fda.gov/drug/enforcement.json").mock(
        return_value=httpx.Response(200, json=OPENFDA_ENFORCEMENT_SEMAGLUTIDE)
    )
    respx.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi").mock(
        return_value=httpx.Response(200, json=PUBMED_ESEARCH_RESPONSE)
    )
    respx.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi").mock(
        return_value=httpx.Response(
            200,
            text=PUBMED_EFETCH_XML,
            headers={"content-type": "text/xml"},
        )
    )


@respx.mock
@pytest.mark.asyncio
async def test_adverse_event_summary_tool() -> None:
    """Verify adverse_event_summary aggregates FAERS top reactions and seriousness ratios."""
    _mock_openfda_and_pubmed()
    res = await adverse_event_summary("Ozempic", limit=5)

    assert res["normalized_drug"]["normalized_name"] == "semaglutide"
    assert res["total_reports"] == 31000
    assert res["seriousness"]["serious_reports"] == 12400
    assert res["seriousness"]["non_serious_reports"] == 18600
    assert res["seriousness"]["serious_percentage"] == 40.0
    assert res["top_reactions"][0]["reaction_meddra_pt"] == "NAUSEA"
    assert res["top_reactions"][0]["count"] == 8420
    assert res["disclaimer"] == MEDICAL_DISCLAIMER


@respx.mock
@pytest.mark.asyncio
async def test_drug_label_lookup_tool() -> None:
    """Verify drug_label_lookup extracts boxed warning, warnings, contraindications, and dosage."""
    _mock_openfda_and_pubmed()
    res = await drug_label_lookup(
        "Ozempic",
        sections=[
            "boxed_warning",
            "warnings",
            "contraindications",
            "dosage_and_administration",
        ],
    )

    assert res["has_boxed_warning"] is True
    assert "THYROID C-CELL TUMORS" in (res["sections"]["boxed_warning"] or "")
    assert "Pancreatitis" in (res["sections"]["warnings"] or "")
    assert "medullary thyroid carcinoma" in (res["sections"]["contraindications"] or "")
    assert "0.25 mg once weekly" in (res["sections"]["dosage_and_administration"] or "")
    assert res["disclaimer"] == MEDICAL_DISCLAIMER


@respx.mock
@pytest.mark.asyncio
async def test_literature_search_tool() -> None:
    """Verify literature_search calls PubMed esearch + efetch and parses XML articles."""
    _mock_openfda_and_pubmed()
    res = await literature_search(drug="semaglutide", condition="obesity", years=5, limit=5)

    assert res["total_count"] == 142
    assert res["returned_count"] == 2
    assert res["articles"][0]["pmid"] == "33567185"
    assert "Once-Weekly Semaglutide" in res["articles"][0]["title"]
    assert res["articles"][0]["doi"] == "10.1056/NEJMoa2032183"
    assert "Wilding JPH" in res["articles"][0]["authors"]
    assert res["disclaimer"] == MEDICAL_DISCLAIMER


@respx.mock
@pytest.mark.asyncio
async def test_drug_safety_brief_tool() -> None:
    """Verify drug_safety_brief combines FAERS events, SPL label, Enforcement recalls, and PubMed."""
    _mock_openfda_and_pubmed()
    res = await drug_safety_brief("Ozempic")

    assert res["normalized_drug"]["normalized_name"] == "semaglutide"
    assert res["adverse_events"]["total_reports"] == 31000
    assert res["fda_label"]["has_boxed_warning"] is True
    assert res["recall_enforcement"]["total_recalls"] == 1
    assert res["recall_enforcement"]["recent_recalls"][0]["recall_number"] == "D-0192-2024"
    assert len(res["recent_literature"]["articles"]) == 2
    assert res["disclaimer"] == MEDICAL_DISCLAIMER


@pytest.mark.asyncio
async def test_all_six_tools_registered_on_mcp() -> None:
    """Verify all 6 MCP tools are registered on the FastMCP server."""
    tools = await mcp.list_tools()
    tool_names = {t.name for t in tools}
    assert tool_names == {
        "search_trials",
        "get_trial_details",
        "adverse_event_summary",
        "drug_label_lookup",
        "literature_search",
        "drug_safety_brief",
    }


@respx.mock
def test_auth_keys_usage_and_rate_limiting(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify user signup/login, hashed API key creation/revocation, MCP auth, 429 rate limiting, and usage stats."""
    _mock_openfda_and_pubmed()
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "3")
    get_settings.cache_clear()

    with TestClient(app) as client:
        # 1. Signup
        signup_resp = client.post(
            "/api/auth/signup",
            json={"email": "researcher@pharmakon.dev", "password": "StrongPassword123!"},
        )
        assert signup_resp.status_code == 201
        jwt_token = signup_resp.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {jwt_token}"}

        # 2. Duplicate signup rejected
        dup_resp = client.post(
            "/api/auth/signup",
            json={"email": "researcher@pharmakon.dev", "password": "StrongPassword123!"},
        )
        assert dup_resp.status_code == 409

        # 3. Login & /api/auth/me
        login_resp = client.post(
            "/api/auth/login",
            json={"email": "researcher@pharmakon.dev", "password": "StrongPassword123!"},
        )
        assert login_resp.status_code == 200
        me_resp = client.get("/api/auth/me", headers=auth_headers)
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == "researcher@pharmakon.dev"

        # 4. Create API key (plaintext returned once; list endpoint only returns prefix)
        key_resp = client.post(
            "/api/keys",
            json={"name": "Claude Desktop Key"},
            headers=auth_headers,
        )
        assert key_resp.status_code == 201
        key_data = key_resp.json()
        raw_api_key = key_data["raw_key"]
        key_id = key_data["id"]
        assert raw_api_key.startswith("pk_live_")

        list_resp = client.get("/api/keys", headers=auth_headers)
        assert list_resp.status_code == 200
        listed_key = list_resp.json()["keys"][0]
        assert "raw_key" not in listed_key
        assert "key_hash" not in listed_key
        assert listed_key["key_prefix"].startswith("pk_live_")

        # 5. /mcp requires Bearer API key
        unauth_mcp = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "ping"})
        assert unauth_mcp.status_code == 401

        # 6. Playground execution using API key & rate limiting (limit = 3 req/min)
        key_headers = {"Authorization": f"Bearer {raw_api_key}"}
        for i in range(3):
            run_resp = client.post(
                "/api/playground/run",
                json={
                    "tool": "adverse_event_summary",
                    "arguments": {"drug": "Ozempic", "limit": 5},
                },
                headers=key_headers,
            )
            assert run_resp.status_code == 200, f"Call {i + 1} failed"
            assert "X-RateLimit-Remaining-Minute" in run_resp.headers

        # 4th call within the same minute must return 429 with Retry-After header
        limited_resp = client.post(
            "/api/playground/run",
            json={"tool": "adverse_event_summary", "arguments": {"drug": "Ozempic", "limit": 5}},
            headers=key_headers,
        )
        assert limited_resp.status_code == 429
        assert "Retry-After" in limited_resp.headers
        assert int(limited_resp.headers["Retry-After"]) >= 1

        # 7. Usage stats reflect the 3 executed tool calls
        stats_resp = client.get("/api/usage/stats", headers=auth_headers)
        assert stats_resp.status_code == 200
        stats = stats_resp.json()
        assert stats["total_calls"] == 3
        assert stats["by_tool"][0]["tool"] == "adverse_event_summary"
        assert stats["by_tool"][0]["count"] == 3

        # 8. Revoke API key -> subsequent calls with that key fail with 401
        revoke_resp = client.delete(f"/api/keys/{key_id}", headers=auth_headers)
        assert revoke_resp.status_code == 200
        assert revoke_resp.json()["is_active"] is False

        revoked_call = client.post(
            "/api/playground/run",
            json={"tool": "adverse_event_summary", "arguments": {"drug": "Ozempic"}},
            headers=key_headers,
        )
        assert revoked_call.status_code == 401
