# Architectural & Engineering Decisions (`docs/DECISIONS.md`)

This document records key architectural, security, and implementation decisions made while building **Pharmakon** — the Drug Safety & Clinical Trials MCP Server and Web Playground.

## 1. FastMCP over Streamable HTTP Mounted in FastAPI
- **Decision**: Use `FastMCP` (`mcp.http_app(path="/", stateless_http=True)`) mounted at `/mcp` inside a primary `FastAPI` application, sharing `lifespan=mcp_app.lifespan` (composed with database initialization).
- **Rationale**:
  - Streamable HTTP is the modern, firewall-friendly MCP transport specification that replaces legacy dual-endpoint SSE setups with a single unified endpoint (`/mcp`) supporting both JSON-RPC request/response and streaming notifications.
  - Using `stateless_http=True` allows horizontal scaling across stateless container instances and prevents session affinity issues on free container hosts (Hugging Face Spaces, Render).
  - Mounting inside FastAPI lets a single container serve both the authenticated `/mcp` protocol endpoint (for Claude Desktop, Cursor, and MCP clients) and the `/api/*` REST endpoints for the web playground, user dashboard, and usage analytics.

## 2. Authentication & Secret Handling
- **Decision**:
  - **MCP Endpoint (`/mcp`)**: Protected via `Authorization: Bearer msk_<token>` API keys. Keys are generated with 32 bytes of cryptographic randomness, prefixed with `msk_`, and only their `SHA-256` hash (`key_hash`) and a short display prefix (`msk_abcd...`) are persisted in the database. Plaintext keys are returned **only once** at creation time.
  - **User Accounts (`/api/auth/*`, `/api/keys/*`, `/api/usage/*`)**: Email + password hashed with `bcrypt` (via `bcrypt` library directly for zero passlib/Python 3.12+ deprecation friction), issuing signed `HS256` JWT Bearer tokens for web dashboard sessions.
  - **Public Web Playground (`/api/playground/run`)**: Supports authenticated API keys or a built-in demo rate-limited bucket per client IP so portfolio visitors can test all 6 tools immediately from the browser without creating an account first, while still encouraging account signup for personal MCP keys.
  - **`OPENFDA_API_KEY` Redaction**: A dedicated URL/message sanitizer (`sanitize_text` / `redact_api_key`) strips `api_key=...` query parameters and raw `OPENFDA_API_KEY` values from all log records, HTTP error strings, and exception tracebacks.

## 3. Caching & Upstream Resilience
- **Decision**: Dual-layer SQLite-backed + in-memory TTL cache (`HTTPCache` table + fast memory lookup) keyed by canonicalized `(method, url_without_secrets, sorted_params)` with configurable TTL (`CACHE_TTL_SECONDS`, default 3600s).
- **Rationale**:
  - Upstream biomedical APIs (openFDA, ClinicalTrials.gov v2, PubMed E-utilities, RxNorm) have strict rate limits (e.g., 3 req/s on keyless E-utilities, 1,000 req/day on keyless openFDA) and occasional transient 5xx responses.
  - Persisting cache entries in SQLite (swappable for PostgreSQL via `DATABASE_URL`) survives process restarts in local dev and single-container deployments while keeping latency under 5ms on cache hits.
  - Requests use `httpx.AsyncClient` with exponential backoff + jitter on HTTP `429`, `500`, `502`, `503`, `504` and network timeouts, returning structured, graceful fallback messages when an upstream service is unavailable.

## 4. Rate Limiting & Daily Quotas
- **Decision**: Per-API-key sliding-window minute rate limiter (`RATE_LIMIT_PER_MINUTE`, default 30 req/min) plus a daily call cap (`RATE_LIMIT_PER_DAY`, default 1,000 req/day) enforced at middleware/dependency level before tool execution.
- **Rationale**:
  - Returns standard HTTP `429 Too Many Requests` with an accurate `Retry-After` header (seconds until the current minute window or UTC day resets) and `X-RateLimit-Remaining-Minute` / `X-RateLimit-Remaining-Day` headers.
  - Every tool invocation records `(api_key_id, tool_name, latency_ms, status, timestamp)` in `usage_logs` for real-time visualization in the web dashboard.

## 5. Drug Name Normalization via RxNorm + Recall Enforcement in Safety Brief
- **Decision**:
  - Use NLM RxNorm REST API (`/REST/rxcui.json?name=...&search=2` and `/REST/rxcui/{rxcui}/related.json?tty=IN+BN`) to resolve brand or generic drug inputs into a canonical generic ingredient (`IN`), RxCUI, and known brand names (`BN`).
  - Include openFDA `/drug/enforcement.json` (active/recent recall enforcement reports) alongside `/drug/event.json` (`adverse_event_summary`), `/drug/label.json` (`drug_label_lookup`), and PubMed `literature_search` inside `drug_safety_brief(drug)` so all three specified openFDA endpoints (`drug/event`, `drug/label`, `drug/enforcement`) are actively utilized and surfaced in compact, LLM-friendly schemas.

## 6. Medical Disclaimer Policy
- **Decision**: Every tool output includes a `disclaimer` field stating:
  `"Informational only — not medical advice. Adverse event reports (FAERS) are unvalidated voluntary submissions and do not establish causation. Clinical decisions must be made by qualified healthcare professionals."`
  Tools strictly retrieve and summarize public regulatory/clinical records and never output clinical advice or treatment recommendations.

