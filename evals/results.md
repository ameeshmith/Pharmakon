# Pharmakon MCP Evaluation Report (`evals/results.md`)

- **Evaluation Mode:** Deterministic Router + Recorded Upstream Fixtures (ANTHROPIC_API_KEY not set — live LLM calls gracefully skipped)
- **Total Benchmark Questions:** 25
- **Tool Selection Accuracy:** **25/25 (100.0%)**
- **Answer / Fact Verification Accuracy:** **25/25 (100.0%)**

| ID | Question | Expected Tool | Selected Tool | Tool Acc | Verifiable Facts | Result |
|---|---|---|---|---|---|---|
| Q01 | Find completed Phase 3 clinical trials of Ozempic (semaglutide) for ... | `search_trials` | `search_trials` | PASS | 4/4 | **PASS** |
| Q02 | What are the eligibility criteria, enrollment count, and primary out... | `get_trial_details` | `get_trial_details` | PASS | 4/4 | **PASS** |
| Q03 | What are the top reported adverse reactions and seriousness breakdow... | `adverse_event_summary` | `adverse_event_summary` | PASS | 4/4 | **PASS** |
| Q04 | Look up the FDA product label boxed warning and contraindications fo... | `drug_label_lookup` | `drug_label_lookup` | PASS | 3/3 | **PASS** |
| Q05 | Search PubMed for recent peer-reviewed literature on semaglutide and... | `literature_search` | `literature_search` | PASS | 3/3 | **PASS** |
| Q06 | Give me a complete drug safety brief for Ozempic combining FAERS adv... | `drug_safety_brief` | `drug_safety_brief` | PASS | 5/5 | **PASS** |
| Q07 | Search for recruiting Phase 2 clinical trials for type 2 diabetes. | `search_trials` | `search_trials` | PASS | 3/3 | **PASS** |
| Q08 | Retrieve full protocol and study arm details for study NCT03548935. | `get_trial_details` | `get_trial_details` | PASS | 3/3 | **PASS** |
| Q09 | Summarize the top FAERS adverse event reports and serious report per... | `adverse_event_summary` | `adverse_event_summary` | PASS | 4/4 | **PASS** |
| Q10 | What are the dosage and administration instructions on the FDA drug ... | `drug_label_lookup` | `drug_label_lookup` | PASS | 3/3 | **PASS** |
| Q11 | Find published PubMed articles discussing cardiovascular outcomes of... | `literature_search` | `literature_search` | PASS | 3/3 | **PASS** |
| Q12 | Compile a comprehensive drug safety report for semaglutide across FD... | `drug_safety_brief` | `drug_safety_brief` | PASS | 4/4 | **PASS** |
| Q13 | Search ClinicalTrials.gov for cardiovascular disease studies involvi... | `search_trials` | `search_trials` | PASS | 3/3 | **PASS** |
| Q14 | Check the secondary outcomes and site locations of clinical trial NC... | `get_trial_details` | `get_trial_details` | PASS | 3/3 | **PASS** |
| Q15 | How many serious vs non-serious adverse event reports are recorded i... | `adverse_event_summary` | `adverse_event_summary` | PASS | 3/3 | **PASS** |
| Q16 | Check the warnings and cautions section of the FDA label for Ozempic... | `drug_label_lookup` | `drug_label_lookup` | PASS | 3/3 | **PASS** |
| Q17 | Search PubMed papers from the last 5 years by Wilding on semaglutide... | `literature_search` | `literature_search` | PASS | 3/3 | **PASS** |
| Q18 | Generate an all-in-one safety overview for Wegovy / semaglutide incl... | `drug_safety_brief` | `drug_safety_brief` | PASS | 3/3 | **PASS** |
| Q19 | List clinical trials in Boston or Cleveland studying semaglutide. | `search_trials` | `search_trials` | PASS | 3/3 | **PASS** |
| Q20 | What are the minimum age and sex eligibility requirements for trial ... | `get_trial_details` | `get_trial_details` | PASS | 3/3 | **PASS** |
| Q21 | Get the MedDRA preferred term counts for vomiting and pancreatitis r... | `adverse_event_summary` | `adverse_event_summary` | PASS | 4/4 | **PASS** |
| Q22 | Look up the FDA SPL adverse reactions section and manufacturer name ... | `drug_label_lookup` | `drug_label_lookup` | PASS | 3/3 | **PASS** |
| Q23 | Find PubMed literature DOIs and abstracts for semaglutide studies pu... | `literature_search` | `literature_search` | PASS | 3/3 | **PASS** |
| Q24 | Provide a complete safety brief for Ozempic so I can review boxed wa... | `drug_safety_brief` | `drug_safety_brief` | PASS | 4/4 | **PASS** |
| Q25 | Search ClinicalTrials.gov for Phase 3 completed trials of semaglutid... | `search_trials` | `search_trials` | PASS | 3/3 | **PASS** |
