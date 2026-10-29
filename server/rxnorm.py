"""RxNorm drug name normalization service using NLM RxNav REST API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from server.http_client import UpstreamAPIError, http_client

RXNORM_BASE_URL = "https://rxnav.nlm.nih.gov/REST"


@dataclass
class NormalizedDrug:
    """Normalized drug identity resolved from RxNorm."""

    input_name: str
    normalized_name: str
    rxcui: str | None = None
    generic_name: str | None = None
    brand_names: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_name": self.input_name,
            "normalized_name": self.normalized_name,
            "rxcui": self.rxcui,
            "generic_name": self.generic_name,
            "brand_names": self.brand_names[:5],
        }


async def normalize_drug_name(drug: str) -> NormalizedDrug:
    """Resolve a drug string to its RxNorm RxCUI, generic ingredient (IN), and brand names (BN).

    Official endpoints used:
    - GET https://rxnav.nlm.nih.gov/REST/rxcui.json?name={drug}&search=2
    - GET https://rxnav.nlm.nih.gov/REST/approximateTerm.json?term={drug}&maxEntries=1 (fallback)
    - GET https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/properties.json
    - GET https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/related.json?tty=IN+BN
    """
    cleaned = (drug or "").strip()
    if not cleaned:
        return NormalizedDrug(input_name="", normalized_name="")

    rxcui: str | None = None
    try:
        # 1. Exact/normalized lookup (search=2 performs exact + normalized string search)
        rxcui_data = await http_client.get_json(
            f"{RXNORM_BASE_URL}/rxcui.json",
            params={"name": cleaned, "search": 2},
            source="RxNorm",
            allow_404_empty=True,
        )
        id_group = rxcui_data.get("idGroup", {})
        rxnorm_ids = id_group.get("rxnormId")
        if isinstance(rxnorm_ids, list) and rxnorm_ids:
            rxcui = str(rxnorm_ids[0])

        # 2. Fallback to approximateTerm if exact/normalized lookup found nothing
        if not rxcui:
            approx_data = await http_client.get_json(
                f"{RXNORM_BASE_URL}/approximateTerm.json",
                params={"term": cleaned, "maxEntries": 1},
                source="RxNorm",
                allow_404_empty=True,
            )
            candidates = approx_data.get("approximateGroup", {}).get("candidate") or []
            if isinstance(candidates, dict):
                candidates = [candidates]
            if candidates and isinstance(candidates[0], dict):
                rxcui = candidates[0].get("rxcui")

        if not rxcui:
            return NormalizedDrug(
                input_name=cleaned,
                normalized_name=cleaned.lower(),
                generic_name=cleaned.lower(),
            )

        # 3. Fetch concept properties and related Ingredient (IN) + Brand Names (BN)
        prop_data = await http_client.get_json(
            f"{RXNORM_BASE_URL}/rxcui/{rxcui}/properties.json",
            source="RxNorm",
            allow_404_empty=True,
        )
        props = prop_data.get("properties") or {}
        concept_name = str(props.get("name") or cleaned).strip()

        related_data = await http_client.get_json(
            f"{RXNORM_BASE_URL}/rxcui/{rxcui}/related.json",
            params={"tty": "IN BN"},
            source="RxNorm",
            allow_404_empty=True,
        )
        concept_groups = related_data.get("relatedGroup", {}).get("conceptGroup") or []
        if isinstance(concept_groups, dict):
            concept_groups = [concept_groups]

        ingredients: list[str] = []
        brands: list[str] = []
        for group in concept_groups:
            tty = group.get("tty")
            concepts = group.get("conceptProperties") or []
            if isinstance(concepts, dict):
                concepts = [concepts]
            for c in concepts:
                c_name = str(c.get("name") or "").strip()
                if not c_name:
                    continue
                if tty == "IN":
                    ingredients.append(c_name.lower())
                elif tty == "BN":
                    brands.append(c_name)

        generic = ingredients[0] if ingredients else concept_name.lower()
        return NormalizedDrug(
            input_name=cleaned,
            normalized_name=generic,
            rxcui=rxcui,
            generic_name=generic,
            brand_names=sorted(set(brands))[:5],
        )

    except UpstreamAPIError:
        # Graceful degradation if RxNorm is unreachable
        return NormalizedDrug(
            input_name=cleaned,
            normalized_name=cleaned.lower(),
            generic_name=cleaned.lower(),
        )
