# Pharmakon — Hosted Drug Safety & Clinical Trials MCP Server

[![CI](https://github.com/ameeshmith/Pharmakon/actions/workflows/ci.yml/badge.svg)](https://github.com/ameeshmith/Pharmakon/actions)
![Python 3.12](https://img.shields.io/badge/python-3.12%2B-14b8a6.svg)
![FastMCP Streamable HTTP](https://img.shields.io/badge/MCP-Streamable%20HTTP-6366f1.svg)
![Eval Pass Rate](https://img.shields.io/badge/Evals-25%2F25%20(100%25)-10b981.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-f43f5e.svg)

**Pharmakon** is a hosted **Model Context Protocol (MCP)** server, FastAPI backend, and Glassmorphism web playground that gives LLMs (Claude Desktop, Cursor, and custom agents) grounded, real-time access to authoritative U.S. biomedical and regulatory databases:

- **openFDA** (`/drug/event.json` FAERS adverse events, `/drug/label.json` SPL drug labels, `/drug/enforcement.json` recalls)
- **ClinicalTrials.gov REST API v2** (`/studies` search & `/studies/{nctId}` full study protocol details)
- **NCBI PubMed E-utilities** (`esearch.fcgi` + `efetch.fcgi` XML abstract retrieval)
- **NLM RxNorm REST API** (`/REST/rxcui.json`, `/approximateTerm.json`, `/related.json` brand-to-generic drug normalization)

Runs **100% on free tiers** with zero billing or payment providers.

---

## Architecture Diagram

```mermaid
flowchart LR
    subgraph Clients["MCP & Web Clients"]
        CD["Claude Desktop / Cursor"]
        UI["Glassmorphism Web UI\n(React + Vite + Tailwind)"]
    end

    subgraph Pharmakon["Pharmakon Backend (FastAPI + FastMCP)"]
        AUTH["Auth & Security Layer\n• SHA-256 Hashed API Keys\n• Bcrypt + JWT Sessions\n• Secret Redacting Logger"]
        RL["Sliding-Window Rate Limiter\n• 30 req/min & 1,000 req/day\n• HTTP 429 + Retry-After"]
        MCP["FastMCP Server\n(Streamable HTTP /mcp)"]
        REST["REST API (/api/*)\n• Playground Proxy\n• Key Management\n• Usage Telemetry"]
        CACHE["Resilient HTTP Client\n• SQLite + Memory TTL Cache\n• Exponential Backoff Retries"]
    end

    subgraph Upstreams["Public Biomedical APIs (100% Free)"]
        FDA["openFDA API\n(event, label, enforcement)"]
        CT["ClinicalTrials.gov\nREST API v2"]
        PM["NCBI PubMed\nE-utilities"]
        RX["NLM RxNorm\nREST API"]
    end

    CD -->|"Bearer pk_live_..."| AUTH
    UI -->|"JWT / Demo Bucket"| AUTH
    AUTH --> RL
    RL --> MCP
    RL --> REST
    MCP --> CACHE
    REST --> CACHE
    CACHE --> FDA
    CACHE --> CT
    CACHE --> PM
    CACHE --> RX
```

---

## Screenshots

| Glassmorphism Landing & Live Demo | Schema-Driven Web Playground | Developer Dashboard & Telemetry |
|---|---|---|
| ![Landing Page Placeholder](docs/screenshots/landing-placeholder.png) | ![Playground Placeholder](docs/screenshots/playground-placeholder.png) | ![Dashboard Placeholder](docs/screenshots/dashboard-placeholder.png) |

---

## MCP Tools Reference (6 Tools)

Every tool output returns compact, structured JSON tailored for LLM context windows and includes a mandatory medical disclaimer.

| Tool | Upstream Sources | Description |
|---|---|---|
| `search_trials(condition, drug, phase, status, location, limit)` | ClinicalTrials.gov v2 + RxNorm | Search clinical studies by disease, RxNorm-normalized intervention, Essie phase filter (`PHASE1`–`PHASE4`), recruitment status, and location. |
| `get_trial_details(nct_id)` | ClinicalTrials.gov v2 | Retrieve protocol summary, eligibility criteria, study arms, primary/secondary outcomes, and locations by NCT ID (e.g., `NCT03548935`). |
| `adverse_event_summary(drug, limit)` | openFDA (`drug/event`) + RxNorm | Aggregate top reported MedDRA Preferred Term reactions, counts, and serious vs. non-serious report breakdowns. |
| `drug_label_lookup(drug, sections)` | openFDA (`drug/label`) + RxNorm | Extract official FDA Structured Product Labeling sections: `boxed_warning`, `warnings_and_cautions`, `contraindications`, `dosage_and_administration`, `adverse_reactions`. |
| `literature_search(drug, condition, years, limit)` | PubMed E-utilities + RxNorm | Search PubMed (`esearch` + `efetch`) with publication window filtering and return PMIDs, titles, journals, DOIs, and abstract snippets. |
| `drug_safety_brief(drug)` | All 4 Sources in Parallel | Combine RxNorm normalization, FAERS adverse event summary, FDA SPL label warnings, openFDA `/drug/enforcement.json` recalls, and recent PubMed safety papers in a single report. |

---

## Connect to Claude Desktop / Cursor in 30 Seconds

1. Sign up on the Pharmakon Web Dashboard (or locally at `http://localhost:5173`) and create an API key (`pk_live_...`).
2. Add this snippet to your `claude_desktop_config.json` (or `.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "pharmakon": {
      "url": "http://localhost:8000/mcp",
      "headers": {
        "Authorization": "Bearer pk_live_YOUR_API_KEY"
      }
    }
  }
}
```

---

## Quick Start (Local Development)

### 1. Clone & Configure Environment
```bash
git clone https://github.com/ameeshmith/Pharmakon.git
cd Pharmakon
cp .env.example .env
# Optional: Add your free OPENFDA_API_KEY= in .env (falls back to keyless mode if empty)
```

### 2. Run Backend (Python 3.12 + uv)
```bash
uv sync --dev
uv run uvicorn server.main:app --reload --port 8000
```
- **API & Health Check:** `http://localhost:8000/health`
- **Streamable HTTP MCP Endpoint:** `http://localhost:8000/mcp`
- **Interactive OpenAPI Docs:** `http://localhost:8000/docs`

### 3. Run Frontend (React + Vite + TypeScript)
```bash
cd web
npm install
npm run dev
```
- **Glassmorphism Web App:** `http://localhost:5173`

### 4. Or Run Everything with Docker Compose
```bash
docker compose up --build
```

---

## Evaluation Benchmark (`/evals`)

Pharmakon ships with a 25-question biomedical benchmark (`evals/questions.json`) testing all 6 MCP tools against verifiable clinical facts.

| Metric | Latest Score | Pass Rate |
|---|---|---|
| **Tool Selection Accuracy** | `25 / 25` | **100.0%** |
| **Answer / Fact Verification Accuracy** | `25 / 25` | **100.0%** |

Run the evaluation suite locally:
```bash
# Uses ANTHROPIC_API_KEY if present in .env; gracefully runs deterministic evaluation if absent
uv run python evals/run_evals.py
```
See [`evals/results.md`](evals/results.md) for the full 25-question breakdown table.

---

## Engineering & Design Decisions

See [`docs/DECISIONS.md`](docs/DECISIONS.md) for full details:
- **Why Streamable HTTP?** Streamable HTTP unifies MCP communication over a single stateless HTTP endpoint (`/mcp`), avoiding fragile dual-connection SSE state across load balancers and free container hosts.
- **Caching Strategy:** Two-tier TTL cache (in-memory hot dictionary + SQLite `http_cache` table) keyed by canonicalized request URLs with sensitive parameters (`api_key`) stripped before hashing.
- **Auth & Secret Hygiene:** User passwords use `bcrypt` (12 rounds). MCP API keys (`pk_live_...`) are hashed with `SHA-256` before storage and returned in plaintext only once. A custom `SecretRedactingFilter` strips `OPENFDA_API_KEY` and `api_key=` from all logs and error messages.
- **What Would Change at Scale:**
  1. Swap SQLite for managed **PostgreSQL** (`DATABASE_URL=postgresql+psycopg://...`) with **Redis** for distributed sliding-window rate limiting and shared TTL caching across replicas.
  2. Offload `UsageLog` writes to an async batch queue (or ClickHouse/TimescaleDB) to eliminate synchronous DB writes on the hot tool-call path.
  3. Add OpenTelemetry distributed tracing across each upstream biomedical API call.

---

## Limitations

- **Unvalidated Voluntary Reports:** openFDA FAERS data consists of voluntary adverse event submissions. Counts do not represent incidence rates or prove drug causation.
- **Upstream Rate Limits in Keyless Mode:** Without `OPENFDA_API_KEY`, openFDA restricts callers to 1,000 requests/day per IP; without `NCBI_API_KEY`, PubMed E-utilities restricts callers to 3 requests/second.
- **Free Tier Cold Starts:** Hosted free tiers (Hugging Face Spaces / Render) can sleep when idle and take 15–30 seconds to wake on the first request. See [`DEPLOY.md`](DEPLOY.md).

---

## Data Sources, Licenses & Disclaimer

- **openFDA:** Provided by the U.S. Food and Drug Administration ([Terms & License](https://open.fda.gov/license/)). Do not rely on openFDA to make decisions regarding medical care.
- **ClinicalTrials.gov API v2:** Provided by the U.S. National Library of Medicine ([Terms and Conditions](https://clinicaltrials.gov/about-site/terms-conditions)).
- **NCBI PubMed E-utilities & NLM RxNorm:** Provided by the National Center for Biotechnology Information / National Library of Medicine ([Policies & Disclaimers](https://www.ncbi.nlm.nih.gov/home/about/policies/)). Check individual paper licenses for reuse restrictions.

> **Disclaimer:** Pharmakon is strictly an informational data retrieval tool and does **not** provide medical advice, diagnosis, or clinical treatment recommendations.
