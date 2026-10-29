import React from "react";
import { BookOpen, Database, ShieldAlert, Terminal } from "lucide-react";
import { CodeBlock, GlassCard } from "../components/ui";
import type { ToolSchema } from "../types";

export const DocsPage: React.FC<{
  tools: ToolSchema[];
  rateLimits: { requests_per_minute: number; requests_per_day: number };
}> = ({ tools, rateLimits }) => {
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
    <div className="space-y-10 pb-16">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold">
          Pharmakon MCP Documentation & Tool Reference
        </h1>
        <p className="text-sm text-slate-600 dark:text-slate-300 mt-1">
          Auto-generated reference from the server&apos;s live tool schemas, connection snippets, rate-limit headers, and regulatory data source caveats.
        </p>
      </div>

      {/* Client Config Snippets */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GlassCard dense className="space-y-3">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-teal-400" />
            <h2 className="font-bold text-base">Claude Desktop Configuration</h2>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-300">
            Add to <code>~/Library/Application Support/Claude/claude_desktop_config.json</code> (macOS) or <code>%APPDATA%\Claude\claude_desktop_config.json</code> (Windows):
          </p>
          <CodeBlock
            title="claude_desktop_config.json"
            language="json"
            code={claudeConfig}
          />
        </GlassCard>

        <GlassCard dense className="space-y-3">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-indigo-400" />
            <h2 className="font-bold text-base">Cursor IDE Configuration</h2>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-300">
            Add to <code>.cursor/mcp.json</code> in your project root or global Cursor settings:
          </p>
          <CodeBlock title=".cursor/mcp.json" language="json" code={cursorConfig} />
        </GlassCard>
      </div>

      {/* Tool Reference generated from schemas */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-teal-400" />
          <span>MCP Tool Reference ({tools.length} Tools)</span>
        </h2>

        <div className="grid grid-cols-1 gap-4">
          {tools.map((tool) => (
            <GlassCard key={tool.name} dense className="space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/10 pb-2.5">
                <div>
                  <span className="font-mono text-sm font-bold text-teal-400">
                    {tool.name}
                  </span>
                  <span className="ml-2.5 text-sm font-semibold">
                    — {tool.title}
                  </span>
                </div>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-white/10">
                  {tool.category}
                </span>
              </div>

              <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-300">
                {tool.description}
              </p>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-white/10 text-slate-500 dark:text-slate-400">
                      <th className="py-2 pr-4">Parameter</th>
                      <th className="py-2 pr-4">Type</th>
                      <th className="py-2 pr-4">Required</th>
                      <th className="py-2">Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tool.parameters.map((p) => (
                      <tr key={p.name} className="border-b border-white/5">
                        <td className="py-2 pr-4 font-mono font-semibold text-teal-600 dark:text-teal-300">
                          {p.name}
                        </td>
                        <td className="py-2 pr-4 font-mono">{p.type}</td>
                        <td className="py-2 pr-4">
                          {p.required ? "Yes" : "Optional"}
                        </td>
                        <td className="py-2 text-slate-600 dark:text-slate-300">
                          {p.description}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </GlassCard>
          ))}
        </div>
      </div>

      {/* Rate Limits & Upstream Data Sources */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <GlassCard dense className="space-y-3">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-cyan-400" />
            <h3 className="font-bold text-base">Rate Limits & Caching</h3>
          </div>
          <ul className="text-xs text-slate-700 dark:text-slate-300 space-y-2 list-disc list-inside leading-relaxed">
            <li>
              <strong>Per-Minute Sliding Window:</strong>{" "}
              {rateLimits.requests_per_minute} requests / minute per API key.
            </li>
            <li>
              <strong>Daily Call Cap:</strong> {rateLimits.requests_per_day}{" "}
              requests / UTC day per API key.
            </li>
            <li>
              <strong>HTTP 429 Handling:</strong> Exceeding either quota returns{" "}
              <code>429 Too Many Requests</code> with a standard{" "}
              <code>Retry-After</code> header in seconds.
            </li>
            <li>
              <strong>Upstream TTL Cache:</strong> Responses from openFDA, ClinicalTrials.gov, PubMed, and RxNorm are cached for 1 hour (configurable via <code>CACHE_TTL_SECONDS</code>).
            </li>
          </ul>
        </GlassCard>

        <GlassCard dense className="space-y-3">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-amber-400" />
            <h3 className="font-bold text-base">
              Data Sources & Regulatory Caveats
            </h3>
          </div>
          <ul className="text-xs text-slate-700 dark:text-slate-300 space-y-2 list-disc list-inside leading-relaxed">
            <li>
              <strong>openFDA (FAERS, SPL, Enforcement):</strong> Adverse event reports are voluntary submissions and do not establish causation or incidence rates.
            </li>
            <li>
              <strong>ClinicalTrials.gov API v2:</strong> Trial statuses and eligibility criteria are maintained by study sponsors.
            </li>
            <li>
              <strong>NCBI PubMed E-utilities & RxNorm:</strong> Provided by the National Library of Medicine (NLM). Check individual article licenses before redistribution.
            </li>
          </ul>
        </GlassCard>
      </div>
    </div>
  );
};
