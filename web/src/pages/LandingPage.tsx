import React, { useState } from "react";
import {
  ArrowRight,
  BookOpen,
  Database,
  FileWarning,
  FlaskConical,
  Lock,
  Play,
  ShieldCheck,
  Terminal,
  Zap,
} from "lucide-react";
import { CodeBlock, GlassButton, GlassCard, Tabs } from "../components/ui";
import type { PageRoute } from "../types";

const DEMO_STEPS = [
  {
    id: "brief",
    label: "1. drug_safety_brief('Ozempic')",
    prompt: "Summarize FDA boxed warnings, FAERS adverse reactions, and recalls for Ozempic.",
    output: `{
  "drug": "Ozempic",
  "normalized_drug": {
    "normalized_name": "semaglutide",
    "rxcui": "1991302",
    "brand_names": ["Ozempic", "Rybelsus", "Wegovy"]
  },
  "adverse_events": {
    "total_reports": 31000,
    "seriousness": { "serious_percentage": 40.0 },
    "top_reactions": [
      { "reaction_meddra_pt": "NAUSEA", "count": 8420 },
      { "reaction_meddra_pt": "VOMITING", "count": 4815 },
      { "reaction_meddra_pt": "PANCREATITIS", "count": 1120 }
    ]
  },
  "fda_label": {
    "has_boxed_warning": true,
    "sections": {
      "boxed_warning": "WARNING: RISK OF THYROID C-CELL TUMORS..."
    }
  },
  "disclaimer": "Informational only — not medical advice."
}`,
  },
  {
    id: "trials",
    label: "2. search_trials('obesity', 'semaglutide')",
    prompt: "Find completed Phase 3 clinical trials of semaglutide for obesity.",
    output: `{
  "total_count": 28,
  "returned_count": 2,
  "trials": [
    {
      "nct_id": "NCT03548935",
      "title": "STEP 1: Research Study Investigating How Well Semaglutide Works...",
      "overall_status": "COMPLETED",
      "phases": ["PHASE3"],
      "enrollment": 1961,
      "lead_sponsor": "Novo Nordisk A/S"
    }
  ],
  "source": "ClinicalTrials.gov API v2"
}`,
  },
];

export const LandingPage: React.FC<{
  onNavigate: (page: PageRoute) => void;
}> = ({ onNavigate }) => {
  const [activeDemo, setActiveDemo] = useState("brief");
  const [configClient, setConfigClient] = useState("claude");

  const currentDemo =
    DEMO_STEPS.find((d) => d.id === activeDemo) || DEMO_STEPS[0];

  const originUrl =
    typeof window !== "undefined"
      ? window.location.origin
      : "https://pharmakon-mcp.hf.space";

  const claudeConfig = `{
  "mcpServers": {
    "pharmakon": {
      "url": "${originUrl}/mcp",
      "headers": {
        "Authorization": "Bearer pk_live_YOUR_API_KEY"
      }
    }
  }
}`;

  const cursorConfig = `{
  "mcpServers": {
    "pharmakon-drug-safety": {
      "type": "streamable-http",
      "url": "${originUrl}/mcp",
      "headers": {
        "Authorization": "Bearer pk_live_YOUR_API_KEY"
      }
    }
  }
}`;

  return (
    <div className="space-y-16 pb-16">
      {/* Hero section */}
      <section className="pt-8 sm:pt-14 text-center max-w-4xl mx-auto space-y-6">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full glass-surface text-xs font-medium text-teal-700 dark:text-teal-300">
          <ShieldCheck className="w-4 h-4" />
          <span>Streamable HTTP MCP Server • openFDA • ClinicalTrials.gov v2 • PubMed • RxNorm</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight leading-tight">
          Grounded Biomedical & Drug Safety{" "}
          <span className="bg-gradient-to-r from-teal-400 via-cyan-300 to-fuchsia-400 bg-clip-text text-transparent">
            Intelligence for LLMs
          </span>
        </h1>

        <p className="text-base sm:text-lg text-slate-700 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed">
          <strong>Pharmakon</strong> connects Claude Desktop, Cursor, and custom AI agents directly to authoritative U.S. regulatory and clinical databases over Streamable HTTP—with hashed API keys, TTL caching, and rate limiting built in.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
          <GlassButton size="lg" onClick={() => onNavigate("playground")}>
            <Play className="w-4 h-4" />
            <span>Launch Web Playground</span>
          </GlassButton>
          <GlassButton
            size="lg"
            variant="secondary"
            onClick={() => onNavigate("auth")}
          >
            <span>Create Free API Key</span>
            <ArrowRight className="w-4 h-4" />
          </GlassButton>
        </div>
      </section>

      {/* Animated Live Tool Call Showcase */}
      <section className="max-w-5xl mx-auto">
        <GlassCard dense className="space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <Terminal className="w-5 h-5 text-teal-400" />
              <h2 className="text-lg font-bold">Interactive MCP Tool Call Preview</h2>
            </div>
            <Tabs
              tabs={DEMO_STEPS.map((d) => ({ id: d.id, label: d.label }))}
              activeTab={activeDemo}
              onChange={setActiveDemo}
            />
          </div>

          <div className="rounded-xl p-3.5 bg-teal-500/10 border border-teal-400/25 text-xs sm:text-sm text-teal-900 dark:text-teal-200 flex items-center justify-between gap-4">
            <span>
              <strong>User Prompt:</strong> &ldquo;{currentDemo.prompt}&rdquo;
            </span>
            <GlassButton
              size="sm"
              variant="secondary"
              onClick={() => onNavigate("playground")}
            >
              Run Live
            </GlassButton>
          </div>

          <CodeBlock
            title={`MCP Response • ${currentDemo.label}`}
            language="json"
            code={currentDemo.output}
          />
        </GlassCard>
      </section>

      {/* 6 MCP Tools + Engineering Highlights */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <GlassCard className="space-y-3">
          <div className="w-10 h-10 rounded-xl bg-teal-500/20 border border-teal-400/30 flex items-center justify-center text-teal-400">
            <FlaskConical className="w-5 h-5" />
          </div>
          <h3 className="text-lg font-bold">ClinicalTrials.gov API v2</h3>
          <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
            <code>search_trials</code> and <code>get_trial_details</code> query live studies by disease, RxNorm-normalized intervention, Essie phase filters, and NCT IDs.
          </p>
        </GlassCard>

        <GlassCard className="space-y-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/20 border border-indigo-400/30 flex items-center justify-center text-indigo-400">
            <FileWarning className="w-5 h-5" />
          </div>
          <h3 className="text-lg font-bold">openFDA FAERS, SPL & Recalls</h3>
          <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
            <code>adverse_event_summary</code>, <code>drug_label_lookup</code>, and <code>drug_safety_brief</code> aggregate MedDRA reactions, boxed warnings, and recall enforcements.
          </p>
        </GlassCard>

        <GlassCard className="space-y-3">
          <div className="w-10 h-10 rounded-xl bg-fuchsia-500/20 border border-fuchsia-400/30 flex items-center justify-center text-fuchsia-400">
            <BookOpen className="w-5 h-5" />
          </div>
          <h3 className="text-lg font-bold">PubMed E-utilities & RxNorm</h3>
          <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
            <code>literature_search</code> fetches peer-reviewed abstracts and DOIs via NCBI <code>esearch</code> + <code>efetch</code> while RxNorm resolves brand names to generic ingredients.
          </p>
        </GlassCard>
      </section>

      {/* Connect in 30 Seconds */}
      <section className="max-w-4xl mx-auto">
        <GlassCard dense className="space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-bold">Connect in 30 Seconds</h2>
              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300">
                Paste this snippet into your Claude Desktop or Cursor MCP configuration file.
              </p>
            </div>
            <Tabs
              tabs={[
                { id: "claude", label: "Claude Desktop" },
                { id: "cursor", label: "Cursor IDE" },
              ]}
              activeTab={configClient}
              onChange={setConfigClient}
            />
          </div>

          <CodeBlock
            title={
              configClient === "claude"
                ? "claude_desktop_config.json"
                : ".cursor/mcp.json"
            }
            language="json"
            code={configClient === "claude" ? claudeConfig : cursorConfig}
          />

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs text-slate-700 dark:text-slate-300">
            <div className="flex items-center gap-2 p-3 rounded-xl bg-white/5 border border-white/10">
              <Lock className="w-4 h-4 text-teal-400 shrink-0" />
              <span>SHA-256 hashed Bearer API keys</span>
            </div>
            <div className="flex items-center gap-2 p-3 rounded-xl bg-white/5 border border-white/10">
              <Zap className="w-4 h-4 text-cyan-400 shrink-0" />
              <span>30 req/min & 1,000 req/day quota</span>
            </div>
            <div className="flex items-center gap-2 p-3 rounded-xl bg-white/5 border border-white/10">
              <Database className="w-4 h-4 text-indigo-400 shrink-0" />
              <span>SQLite/Postgres TTL response cache</span>
            </div>
          </div>
        </GlassCard>
      </section>

      {/* FAQ */}
      <section className="max-w-4xl mx-auto space-y-4">
        <h2 className="text-2xl font-bold text-center">Frequently Asked Questions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <GlassCard dense className="space-y-2">
            <h3 className="font-bold text-sm">Does Pharmakon require a paid API key?</h3>
            <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
              No. Pharmakon runs 100% on free public biomedical APIs. If <code>OPENFDA_API_KEY</code> is omitted, the server automatically falls back to keyless openFDA mode.
            </p>
          </GlassCard>
          <GlassCard dense className="space-y-2">
            <h3 className="font-bold text-sm">Do FAERS adverse event counts prove causation?</h3>
            <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
              No. FDA FAERS reports are unvalidated voluntary submissions. High report counts often reflect widespread prescribing volume rather than causal risk.
            </p>
          </GlassCard>
          <GlassCard dense className="space-y-2">
            <h3 className="font-bold text-sm">How are brand drug names like Ozempic handled?</h3>
            <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
              Every drug query is normalized through the NLM RxNorm REST API to resolve its RxCUI, generic ingredient (e.g., <em>semaglutide</em>), and related brand names.
            </p>
          </GlassCard>
          <GlassCard dense className="space-y-2">
            <h3 className="font-bold text-sm">How is my API key stored?</h3>
            <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
              Plaintext keys are shown once at creation and hashed with SHA-256 before persistence. Upstream secrets like <code>OPENFDA_API_KEY</code> are scrubbed from all logs.
            </p>
          </GlassCard>
        </div>
      </section>
    </div>
  );
};
