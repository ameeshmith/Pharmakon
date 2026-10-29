import type { APIKeyItem, ToolSchema, UsageStatsResponse, UserProfile } from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) || "";

export const DEFAULT_TOOLS_FALLBACK: ToolSchema[] = [
  {
    name: "search_trials",
    title: "Search Clinical Trials",
    category: "ClinicalTrials.gov API v2",
    description:
      "Search ClinicalTrials.gov (API v2) for clinical studies by condition, drug (normalized via RxNorm), trial phase, recruitment status, or geographic location.",
    parameters: [
      {
        name: "condition",
        type: "string",
        required: false,
        placeholder: "type 2 diabetes",
        description: "Disease or medical condition (maps to query.cond).",
      },
      {
        name: "drug",
        type: "string",
        required: false,
        placeholder: "Ozempic",
        description: "Drug or intervention name, brand or generic (normalized via RxNorm).",
      },
      {
        name: "phase",
        type: "string",
        required: false,
        enum: ["", "EARLY_PHASE1", "PHASE1", "PHASE2", "PHASE3", "PHASE4"],
        description: "Clinical trial phase filter (AREA[Phase]).",
      },
      {
        name: "status",
        type: "string",
        required: false,
        enum: [
          "",
          "RECRUITING",
          "ACTIVE_NOT_RECRUITING",
          "COMPLETED",
          "NOT_YET_RECRUITING",
          "TERMINATED",
        ],
        description: "Recruitment status filter (filter.overallStatus).",
      },
      {
        name: "location",
        type: "string",
        required: false,
        placeholder: "United States",
        description: "Country, state, city, or facility (maps to query.locn).",
      },
      {
        name: "limit",
        type: "integer",
        required: false,
        default: 5,
        min: 1,
        max: 50,
        description: "Maximum number of clinical trials to return (1-50).",
      },
    ],
    example_args: {
      condition: "obesity",
      drug: "semaglutide",
      phase: "PHASE3",
      status: "COMPLETED",
      limit: 5,
    },
  },
  {
    name: "get_trial_details",
    title: "Get Trial Details",
    category: "ClinicalTrials.gov API v2",
    description:
      "Retrieve full protocol summary, eligibility criteria, study arms, interventions, primary/secondary outcomes, and site locations for a single trial by NCT ID.",
    parameters: [
      {
        name: "nct_id",
        type: "string",
        required: true,
        placeholder: "NCT03548935",
        description: "ClinicalTrials.gov study identifier in NCT######## format.",
      },
    ],
    example_args: { nct_id: "NCT03548935" },
  },
  {
    name: "adverse_event_summary",
    title: "Adverse Event Summary (FAERS)",
    category: "openFDA FAERS + RxNorm",
    description:
      "Aggregate top reported MedDRA adverse event reactions, report counts, and seriousness breakdown from openFDA FAERS (/drug/event.json) with RxNorm drug normalization.",
    parameters: [
      {
        name: "drug",
        type: "string",
        required: true,
        placeholder: "semaglutide",
        description: "Brand or generic drug name (normalized via RxNorm).",
      },
      {
        name: "limit",
        type: "integer",
        required: false,
        default: 10,
        min: 1,
        max: 50,
        description: "Number of top MedDRA Preferred Term reactions to return (1-50).",
      },
    ],
    example_args: { drug: "semaglutide", limit: 10 },
  },
  {
    name: "drug_label_lookup",
    title: "FDA Drug Label Lookup (SPL)",
    category: "openFDA SPL + RxNorm",
    description:
      "Fetch structured FDA product labeling (/drug/label.json) including boxed warnings, warnings & cautions, contraindications, dosage & administration, and indications.",
    parameters: [
      {
        name: "drug",
        type: "string",
        required: true,
        placeholder: "warfarin",
        description: "Brand or generic drug name.",
      },
      {
        name: "sections",
        type: "array",
        required: false,
        placeholder: "boxed_warning, warnings, contraindications, dosage_and_administration",
        description:
          "Comma-separated list of SPL label sections to extract (defaults to boxed_warning, warnings_and_cautions, contraindications, dosage_and_administration).",
      },
    ],
    example_args: {
      drug: "warfarin",
      sections: ["boxed_warning", "warnings", "contraindications", "dosage_and_administration"],
    },
  },
  {
    name: "literature_search",
    title: "PubMed Literature Search",
    category: "NCBI PubMed E-utilities",
    description:
      "Search peer-reviewed biomedical literature via NCBI PubMed E-utilities (esearch + efetch) filtering by drug, condition, publication window (years), and result limit.",
    parameters: [
      {
        name: "drug",
        type: "string",
        required: false,
        placeholder: "pembrolizumab",
        description: "Drug or active ingredient name.",
      },
      {
        name: "condition",
        type: "string",
        required: false,
        placeholder: "melanoma",
        description: "Condition, indication, or safety topic.",
      },
      {
        name: "years",
        type: "integer",
        required: false,
        default: 5,
        min: 1,
        max: 50,
        description: "Lookback window in years (e.g. 5 for last 5 years).",
      },
      {
        name: "limit",
        type: "integer",
        required: false,
        default: 5,
        min: 1,
        max: 25,
        description: "Maximum number of PubMed articles with abstracts to return (1-25).",
      },
    ],
    example_args: {
      drug: "pembrolizumab",
      condition: "melanoma",
      years: 5,
      limit: 5,
    },
  },
  {
    name: "drug_safety_brief",
    title: "Comprehensive Drug Safety Brief",
    category: "Composite (openFDA + PubMed + RxNorm)",
    description:
      "Generate a unified drug safety intelligence report combining RxNorm normalization, openFDA FAERS adverse events, FDA SPL label warnings/contraindications, openFDA recall enforcement reports, and recent PubMed safety literature in one parallel call.",
    parameters: [
      {
        name: "drug",
        type: "string",
        required: true,
        placeholder: "metformin",
        description: "Brand or generic drug name to generate a full safety brief for.",
      },
    ],
    example_args: { drug: "metformin" },
  },
];

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const retryAfter = res.headers.get("Retry-After");
    const msg =
      body?.detail ||
      body?.message ||
      body?.error ||
      `Request failed with HTTP ${res.status}`;
    throw new Error(retryAfter ? `${msg} (Retry-After: ${retryAfter}s)` : msg);
  }
  return body as T;
}

export async function fetchToolsCatalog(): Promise<{
  tools: ToolSchema[];
  rate_limits: { requests_per_minute: number; requests_per_day: number };
}> {
  try {
    return await requestJson("/api/tools");
  } catch {
    return {
      tools: DEFAULT_TOOLS_FALLBACK,
      rate_limits: { requests_per_minute: 30, requests_per_day: 1000 },
    };
  }
}

export async function runPlaygroundTool(
  tool: string,
  args: Record<string, unknown>,
  tokenOrApiKey?: string | null
): Promise<{
  tool: string;
  arguments: Record<string, unknown>;
  result: Record<string, unknown>;
  rate_limit?: {
    limit_minute: number;
    remaining_minute: number;
    limit_day: number;
    remaining_day: number;
  };
}> {
  const headers: Record<string, string> = {};
  if (tokenOrApiKey) {
    headers["Authorization"] = `Bearer ${tokenOrApiKey}`;
  }
  return requestJson("/api/playground/run", {
    method: "POST",
    headers,
    body: JSON.stringify({ tool, arguments: args }),
  });
}

export async function signupUser(
  email: string,
  password: string
): Promise<{ access_token: string; user: UserProfile }> {
  return requestJson("/api/auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function loginUser(
  email: string,
  password: string
): Promise<{ access_token: string; user: UserProfile }> {
  return requestJson("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function fetchCurrentUser(token: string): Promise<UserProfile> {
  return requestJson("/api/auth/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function fetchApiKeys(token: string): Promise<{ keys: APIKeyItem[] }> {
  return requestJson("/api/keys", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function createApiKey(
  token: string,
  name: string
): Promise<APIKeyItem> {
  return requestJson("/api/keys", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ name }),
  });
}

export async function revokeApiKey(
  token: string,
  keyId: number
): Promise<APIKeyItem> {
  return requestJson(`/api/keys/${keyId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function fetchUsageStats(token: string): Promise<UsageStatsResponse> {
  return requestJson("/api/usage/stats", {
    headers: { Authorization: `Bearer ${token}` },
  });
}
