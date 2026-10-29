"""Recorded upstream API fixtures for openFDA (event, label, enforcement) and PubMed (esearch, efetch)."""

from __future__ import annotations

from typing import Any

OPENFDA_EVENT_REACTIONS_SEMAGLUTIDE: dict[str, Any] = {
    "meta": {"results": {"total": 3}},
    "results": [
        {"term": "NAUSEA", "count": 8420},
        {"term": "VOMITING", "count": 4815},
        {"term": "DIARRHOEA", "count": 3910},
        {"term": "PANCREATITIS", "count": 1120},
    ],
}

OPENFDA_EVENT_SERIOUS_SEMAGLUTIDE: dict[str, Any] = {
    "results": [
        {"term": 1, "count": 12400},
        {"term": 2, "count": 18600},
    ]
}

OPENFDA_LABEL_SEMAGLUTIDE: dict[str, Any] = {
    "results": [
        {
            "set_id": "adec4fd2-9856-4c99-91d4-1102a743a001",
            "effective_time": "20240118",
            "openfda": {
                "brand_name": ["OZEMPIC"],
                "generic_name": ["SEMAGLUTIDE"],
                "manufacturer_name": ["Novo Nordisk Inc."],
                "route": ["SUBCUTANEOUS"],
                "product_type": ["HUMAN PRESCRIPTION DRUG"],
            },
            "boxed_warning": [
                "WARNING: RISK OF THYROID C-CELL TUMORS. In rodents, semaglutide causes dose-dependent and treatment-duration-dependent thyroid C-cell tumors. Contraindicated in patients with a personal or family history of medullary thyroid carcinoma (MTC) or in patients with Multiple Endocrine Neoplasia syndrome type 2 (MEN 2)."
            ],
            "warnings_and_cautions": [
                "Pancreatitis: Has been reported in clinical trials. Discontinue promptly if pancreatitis is suspected. Diabetic Retinopathy Complications: Has been reported in a cardiovascular outcomes trial. Acute Kidney Injury: Monitor renal function in patients with renal impairment reporting severe adverse gastrointestinal reactions."
            ],
            "contraindications": [
                "Personal or family history of medullary thyroid carcinoma (MTC) or in patients with Multiple Endocrine Neoplasia syndrome type 2 (MEN 2). Prior serious hypersensitivity reaction to semaglutide."
            ],
            "dosage_and_administration": [
                "Start at 0.25 mg once weekly subcutaneously for 4 weeks, then increase to 0.5 mg once weekly. May increase to 1 mg or 2 mg once weekly if additional glycemic control is needed."
            ],
            "adverse_reactions": [
                "The most common adverse reactions, reported in >=5% of patients treated with OZEMPIC are: nausea, vomiting, diarrhea, abdominal pain, and constipation."
            ],
            "indications_and_usage": [
                "OZEMPIC is a GLP-1 receptor agonist indicated as an adjunct to diet and exercise to improve glycemic control in adults with type 2 diabetes mellitus and to reduce the risk of major adverse cardiovascular events."
            ],
        }
    ]
}

OPENFDA_ENFORCEMENT_SEMAGLUTIDE: dict[str, Any] = {
    "meta": {"results": {"total": 1}},
    "results": [
        {
            "recall_number": "D-0192-2024",
            "classification": "Class II",
            "status": "Ongoing",
            "recalling_firm": "Example Specialty Compounding Pharmacy",
            "reason_for_recall": "Lack of Assurance of Sterility in compounded semaglutide vials.",
            "report_date": "20240214",
            "product_description": "Semaglutide Injection 2.5 mg/mL sterile multi-dose vial",
        }
    ],
}

PUBMED_ESEARCH_RESPONSE: dict[str, Any] = {
    "esearchresult": {
        "count": "142",
        "retmax": "2",
        "idlist": ["33567185", "37952199"],
    }
}

PUBMED_EFETCH_XML = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE PubmedArticleSet PUBLIC "-//NLM//DTD PubMedArticle, 1st January 2024//EN" "https://dtd.nlm.nih.gov/ncbi/pubmed/out/pubmed_240101.dtd">
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID Version="1">33567185</PMID>
      <Article>
        <Journal>
          <Title>The New England Journal of Medicine</Title>
          <JournalIssue>
            <PubDate>
              <Year>2021</Year>
              <Month>Mar</Month>
            </PubDate>
          </JournalIssue>
        </Journal>
        <ArticleTitle>Once-Weekly Semaglutide in Adults with Overweight or Obesity.</ArticleTitle>
        <ELocationID EIdType="doi" ValidYN="Y">10.1056/NEJMoa2032183</ELocationID>
        <Abstract>
          <AbstractText Label="BACKGROUND">Obesity is a global health challenge with few pharmacologic options.</AbstractText>
          <AbstractText Label="RESULTS">Mean change in body weight from baseline to week 68 was -14.9% in the semaglutide group as compared with -2.4% with placebo. Gastrointestinal disorders (nausea and diarrhea) were the most common adverse events.</AbstractText>
        </Abstract>
        <AuthorList>
          <Author>
            <LastName>Wilding</LastName>
            <Initials>JPH</Initials>
          </Author>
          <Author>
            <LastName>Batterham</LastName>
            <Initials>RL</Initials>
          </Author>
        </AuthorList>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
  <PubmedArticle>
    <MedlineCitation>
      <PMID Version="1">37952199</PMID>
      <Article>
        <Journal>
          <Title>The New England Journal of Medicine</Title>
          <JournalIssue>
            <PubDate>
              <Year>2023</Year>
              <Month>Nov</Month>
            </PubDate>
          </JournalIssue>
        </Journal>
        <ArticleTitle>Semaglutide and Cardiovascular Outcomes in Obesity without Diabetes.</ArticleTitle>
        <ELocationID EIdType="doi" ValidYN="Y">10.1056/NEJMoa2307563</ELocationID>
        <Abstract>
          <AbstractText Label="CONCLUSIONS">In patients with preexisting cardiovascular disease and overweight or obesity but without diabetes, weekly subcutaneous semaglutide at a dose of 2.4 mg was superior to placebo in reducing the incidence of death from cardiovascular causes, nonfatal myocardial infarction, or nonfatal stroke.</AbstractText>
        </Abstract>
        <AuthorList>
          <Author>
            <LastName>Lincoff</LastName>
            <Initials>AM</Initials>
          </Author>
        </AuthorList>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
"""
