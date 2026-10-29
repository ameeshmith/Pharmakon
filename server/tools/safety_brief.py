"""Composite drug_safety_brief tool combining openFDA FAERS, SPL Labels, Enforcement Recalls, and PubMed."""

from __future__ import annotations

import asyncio
from typing import Any

from server.config import MEDICAL_DISCLAIMER
from server.rxnorm import normalize_drug_name
from server.tools.openfda import (
    adverse_event_summary,
    drug_label_lookup,
    fetch_drug_enforcement_recalls,
)
from server.tools.pubmed import literature_search


async def drug_safety_brief(drug: str) -> dict[str, Any]:
    """Generate a compact, multi-source drug safety brief combining FAERS adverse events, FDA labeling, recalls, and PubMed literature."""
    cleaned_drug = (drug or "").strip()
    if not cleaned_drug:
        return {
            "status": "error",
            "error": "Parameter 'drug' is required.",
            "disclaimer": MEDICAL_DISCLAIMER,
        }

    norm = await normalize_drug_name(cleaned_drug)
    canonical_drug = norm.normalized_name or cleaned_drug

    events_task = adverse_event_summary(drug=cleaned_drug, limit=8)
    label_task = drug_label_lookup(
        drug=cleaned_drug,
        sections=[
            "boxed_warning",
            "warnings_and_cautions",
            "contraindications",
            "dosage_and_administration",
            "adverse_reactions",
        ],
    )
    lit_task = literature_search(
        drug=canonical_drug,
        condition="adverse effects OR safety",
        years=5,
        limit=5,
    )
    recalls_task = fetch_drug_enforcement_recalls(
        drug=cleaned_drug,
        normalized_name=canonical_drug,
        limit=5,
    )

    events_res, label_res, lit_res, recalls_res = await asyncio.gather(
        events_task, label_task, lit_task, recalls_task
    )

    return {
        "drug": cleaned_drug,
        "normalized_drug": norm.to_dict(),
        "adverse_events": {
            "total_reports": events_res.get("total_reports", 0),
            "seriousness": events_res.get("seriousness", {}),
            "top_reactions": events_res.get("top_reactions", []),
            "status": events_res.get("status", "ok"),
        },
        "fda_label": {
            "has_boxed_warning": label_res.get("has_boxed_warning", False),
            "metadata": label_res.get("label_metadata", {}),
            "sections": label_res.get("sections", {}),
            "status": label_res.get("status", "ok"),
        },
        "recall_enforcement": recalls_res,
        "recent_literature": {
            "total_matching_articles": lit_res.get("total_count", 0),
            "articles": lit_res.get("articles", []),
            "status": lit_res.get("status", "ok"),
        },
        "sources": [
            "RxNorm REST API",
            "openFDA FAERS (/drug/event.json)",
            "openFDA SPL (/drug/label.json)",
            "openFDA Recall Enforcement (/drug/enforcement.json)",
            "NCBI PubMed E-utilities",
        ],
        "disclaimer": MEDICAL_DISCLAIMER,
    }
