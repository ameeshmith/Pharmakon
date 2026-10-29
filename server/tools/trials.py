"""ClinicalTrials.gov API v2 tools: search_trials and get_trial_details."""

from __future__ import annotations

import re
from typing import Any

from server.config import MEDICAL_DISCLAIMER
from server.http_client import UpstreamAPIError, http_client
from server.rxnorm import normalize_drug_name

CLINICAL_TRIALS_BASE_URL = "https://clinicaltrials.gov/api/v2"

_VALID_STATUSES = {
    "RECRUITING",
    "NOT_YET_RECRUITING",
    "ACTIVE_NOT_RECRUITING",
    "ENROLLING_BY_INVITATION",
    "COMPLETED",
    "SUSPENDED",
    "TERMINATED",
    "WITHDRAWN",
}

_PHASE_MAP = {
    "1": "PHASE1",
    "PHASE1": "PHASE1",
    "PHASE 1": "PHASE1",
    "EARLY_PHASE1": "EARLY_PHASE1",
    "EARLY PHASE 1": "EARLY_PHASE1",
    "0": "EARLY_PHASE1",
    "2": "PHASE2",
    "PHASE2": "PHASE2",
    "PHASE 2": "PHASE2",
    "3": "PHASE3",
    "PHASE3": "PHASE3",
    "PHASE 3": "PHASE3",
    "4": "PHASE4",
    "PHASE4": "PHASE4",
    "PHASE 4": "PHASE4",
    "NA": "NA",
}

_SEARCH_FIELDS = (
    "NCTId,BriefTitle,OverallStatus,Phase,StartDate,CompletionDate,"
    "EnrollmentCount,ConditionsModule,ArmsInterventionsModule,LeadSponsorName,LocationFacility"
)

_NCT_RE = re.compile(r"^NCT\d{8}$", re.IGNORECASE)


def _normalize_phase(phase: str | None) -> str | None:
    if not phase:
        return None
    key = phase.strip().upper().replace("-", " ")
    return _PHASE_MAP.get(key, key)


def _normalize_status(status: str | None) -> str | None:
    if not status:
        return None
    norm = status.strip().upper().replace(" ", "_").replace("-", "_")
    if norm in _VALID_STATUSES:
        return norm
    return norm


def _truncate(text: str | None, max_len: int = 500) -> str | None:
    if not text:
        return None
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 3] + "..."


async def search_trials(
    condition: str | None = None,
    drug: str | None = None,
    phase: str | None = None,
    status: str | None = None,
    location: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Search ClinicalTrials.gov (API v2) for clinical studies by condition, drug, phase, status, or location.

    Returns a compact, structured list of matching trials with NCT IDs, titles, status, phases,
    conditions, interventions, sponsor, and sample locations.
    """
    clamped_limit = max(1, min(int(limit or 10), 50))
    if not any([condition, drug, phase, status, location]):
        return {
            "status": "error",
            "error": "Provide at least one filter (condition, drug, phase, status, or location).",
            "disclaimer": MEDICAL_DISCLAIMER,
        }

    normalized_drug_info = None
    drug_query = None
    if drug and drug.strip():
        normalized_drug_info = await normalize_drug_name(drug)
        drug_query = normalized_drug_info.normalized_name or drug.strip()

    params: dict[str, Any] = {
        "fields": _SEARCH_FIELDS,
        "pageSize": clamped_limit,
        "countTotal": "true",
    }
    if condition and condition.strip():
        params["query.cond"] = condition.strip()
    if drug_query:
        params["query.intr"] = drug_query
    if location and location.strip():
        params["query.locn"] = location.strip()

    norm_status = _normalize_status(status)
    if norm_status:
        params["filter.overallStatus"] = norm_status

    norm_phase = _normalize_phase(phase)
    if norm_phase:
        params["filter.advanced"] = f"AREA[Phase]{norm_phase}"

    try:
        data = await http_client.get_json(
            f"{CLINICAL_TRIALS_BASE_URL}/studies",
            params=params,
            source="ClinicalTrials.gov",
        )
    except UpstreamAPIError as exc:
        return {
            "status": "upstream_error",
            "source": "ClinicalTrials.gov",
            "error": exc.message,
            "disclaimer": MEDICAL_DISCLAIMER,
        }

    raw_studies = data.get("studies") or []
    trials: list[dict[str, Any]] = []
    for study in raw_studies[:clamped_limit]:
        proto = study.get("protocolSection") or {}
        id_mod = proto.get("identificationModule") or {}
        status_mod = proto.get("statusModule") or {}
        design_mod = proto.get("designModule") or {}
        cond_mod = proto.get("conditionsModule") or {}
        arms_mod = proto.get("armsInterventionsModule") or {}
        sponsor_mod = proto.get("sponsorCollaboratorsModule") or {}
        loc_mod = proto.get("contactsLocationsModule") or {}

        interventions = [
            f"{i.get('type', 'OTHER')}: {i.get('name', '')}".strip(": ")
            for i in (arms_mod.get("interventions") or [])[:5]
            if isinstance(i, dict) and i.get("name")
        ]

        locations = []
        for loc in (loc_mod.get("locations") or [])[:3]:
            if isinstance(loc, dict):
                parts = [p for p in (loc.get("facility"), loc.get("city"), loc.get("country")) if p]
                if parts:
                    locations.append(", ".join(parts))

        nct_id = id_mod.get("nctId", "")
        trials.append(
            {
                "nct_id": nct_id,
                "title": id_mod.get("briefTitle") or id_mod.get("officialTitle") or "",
                "overall_status": status_mod.get("overallStatus", "UNKNOWN"),
                "phases": design_mod.get("phases") or [],
                "enrollment": (design_mod.get("enrollmentInfo") or {}).get("count"),
                "start_date": (status_mod.get("startDateStruct") or {}).get("date"),
                "completion_date": (status_mod.get("completionDateStruct") or {}).get("date"),
                "conditions": (cond_mod.get("conditions") or [])[:5],
                "interventions": interventions,
                "lead_sponsor": (sponsor_mod.get("leadSponsor") or {}).get("name"),
                "sample_locations": locations,
                "url": f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else None,
            }
        )

    return {
        "query": {
            "condition": condition,
            "drug": drug,
            "normalized_drug": normalized_drug_info.to_dict() if normalized_drug_info else None,
            "phase": norm_phase,
            "status": norm_status,
            "location": location,
            "limit": clamped_limit,
        },
        "total_count": data.get("totalCount", len(trials)),
        "returned_count": len(trials),
        "trials": trials,
        "source": "ClinicalTrials.gov API v2",
        "disclaimer": MEDICAL_DISCLAIMER,
    }


async def get_trial_details(nct_id: str) -> dict[str, Any]:
    """Retrieve comprehensive protocol, eligibility, arms, and outcome details for a single clinical trial by NCT ID (e.g. NCT04280705)."""
    cleaned_id = (nct_id or "").strip().upper()
    if not _NCT_RE.match(cleaned_id):
        return {
            "status": "error",
            "error": f"Invalid NCT ID '{nct_id}'. Expected format 'NCT' followed by 8 digits (e.g. NCT04280705).",
            "disclaimer": MEDICAL_DISCLAIMER,
        }

    try:
        study = await http_client.get_json(
            f"{CLINICAL_TRIALS_BASE_URL}/studies/{cleaned_id}",
            source="ClinicalTrials.gov",
            allow_404_empty=True,
        )
    except UpstreamAPIError as exc:
        return {
            "status": "upstream_error",
            "source": "ClinicalTrials.gov",
            "nct_id": cleaned_id,
            "error": exc.message,
            "disclaimer": MEDICAL_DISCLAIMER,
        }

    if not study or "protocolSection" not in study:
        return {
            "status": "not_found",
            "nct_id": cleaned_id,
            "error": f"No clinical trial found for NCT ID '{cleaned_id}'.",
            "disclaimer": MEDICAL_DISCLAIMER,
        }

    proto = study.get("protocolSection") or {}
    id_mod = proto.get("identificationModule") or {}
    status_mod = proto.get("statusModule") or {}
    desc_mod = proto.get("descriptionModule") or {}
    cond_mod = proto.get("conditionsModule") or {}
    design_mod = proto.get("designModule") or {}
    arms_mod = proto.get("armsInterventionsModule") or {}
    outcomes_mod = proto.get("outcomesModule") or {}
    elig_mod = proto.get("eligibilityModule") or {}
    sponsor_mod = proto.get("sponsorCollaboratorsModule") or {}
    loc_mod = proto.get("contactsLocationsModule") or {}

    interventions = [
        {
            "type": item.get("type"),
            "name": item.get("name"),
            "description": _truncate(item.get("description"), 240),
        }
        for item in (arms_mod.get("interventions") or [])[:8]
        if isinstance(item, dict)
    ]

    primary_outcomes = [
        {
            "measure": item.get("measure"),
            "time_frame": item.get("timeFrame"),
            "description": _truncate(item.get("description"), 220),
        }
        for item in (outcomes_mod.get("primaryOutcomes") or [])[:5]
        if isinstance(item, dict)
    ]

    secondary_outcomes = [
        {
            "measure": item.get("measure"),
            "time_frame": item.get("timeFrame"),
        }
        for item in (outcomes_mod.get("secondaryOutcomes") or [])[:5]
        if isinstance(item, dict)
    ]

    locations = [
        {
            "facility": loc.get("facility"),
            "city": loc.get("city"),
            "state": loc.get("state"),
            "country": loc.get("country"),
            "status": loc.get("status"),
        }
        for loc in (loc_mod.get("locations") or [])[:8]
        if isinstance(loc, dict)
    ]

    return {
        "nct_id": id_mod.get("nctId", cleaned_id),
        "brief_title": id_mod.get("briefTitle"),
        "official_title": id_mod.get("officialTitle"),
        "overall_status": status_mod.get("overallStatus"),
        "study_type": design_mod.get("studyType"),
        "phases": design_mod.get("phases") or [],
        "enrollment": (design_mod.get("enrollmentInfo") or {}).get("count"),
        "dates": {
            "start_date": (status_mod.get("startDateStruct") or {}).get("date"),
            "primary_completion_date": (status_mod.get("primaryCompletionDateStruct") or {}).get(
                "date"
            ),
            "completion_date": (status_mod.get("completionDateStruct") or {}).get("date"),
            "last_update_posted": (status_mod.get("lastUpdatePostDateStruct") or {}).get("date"),
        },
        "lead_sponsor": (sponsor_mod.get("leadSponsor") or {}).get("name"),
        "conditions": cond_mod.get("conditions") or [],
        "brief_summary": _truncate(desc_mod.get("briefSummary"), 900),
        "interventions": interventions,
        "eligibility": {
            "sex": elig_mod.get("sex"),
            "minimum_age": elig_mod.get("minimumAge"),
            "maximum_age": elig_mod.get("maximumAge"),
            "healthy_volunteers": elig_mod.get("healthyVolunteers"),
            "std_ages": elig_mod.get("stdAges") or [],
            "criteria_snippet": _truncate(elig_mod.get("eligibilityCriteria"), 900),
        },
        "primary_outcomes": primary_outcomes,
        "secondary_outcomes": secondary_outcomes,
        "locations": locations,
        "has_results": bool(study.get("hasResults", False)),
        "url": f"https://clinicaltrials.gov/study/{cleaned_id}",
        "source": "ClinicalTrials.gov API v2",
        "disclaimer": MEDICAL_DISCLAIMER,
    }
