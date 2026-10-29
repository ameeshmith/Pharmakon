"""Recorded upstream API fixtures for deterministic offline testing."""

from __future__ import annotations

from typing import Any

RXNORM_RXCUI_OZEMPIC: dict[str, Any] = {
    "idGroup": {
        "rxnormId": ["1991302"],
    }
}

RXNORM_PROPERTIES_OZEMPIC: dict[str, Any] = {
    "properties": {
        "rxcui": "1991302",
        "name": "semaglutide",
        "tty": "IN",
    }
}

RXNORM_RELATED_OZEMPIC: dict[str, Any] = {
    "relatedGroup": {
        "rxcui": "1991302",
        "conceptGroup": [
            {
                "tty": "IN",
                "conceptProperties": [{"rxcui": "1991302", "name": "semaglutide", "tty": "IN"}],
            },
            {
                "tty": "BN",
                "conceptProperties": [
                    {"rxcui": "1991306", "name": "Ozempic", "tty": "BN"},
                    {"rxcui": "2200644", "name": "Rybelsus", "tty": "BN"},
                    {"rxcui": "2553502", "name": "Wegovy", "tty": "BN"},
                ],
            },
        ],
    }
}

CT_SEARCH_RESPONSE: dict[str, Any] = {
    "totalCount": 2,
    "studies": [
        {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT03548935",
                    "briefTitle": "STEP 1: Research Study Investigating How Well Semaglutide Works in People Suffering From Overweight or Obesity",
                },
                "statusModule": {
                    "overallStatus": "COMPLETED",
                    "startDateStruct": {"date": "2018-06-04"},
                    "completionDateStruct": {"date": "2020-03-19"},
                },
                "designModule": {
                    "phases": ["PHASE3"],
                    "enrollmentInfo": {"count": 1961},
                },
                "conditionsModule": {
                    "conditions": ["Obesity", "Overweight"],
                },
                "armsInterventionsModule": {
                    "interventions": [
                        {"type": "DRUG", "name": "Semaglutide 2.4 mg"},
                        {"type": "DRUG", "name": "Placebo"},
                    ]
                },
                "sponsorCollaboratorsModule": {
                    "leadSponsor": {"name": "Novo Nordisk A/S"},
                },
                "contactsLocationsModule": {
                    "locations": [
                        {
                            "facility": "Massachusetts General Hospital",
                            "city": "Boston",
                            "country": "United States",
                        }
                    ]
                },
            }
        },
        {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT04881760",
                    "briefTitle": "Semaglutide Cardiovascular Outcomes Trial in Patients With Type 2 Diabetes (SOUL)",
                },
                "statusModule": {
                    "overallStatus": "ACTIVE_NOT_RECRUITING",
                    "startDateStruct": {"date": "2021-06-17"},
                    "completionDateStruct": {"date": "2024-07-30"},
                },
                "designModule": {
                    "phases": ["PHASE3"],
                    "enrollmentInfo": {"count": 9650},
                },
                "conditionsModule": {
                    "conditions": ["Type 2 Diabetes Mellitus", "Cardiovascular Disease"],
                },
                "armsInterventionsModule": {
                    "interventions": [
                        {"type": "DRUG", "name": "Oral semaglutide"},
                    ]
                },
                "sponsorCollaboratorsModule": {
                    "leadSponsor": {"name": "Novo Nordisk A/S"},
                },
                "contactsLocationsModule": {
                    "locations": [
                        {
                            "facility": "Cleveland Clinic",
                            "city": "Cleveland",
                            "country": "United States",
                        }
                    ]
                },
            }
        },
    ],
}

CT_STUDY_DETAIL_NCT03548935: dict[str, Any] = {
    "hasResults": True,
    "protocolSection": {
        "identificationModule": {
            "nctId": "NCT03548935",
            "briefTitle": "STEP 1: Research Study Investigating How Well Semaglutide Works in People Suffering From Overweight or Obesity",
            "officialTitle": "Effect and Safety of Semaglutide 2.4 mg Once-weekly in Subjects With Overweight or Obesity",
        },
        "statusModule": {
            "overallStatus": "COMPLETED",
            "startDateStruct": {"date": "2018-06-04"},
            "primaryCompletionDateStruct": {"date": "2020-03-19"},
            "completionDateStruct": {"date": "2020-03-19"},
            "lastUpdatePostDateStruct": {"date": "2021-05-12"},
        },
        "descriptionModule": {
            "briefSummary": "This randomized, double-blind, placebo-controlled Phase 3a trial evaluated the efficacy and safety of once-weekly subcutaneous semaglutide 2.4 mg plus lifestyle intervention for weight management in adults with obesity or overweight.",
        },
        "conditionsModule": {
            "conditions": ["Obesity", "Overweight"],
        },
        "designModule": {
            "studyType": "INTERVENTIONAL",
            "phases": ["PHASE3"],
            "enrollmentInfo": {"count": 1961},
        },
        "armsInterventionsModule": {
            "interventions": [
                {
                    "type": "DRUG",
                    "name": "Semaglutide 2.4 mg",
                    "description": "Subcutaneous injection once weekly for 68 weeks",
                },
                {
                    "type": "DRUG",
                    "name": "Placebo",
                    "description": "Matching subcutaneous placebo injection once weekly",
                },
            ]
        },
        "outcomesModule": {
            "primaryOutcomes": [
                {
                    "measure": "Percentage Change in Body Weight From Baseline to Week 68",
                    "timeFrame": "Baseline to Week 68",
                    "description": "Co-primary endpoint assessing percent body weight reduction",
                },
                {
                    "measure": "Subjects Who Achieve >= 5% Body Weight Reduction at Week 68",
                    "timeFrame": "Week 68",
                    "description": "Proportion of participants achieving clinically meaningful weight loss",
                },
            ],
            "secondaryOutcomes": [
                {
                    "measure": "Change in Waist Circumference",
                    "timeFrame": "Baseline to Week 68",
                }
            ],
        },
        "eligibilityModule": {
            "sex": "ALL",
            "minimumAge": "18 Years",
            "maximumAge": "N/A",
            "healthyVolunteers": False,
            "stdAges": ["ADULT", "OLDER_ADULT"],
            "eligibilityCriteria": "Inclusion Criteria:\n- BMI >= 30.0 kg/m^2 or >= 27.0 kg/m^2 with weight-related comorbidity.\nExclusion Criteria:\n- History of type 1 or type 2 diabetes mellitus.",
        },
        "sponsorCollaboratorsModule": {
            "leadSponsor": {"name": "Novo Nordisk A/S"},
        },
        "contactsLocationsModule": {
            "locations": [
                {
                    "facility": "Massachusetts General Hospital",
                    "city": "Boston",
                    "state": "Massachusetts",
                    "country": "United States",
                    "status": "COMPLETED",
                }
            ]
        },
    },
}
