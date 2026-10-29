# Zero-Cost Deployment Guide (`DEPLOY.md`)

**Pharmakon** is engineered to run **100% on free tiers** with **no credit card or payment provider required**.

This guide walks through deploying:
1. **Backend (FastAPI + FastMCP Streamable HTTP):** **Hugging Face Spaces (Docker SDK)** — offers 2 vCPU, 16 GB RAM, and zero credit card requirement.
2. **Frontend (React + Vite + Tailwind Glassmorphism UI):** **Cloudflare Pages** — unlimited free static bandwidth, global CDN, and zero credit card requirement.

---

## Part 1: Deploy Backend on Hugging Face Spaces (Docker, No Card Required)

1. **Create a New Space:**
   - Sign in at [huggingface.co/spaces](https://huggingface.co/spaces) and click **Create new Space**.
   - **Space name:** `pharmakon-mcp`
   - **Select the Space SDK:** Choose **Docker** (Blank template).
   - **Hardware:** Select **CPU basic (Free — 2 vCPU · 16 GB RAM)**.
   - **Visibility:** Public.

2. **Configure Space Variables & Secrets (`Settings -> Variables and secrets`):**
   - Click **New secret**:
     - `OPENFDA_API_KEY`: Your free key from [open.fda.gov/apis/authentication](https://open.fda.gov/apis/authentication/) (optional; falls back to keyless mode if omitted).
     - `JWT_SECRET_KEY`: A random 32-byte hex string (`openssl rand -hex 32`).
   - Click **New variable**:
     - `PORT`: `7860` (default port exposed by Hugging Face Docker Spaces, already configured in `Dockerfile`).
     - `CORS_ORIGINS`: `https://pharmakon.pages.dev,http://localhost:5173` (update with your Cloudflare Pages URL).
     - `RATE_LIMIT_PER_MINUTE`: `30`
     - `RATE_LIMIT_PER_DAY`: `1000`
     - `CACHE_TTL_SECONDS`: `3600`

3. **Push Repository to Your Space:**
   Add the Space frontmatter header to the Space's `README.md` or push this repo directly:
   ```bash
   git remote add hf https://huggingface.co/spaces/<your-hf-username>/pharmakon-mcp
   git push hf main
   ```
   Hugging Face will build the `Dockerfile` and start `uvicorn server.main:app --host 0.0.0.0 --port 7860`.

4. **Verify Your Live Endpoints:**
   - **Health Check:** `https://<your-hf-username>-pharmakon-mcp.hf.space/health`
   - **MCP Streamable HTTP Endpoint:** `https://<your-hf-username>-pharmakon-mcp.hf.space/mcp`
   - **OpenAPI Docs:** `https://<your-hf-username>-pharmakon-mcp.hf.space/docs`

---

## Part 2: Deploy Frontend on Cloudflare Pages (Free, No Card Required)

1. Sign in to the [Cloudflare Dashboard](https://dash.cloudflare.com/) and navigate to **Workers & Pages -> Create -> Pages -> Connect to Git**.
2. Select your GitHub repository (`ameeshmith/Pharmakon`).
3. Configure the build settings:
   - **Framework preset:** `Vite`
   - **Root directory:** `web`
   - **Build command:** `npm run build`
   - **Build output directory:** `dist`
4. Add an Environment Variable under **Environment variables (Production & Preview)**:
   - `VITE_API_BASE_URL`: `https://<your-hf-username>-pharmakon-mcp.hf.space`
5. Click **Save and Deploy**. Within ~60 seconds, your Glassmorphism Web Playground and Developer Dashboard will be live at `https://pharmakon.pages.dev`.

---

## Part 3: What to Expect on Free Tiers (Idle Sleep & Ephemeral Storage)

- **Cold Starts / Idle Sleep:**
  - **Hugging Face Spaces** free CPU instances sleep after ~48 hours of inactivity (and **Render** free web services sleep after 15 minutes of inactivity).
  - The first request after sleeping takes **15–30 seconds** while the container boots. Hit `/health` or open the Web Playground once to wake the container before running an interactive Claude Desktop session.
- **Ephemeral SQLite Storage on Free Containers:**
  - Free container filesystems reset when the container is rebuilt or restarted after prolonged sleep.
  - To persist user accounts, hashed API keys, and usage logs across container restarts at zero cost, set `DATABASE_URL` in your Space secrets to a free managed PostgreSQL instance (e.g., [Neon](https://neon.tech) or [Supabase](https://supabase.com) free tier: `postgresql+psycopg://...`). No code changes are required—SQLAlchemy automatically switches dialects via `DATABASE_URL`.
