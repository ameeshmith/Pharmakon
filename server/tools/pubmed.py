"""PubMed E-utilities tool: literature_search (esearch.fcgi + efetch.fcgi)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from typing import Any

from server.config import MEDICAL_DISCLAIMER, get_settings
from server.http_client import UpstreamAPIError, http_client
from server.rxnorm import normalize_drug_name

EUTILS_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def _ncbi_common_params() -> dict[str, Any]:
    settings = get_settings()
    params: dict[str, Any] = {
        "tool": "pharmakon_mcp",
    }
    if settings.ncbi_email:
        params["email"] = settings.ncbi_email
    if settings.ncbi_api_key:
        params["api_key"] = settings.ncbi_api_key
    return params


def _build_date_clause(years: int | str | None) -> str | None:
    """Convert a `years` filter (e.g. 5 or '2020-2025' or '2022') into a PubMed [dp] filter."""
    if years is None:
        return None
    raw = str(years).strip()
    if not raw:
        return None
    current_year = datetime.now(UTC).year
    if raw.isdigit():
        val = int(raw)
        if 1 <= val <= 50:
            start_yr = current_year - val
            return f"{start_yr}:{current_year}[dp]"
        if 1900 <= val <= current_year + 1:
            return f"{val}:{val}[dp]"
    if "-" in raw:
        parts = [p.strip() for p in raw.split("-", 1)]
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            return f"{parts[0]}:{parts[1]}[dp]"
    return None


def _parse_pubmed_xml(xml_text: str) -> list[dict[str, Any]]:
    """Parse PubMed efetch XML into compact article summaries."""
    if not xml_text.strip():
        return []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    articles: list[dict[str, Any]] = []
    for pubmed_article in root.iter("PubmedArticle"):
        pmid_elem = pubmed_article.find(".//PMID")
        art_elem = pubmed_article.find(".//Article")
        if pmid_elem is None or art_elem is None or not pmid_elem.text:
            continue

        pmid = pmid_elem.text.strip()
        title_elem = art_elem.find("ArticleTitle")
        title = "".join(title_elem.itertext()).strip() if title_elem is not None else ""

        authors: list[str] = []
        for author in art_elem.findall(".//AuthorList/Author")[:5]:
            last = (author.findtext("LastName") or "").strip()
            initials = (author.findtext("Initials") or "").strip()
            collective = (author.findtext("CollectiveName") or "").strip()
            name = f"{last} {initials}".strip() if last else collective
            if name:
                authors.append(name)

        abstract_parts: list[str] = []
        for ab_node in art_elem.findall(".//Abstract/AbstractText"):
            label = ab_node.get("Label")
            txt = "".join(ab_node.itertext()).strip()
            if txt:
                abstract_parts.append(f"{label}: {txt}" if label else txt)
        full_abstract = " ".join(abstract_parts)
        abstract_snippet = (
            full_abstract[:600] + "..." if len(full_abstract) > 600 else full_abstract
        ) or None

        doi = None
        for eloc in art_elem.findall("ELocationID"):
            if eloc.get("EIdType") == "doi" and eloc.text:
                doi = eloc.text.strip()
                break

        journal_elem = art_elem.find(".//Journal")
        journal_title = journal_elem.findtext("Title") if journal_elem is not None else None
        pub_year = None
        if journal_elem is not None:
            pd = journal_elem.find(".//PubDate")
            if pd is not None:
                pub_year = pd.findtext("Year") or pd.findtext("MedlineDate")

        articles.append(
            {
                "pmid": pmid,
                "title": title,
                "authors": authors,
                "journal": journal_title,
                "pub_date": pub_year,
                "doi": doi,
                "abstract_snippet": abstract_snippet,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            }
        )
    return articles


async def literature_search(
    drug: str | None = None,
    condition: str | None = None,
    years: int | str | None = 5,
    limit: int = 10,
) -> dict[str, Any]:
    """Search PubMed via NCBI E-utilities (esearch.fcgi + efetch.fcgi) for biomedical literature on a drug and/or condition."""
    cleaned_drug = (drug or "").strip()
    cleaned_cond = (condition or "").strip()
    if not cleaned_drug and not cleaned_cond:
        return {
            "status": "error",
            "error": "Provide at least 'drug' or 'condition' to search PubMed.",
            "disclaimer": MEDICAL_DISCLAIMER,
        }

    clamped_limit = max(1, min(int(limit or 10), 25))
    norm_drug = await normalize_drug_name(cleaned_drug) if cleaned_drug else None

    clauses: list[str] = []
    if norm_drug and norm_drug.normalized_name:
        if norm_drug.normalized_name.lower() != cleaned_drug.lower():
            clauses.append(f'("{norm_drug.normalized_name}"[tiab] OR "{cleaned_drug}"[tiab])')
        else:
            clauses.append(f'"{norm_drug.normalized_name}"[tiab]')
    if cleaned_cond:
        clauses.append(f'"{cleaned_cond}"[tiab]')

    date_clause = _build_date_clause(years)
    if date_clause:
        clauses.append(date_clause)

    query_term = " AND ".join(clauses)

    try:
        esearch_params = _ncbi_common_params() | {
            "db": "pubmed",
            "term": query_term,
            "retmax": clamped_limit,
            "sort": "relevance",
            "retmode": "json",
        }
        search_data = await http_client.get_json(
            f"{EUTILS_BASE_URL}/esearch.fcgi",
            params=esearch_params,
            source="PubMed E-utilities (esearch)",
        )
        esearch_result = search_data.get("esearchresult") or {}
        pmids: list[str] = esearch_result.get("idlist") or []
        total_count = int(esearch_result.get("count") or len(pmids))

        if not pmids:
            return {
                "query": {
                    "drug": cleaned_drug or None,
                    "normalized_drug": norm_drug.to_dict() if norm_drug else None,
                    "condition": cleaned_cond or None,
                    "years": years,
                    "pubmed_query": query_term,
                },
                "total_count": 0,
                "returned_count": 0,
                "articles": [],
                "source": "NCBI PubMed E-utilities",
                "disclaimer": MEDICAL_DISCLAIMER,
            }

        efetch_params = _ncbi_common_params() | {
            "db": "pubmed",
            "id": ",".join(pmids[:clamped_limit]),
            "rettype": "abstract",
            "retmode": "xml",
        }
        xml_body = await http_client.get_text(
            f"{EUTILS_BASE_URL}/efetch.fcgi",
            params=efetch_params,
            source="PubMed E-utilities (efetch)",
            expected_type="text/xml",
        )
        articles = _parse_pubmed_xml(xml_body)

        return {
            "query": {
                "drug": cleaned_drug or None,
                "normalized_drug": norm_drug.to_dict() if norm_drug else None,
                "condition": cleaned_cond or None,
                "years": years,
                "pubmed_query": query_term,
            },
            "total_count": total_count,
            "returned_count": len(articles),
            "articles": articles,
            "source": "NCBI PubMed E-utilities",
            "disclaimer": MEDICAL_DISCLAIMER,
        }

    except UpstreamAPIError as exc:
        return {
            "status": "upstream_error",
            "source": "NCBI PubMed E-utilities",
            "error": exc.message,
            "disclaimer": MEDICAL_DISCLAIMER,
        }
