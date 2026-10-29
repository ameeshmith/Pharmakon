"""openFDA tools: adverse_event_summary, drug_label_lookup, and recall enforcement helper."""

from __future__ import annotations

from typing import Any

from server.config import MEDICAL_DISCLAIMER, get_settings
from server.http_client import UpstreamAPIError, http_client
from server.rxnorm import NormalizedDrug, normalize_drug_name

OPENFDA_BASE_URL = "https://api.fda.gov"

DEFAULT_LABEL_SECTIONS = [
    "boxed_warning",
    "warnings_and_cautions",
    "warnings",
    "contraindications",
    "dosage_and_administration",
    "indications_and_usage",
    "adverse_reactions",
    "drug_interactions",
]


def _with_openfda_key(params: dict[str, Any]) -> dict[str, Any]:
    """Attach api_key query param if OPENFDA_API_KEY is configured."""
    out = dict(params)
    key = get_settings().effective_openfda_key
    if key:
        out["api_key"] = key
    return out


def _clean_snippet(value: Any, max_chars: int = 750) -> str | None:
    if value is None:
        return None
    joined = " ".join(str(v) for v in value if v) if isinstance(value, list) else str(value)
    collapsed = " ".join(joined.split())
    if not collapsed:
        return None
    if len(collapsed) <= max_chars:
        return collapsed
    return collapsed[: max_chars - 3] + "..."


def _build_event_search_query(norm: NormalizedDrug) -> str:
    """Build an openFDA FAERS search query matching generic or input drug name."""
    candidates = {norm.input_name.strip().upper(), norm.normalized_name.strip().upper()}
    for b in norm.brand_names[:3]:
        if b.strip():
            candidates.add(b.strip().upper())
    clauses: list[str] = []
    for term in sorted(c for c in candidates if c):
        safe_term = term.replace('"', "")
        clauses.append(f'patient.drug.medicinalproduct:"{safe_term}"')
        clauses.append(f'patient.drug.openfda.generic_name:"{safe_term}"')
        clauses.append(f'patient.drug.openfda.brand_name:"{safe_term}"')
    return "+OR+".join(clauses) if clauses else f'patient.drug.medicinalproduct:"{norm.input_name}"'


async def adverse_event_summary(drug: str, limit: int = 10) -> dict[str, Any]:
    """Query openFDA FAERS (/drug/event.json) for top reported reactions, report counts, and seriousness breakdown."""
    cleaned_drug = (drug or "").strip()
    if not cleaned_drug:
        return {
            "status": "error",
            "error": "Parameter 'drug' is required.",
            "disclaimer": MEDICAL_DISCLAIMER,
        }

    clamped_limit = max(1, min(int(limit or 10), 50))
    norm = await normalize_drug_name(cleaned_drug)
    search_expr = f'patient.drug.medicinalproduct:"{norm.normalized_name.upper()}"'

    try:
        # 1. Top reactions count
        reactions_resp = await http_client.get_json(
            f"{OPENFDA_BASE_URL}/drug/event.json",
            params=_with_openfda_key(
                {
                    "search": search_expr,
                    "count": "patient.reaction.reactionmeddrapt.exact",
                    "limit": clamped_limit,
                }
            ),
            source="openFDA (drug/event)",
            allow_404_empty=True,
        )

        # Fallback to input name if normalized generic name returned 404/empty
        if (
            not reactions_resp.get("results")
            and norm.normalized_name.lower() != cleaned_drug.lower()
        ):
            search_expr = f'patient.drug.medicinalproduct:"{cleaned_drug.upper()}"'
            reactions_resp = await http_client.get_json(
                f"{OPENFDA_BASE_URL}/drug/event.json",
                params=_with_openfda_key(
                    {
                        "search": search_expr,
                        "count": "patient.reaction.reactionmeddrapt.exact",
                        "limit": clamped_limit,
                    }
                ),
                source="openFDA (drug/event)",
                allow_404_empty=True,
            )

        # 2. Seriousness breakdown (1 = serious, 2 = non-serious)
        serious_resp = await http_client.get_json(
            f"{OPENFDA_BASE_URL}/drug/event.json",
            params=_with_openfda_key(
                {
                    "search": search_expr,
                    "count": "serious",
                }
            ),
            source="openFDA (drug/event)",
            allow_404_empty=True,
        )

        # 3. Seriousness outcome counts (death, hospitalization, life-threatening)
        total_serious_reports = 0
        total_non_serious_reports = 0
        for item in serious_resp.get("results") or []:
            term_val = str(item.get("term", ""))
            cnt = int(item.get("count", 0))
            if term_val == "1":
                total_serious_reports += cnt
            elif term_val == "2":
                total_non_serious_reports += cnt

        total_reports = total_serious_reports + total_non_serious_reports
        raw_reactions = reactions_resp.get("results") or []
        top_reactions: list[dict[str, Any]] = []
        for r in raw_reactions[:clamped_limit]:
            count_val = int(r.get("count", 0))
            pct = round((count_val / total_reports) * 100, 2) if total_reports > 0 else None
            top_reactions.append(
                {
                    "reaction_meddra_pt": r.get("term"),
                    "count": count_val,
                    "percentage_of_reports": pct,
                }
            )

        serious_ratio = (
            round((total_serious_reports / total_reports) * 100, 2) if total_reports > 0 else 0.0
        )

        return {
            "drug": cleaned_drug,
            "normalized_drug": norm.to_dict(),
            "total_reports": total_reports,
            "seriousness": {
                "serious_reports": total_serious_reports,
                "non_serious_reports": total_non_serious_reports,
                "serious_percentage": serious_ratio,
            },
            "top_reactions": top_reactions,
            "source": "openFDA FAERS (/drug/event.json)",
            "disclaimer": MEDICAL_DISCLAIMER,
        }

    except UpstreamAPIError as exc:
        return {
            "status": "upstream_error",
            "drug": cleaned_drug,
            "source": "openFDA FAERS (/drug/event.json)",
            "error": exc.message,
            "disclaimer": MEDICAL_DISCLAIMER,
        }


async def drug_label_lookup(
    drug: str,
    sections: list[str] | None = None,
) -> dict[str, Any]:
    """Query openFDA Structured Product Labeling (/drug/label.json) for warnings, contraindications, dosage, and indications."""
    cleaned_drug = (drug or "").strip()
    if not cleaned_drug:
        return {
            "status": "error",
            "error": "Parameter 'drug' is required.",
            "disclaimer": MEDICAL_DISCLAIMER,
        }

    requested_sections = [
        s.strip().lower() for s in (sections or DEFAULT_LABEL_SECTIONS) if s and s.strip()
    ]
    if not requested_sections:
        requested_sections = list(DEFAULT_LABEL_SECTIONS)

    norm = await normalize_drug_name(cleaned_drug)
    queries_to_try = [
        f'openfda.generic_name:"{norm.normalized_name}"',
        f'openfda.brand_name:"{cleaned_drug}"',
        f'"{cleaned_drug}"',
    ]

    label_record: dict[str, Any] | None = None
    try:
        for q in queries_to_try:
            resp = await http_client.get_json(
                f"{OPENFDA_BASE_URL}/drug/label.json",
                params=_with_openfda_key({"search": q, "limit": 1}),
                source="openFDA (drug/label)",
                allow_404_empty=True,
            )
            results = resp.get("results") or []
            if results and isinstance(results[0], dict):
                label_record = results[0]
                break
    except UpstreamAPIError as exc:
        return {
            "status": "upstream_error",
            "drug": cleaned_drug,
            "source": "openFDA SPL (/drug/label.json)",
            "error": exc.message,
            "disclaimer": MEDICAL_DISCLAIMER,
        }

    if not label_record:
        return {
            "status": "not_found",
            "drug": cleaned_drug,
            "normalized_drug": norm.to_dict(),
            "error": f"No FDA structured product label found for '{cleaned_drug}'.",
            "source": "openFDA SPL (/drug/label.json)",
            "disclaimer": MEDICAL_DISCLAIMER,
        }

    openfda_meta = label_record.get("openfda") or {}
    extracted_sections: dict[str, str | None] = {}
    for sec in requested_sections:
        val = label_record.get(sec)
        # Provide helpful alias fallback between warnings and warnings_and_cautions
        if val is None and sec == "warnings":
            val = label_record.get("warnings_and_cautions")
        elif val is None and sec == "warnings_and_cautions":
            val = label_record.get("warnings")
        elif val is None and sec == "dosage":
            val = label_record.get("dosage_and_administration")
        extracted_sections[sec] = _clean_snippet(val, max_chars=900)

    return {
        "drug": cleaned_drug,
        "normalized_drug": norm.to_dict(),
        "label_metadata": {
            "brand_names": (openfda_meta.get("brand_name") or [])[:5],
            "generic_names": (openfda_meta.get("generic_name") or [])[:5],
            "manufacturer_names": (openfda_meta.get("manufacturer_name") or [])[:3],
            "route": (openfda_meta.get("route") or [])[:3],
            "product_type": (openfda_meta.get("product_type") or [])[:2],
            "effective_time": label_record.get("effective_time"),
            "set_id": label_record.get("set_id"),
        },
        "has_boxed_warning": bool(label_record.get("boxed_warning")),
        "sections": extracted_sections,
        "source": "openFDA Structured Product Labeling (/drug/label.json)",
        "disclaimer": MEDICAL_DISCLAIMER,
    }


async def fetch_drug_enforcement_recalls(
    drug: str,
    normalized_name: str | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """Query openFDA (/drug/enforcement.json) for drug recall enforcement reports."""
    target = (normalized_name or drug or "").strip()
    if not target:
        return {"total_recalls": 0, "recent_recalls": []}

    clamped_limit = max(1, min(limit, 20))
    queries = [
        f'openfda.generic_name:"{target}"',
        f'product_description:"{target}"',
    ]

    try:
        for q in queries:
            resp = await http_client.get_json(
                f"{OPENFDA_BASE_URL}/drug/enforcement.json",
                params=_with_openfda_key(
                    {
                        "search": q,
                        "sort": "report_date:desc",
                        "limit": clamped_limit,
                    }
                ),
                source="openFDA (drug/enforcement)",
                allow_404_empty=True,
            )
            results = resp.get("results") or []
            if results:
                meta_total = (resp.get("meta") or {}).get("results", {}).get("total", len(results))
                recalls = [
                    {
                        "recall_number": item.get("recall_number"),
                        "classification": item.get("classification"),
                        "status": item.get("status"),
                        "recalling_firm": item.get("recalling_firm"),
                        "reason_for_recall": _clean_snippet(item.get("reason_for_recall"), 260),
                        "report_date": item.get("report_date"),
                        "product_description": _clean_snippet(item.get("product_description"), 200),
                    }
                    for item in results[:clamped_limit]
                    if isinstance(item, dict)
                ]
                return {
                    "total_recalls": meta_total,
                    "recent_recalls": recalls,
                }
    except UpstreamAPIError as exc:
        return {
            "total_recalls": 0,
            "recent_recalls": [],
            "error": exc.message,
        }

    return {"total_recalls": 0, "recent_recalls": []}
