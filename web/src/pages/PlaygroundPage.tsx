import React, { useEffect, useState } from "react";
import {
  AlertTriangle,
  ExternalLink,
  Play,
  RotateCcw,
  Sparkles,
} from "lucide-react";
import { runPlaygroundTool } from "../api";
import {
  CodeBlock,
  GlassButton,
  GlassCard,
  GlassInput,
  Skeleton,
  Tabs,
} from "../components/ui";
import type { ToolSchema } from "../types";

export const PlaygroundPage: React.FC<{
  tools: ToolSchema[];
  authToken: string | null;
  onNotify: (msg: string, type?: "success" | "error" | "info") => void;
}> = ({ tools, authToken, onNotify }) => {
  const [selectedToolName, setSelectedToolName] = useState<string>(
    tools[0]?.name || "search_trials"
  );
  const [formValues, setFormValues] = useState<Record<string, string>>({});
  const [customApiKey, setCustomApiKey] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [resultTab, setResultTab] = useState<string>("formatted");
  const [output, setOutput] = useState<Record<string, unknown> | null>(null);
  const [rateInfo, setRateInfo] = useState<{
    limit_minute: number;
    remaining_minute: number;
    limit_day: number;
    remaining_day: number;
  } | null>(null);

  const selectedTool =
    tools.find((t) => t.name === selectedToolName) || tools[0];

  useEffect(() => {
    if (!selectedTool) return;
    const defaults: Record<string, string> = {};
    for (const p of selectedTool.parameters) {
      const exVal = selectedTool.example_args?.[p.name];
      if (Array.isArray(exVal)) {
        defaults[p.name] = exVal.join(", ");
      } else if (exVal !== undefined && exVal !== null) {
        defaults[p.name] = String(exVal);
      } else if (p.default !== undefined) {
        defaults[p.name] = String(p.default);
      } else {
        defaults[p.name] = "";
      }
    }
    setFormValues(defaults);
  }, [selectedToolName, selectedTool]);

  if (!selectedTool) {
    return null;
  }

  const buildCleanedArgs = (): Record<string, unknown> => {
    const args: Record<string, unknown> = {};
    for (const param of selectedTool.parameters) {
      const raw = (formValues[param.name] ?? "").trim();
      if (!raw) continue;
      if (param.type === "integer") {
        const parsed = parseInt(raw, 10);
        if (!Number.isNaN(parsed)) args[param.name] = parsed;
      } else if (param.type === "array") {
        args[param.name] = raw
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean);
      } else {
        args[param.name] = raw;
      }
    }
    return args;
  };

  const handleRun = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const args = buildCleanedArgs();
      const keyToUse = customApiKey.trim() || authToken;
      const res = await runPlaygroundTool(selectedTool.name, args, keyToUse);
      setOutput(res.result);
      if (res.rate_limit) {
        setRateInfo(res.rate_limit);
      }
      onNotify(`Executed ${selectedTool.name} successfully`, "success");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Tool execution failed";
      onNotify(msg, "error");
    } finally {
      setLoading(false);
    }
  };

  const originUrl =
    typeof window !== "undefined"
      ? window.location.origin
      : "http://localhost:8000";

  const cleanedArgs = buildCleanedArgs();
  const curlSnippet = `curl -X POST "${originUrl}/api/playground/run" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer ${customApiKey.trim() || "pk_live_YOUR_API_KEY"}" \\
  -d '${JSON.stringify(
    { tool: selectedTool.name, arguments: cleanedArgs },
    null,
    2
  )}'`;

  const mcpJsonRpcSnippet = JSON.stringify(
    {
      jsonrpc: "2.0",
      id: 1,
      method: "tools/call",
      params: {
        name: selectedTool.name,
        arguments: cleanedArgs,
      },
    },
    null,
    2
  );

  return (
    <div className="space-y-6 pb-16">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold">
            Interactive MCP Playground
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-300">
            Select any Pharmakon tool, customize parameters from its live schema, and inspect structured biomedical results.
          </p>
        </div>
        {rateInfo && (
          <div className="glass-surface rounded-xl px-3.5 py-2 text-xs flex items-center gap-3">
            <span>
              Minute quota:{" "}
              <strong>
                {rateInfo.remaining_minute}/{rateInfo.limit_minute}
              </strong>
            </span>
            <span className="opacity-40">|</span>
            <span>
              Daily quota:{" "}
              <strong>
                {rateInfo.remaining_day}/{rateInfo.limit_day}
              </strong>
            </span>
          </div>
        )}
      </div>

      {/* Tool selector pills */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {tools.map((t) => {
          const active = t.name === selectedTool.name;
          return (
            <button
              key={t.name}
              type="button"
              onClick={() => setSelectedToolName(t.name)}
              className={`text-left p-4 rounded-2xl transition-all border ${
                active
                  ? "glass-dense-tint border-teal-400/60 ring-2 ring-teal-400/40"
                  : "glass-surface hover:bg-white/15"
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-xs font-bold text-teal-600 dark:text-teal-300">
                  {t.name}()
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/10 text-slate-600 dark:text-slate-300">
                  {t.category}
                </span>
              </div>
              <p className="text-sm font-semibold mt-1">{t.title}</p>
            </button>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Schema-driven Form */}
        <GlassCard dense className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <div>
              <h2 className="font-bold text-base">{selectedTool.title}</h2>
              <p className="text-xs text-slate-600 dark:text-slate-300 mt-0.5">
                {selectedTool.description}
              </p>
            </div>
          </div>

          <form onSubmit={handleRun} className="space-y-4">
            {selectedTool.parameters.map((param) => (
              <div key={param.name}>
                {param.enum ? (
                  <div className="flex flex-col gap-1.5">
                    <label
                      htmlFor={`param-${param.name}`}
                      className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-200"
                    >
                      {param.name}{" "}
                      {param.required && (
                        <span className="text-rose-400">*</span>
                      )}
                    </label>
                    <select
                      id={`param-${param.name}`}
                      value={formValues[param.name] ?? ""}
                      onChange={(e) =>
                        setFormValues((prev) => ({
                          ...prev,
                          [param.name]: e.target.value,
                        }))
                      }
                      className="w-full rounded-xl px-3.5 py-2.5 text-sm bg-white/80 dark:bg-slate-950/75 text-slate-900 dark:text-slate-100 border border-slate-300/70 dark:border-white/15 focus:outline-none focus:ring-2 focus:ring-teal-400/70"
                    >
                      {param.enum.map((opt) => (
                        <option key={opt} value={opt}>
                          {opt || "Any (No filter)"}
                        </option>
                      ))}
                    </select>
                    <span className="text-xs text-slate-600 dark:text-slate-300">
                      {param.description}
                    </span>
                  </div>
                ) : (
                  <GlassInput
                    id={`param-${param.name}`}
                    label={`${param.name}${param.required ? " *" : ""}`}
                    type={param.type === "integer" ? "number" : "text"}
                    min={param.min}
                    max={param.max}
                    placeholder={param.placeholder}
                    helperText={param.description}
                    required={param.required}
                    value={formValues[param.name] ?? ""}
                    onChange={(e) =>
                      setFormValues((prev) => ({
                        ...prev,
                        [param.name]: e.target.value,
                      }))
                    }
                  />
                )}
              </div>
            ))}

            <div className="pt-2 border-t border-white/10">
              <GlassInput
                id="playground-api-key"
                label="Optional API Key (pk_live_...)"
                placeholder="Uses built-in demo bucket if blank"
                value={customApiKey}
                onChange={(e) => setCustomApiKey(e.target.value)}
              />
            </div>

            <div className="flex items-center gap-2 pt-2">
              <GlassButton
                type="submit"
                disabled={loading}
                className="flex-1"
              >
                <Play className="w-4 h-4" />
                <span>{loading ? "Querying Upstream APIs..." : "Run Tool"}</span>
              </GlassButton>
              <GlassButton
                type="button"
                variant="secondary"
                onClick={() => {
                  const preset: Record<string, string> = {};
                  for (const p of selectedTool.parameters) {
                    const v = selectedTool.example_args?.[p.name];
                    preset[p.name] = Array.isArray(v)
                      ? v.join(", ")
                      : v !== undefined
                      ? String(v)
                      : "";
                  }
                  setFormValues(preset);
                }}
              >
                <RotateCcw className="w-4 h-4" />
                <span>Reset Example</span>
              </GlassButton>
            </div>
          </form>
        </GlassCard>

        {/* Result & Export Pane */}
        <GlassCard dense className="lg:col-span-7 space-y-4 flex flex-col">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/10 pb-3">
            <h2 className="font-bold text-base flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-teal-400" />
              <span>Tool Output & Snippets</span>
            </h2>
            <Tabs
              tabs={[
                { id: "formatted", label: "Formatted View" },
                { id: "json", label: "Raw JSON" },
                { id: "curl", label: "cURL / MCP JSON-RPC" },
              ]}
              activeTab={resultTab}
              onChange={setResultTab}
            />
          </div>

          {loading ? (
            <div className="space-y-3 py-6">
              <Skeleton className="h-8 w-2/3" />
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-24 w-full" />
            </div>
          ) : resultTab === "curl" ? (
            <div className="space-y-4">
              <CodeBlock title="cURL Request" language="bash" code={curlSnippet} />
              <CodeBlock
                title="MCP Streamable HTTP JSON-RPC Payload (POST /mcp)"
                language="json"
                code={mcpJsonRpcSnippet}
              />
            </div>
          ) : !output ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center py-14 text-slate-600 dark:text-slate-300 space-y-2">
              <Play className="w-8 h-8 text-teal-400 opacity-80" />
              <p className="text-sm font-semibold">
                Click &ldquo;Run Tool&rdquo; to execute <code>{selectedTool.name}</code> against live biomedical APIs.
              </p>
            </div>
          ) : resultTab === "json" ? (
            <CodeBlock
              title={`${selectedTool.name} JSON Output`}
              language="json"
              code={JSON.stringify(output, null, 2)}
            />
          ) : (
            <FormattedToolResult output={output} />
          )}
        </GlassCard>
      </div>
    </div>
  );
};

const FormattedToolResult: React.FC<{ output: Record<string, unknown> }> = ({
  output,
}) => {
  const disclaimer =
    typeof output.disclaimer === "string" ? output.disclaimer : null;

  return (
    <div className="space-y-4 text-sm">
      {output.error ? (
        <div className="p-4 rounded-xl bg-rose-500/15 border border-rose-400/40 text-rose-800 dark:text-rose-200">
          <strong>Error:</strong> {String(output.error)}
        </div>
      ) : null}

      {/* Normalized drug pill if present */}
      {output.normalized_drug && typeof output.normalized_drug === "object" ? (
        <div className="p-3 rounded-xl bg-teal-500/10 border border-teal-400/25 flex flex-wrap items-center gap-3 text-xs">
          <span className="font-semibold text-teal-700 dark:text-teal-300">
            RxNorm Normalized:
          </span>
          <span>
            Generic:{" "}
            <strong>
              {String(
                (output.normalized_drug as Record<string, unknown>)
                  .normalized_name || ""
              )}
            </strong>
          </span>
          {(output.normalized_drug as Record<string, unknown>).rxcui ? (
            <span>
              RxCUI:{" "}
              <code>
                {String(
                  (output.normalized_drug as Record<string, unknown>).rxcui
                )}
              </code>
            </span>
          ) : null}
        </div>
      ) : null}

      {/* Trials list */}
      {Array.isArray(output.trials) && (
        <div className="space-y-3">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-300">
            Matching Studies ({String(output.total_count ?? output.trials.length)})
          </div>
          {(output.trials as Record<string, unknown>[]).map((trial) => (
            <div
              key={String(trial.nct_id)}
              className="p-3.5 rounded-xl bg-white/5 border border-white/10 space-y-1.5"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-xs font-bold text-teal-400">
                  {String(trial.nct_id)}
                </span>
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300">
                  {String(trial.overall_status)}
                </span>
              </div>
              <p className="font-semibold text-sm">{String(trial.title)}</p>
              <div className="text-xs text-slate-600 dark:text-slate-300 flex flex-wrap gap-3">
                {trial.lead_sponsor ? (
                  <span>Sponsor: {String(trial.lead_sponsor)}</span>
                ) : null}
                {trial.enrollment ? (
                  <span>Enrollment: {String(trial.enrollment)}</span>
                ) : null}
                {trial.url ? (
                  <a
                    href={String(trial.url)}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-teal-400 hover:underline"
                  >
                    <span>ClinicalTrials.gov</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Top Adverse Reactions */}
      {Array.isArray(output.top_reactions) && (
        <div className="space-y-2.5">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold uppercase tracking-wider">
              Top MedDRA Adverse Reactions
            </span>
            <span>
              Total FAERS Reports:{" "}
              <strong>{String(output.total_reports ?? 0)}</strong>
            </span>
          </div>
          <div className="space-y-1.5">
            {(output.top_reactions as Record<string, unknown>[]).map((r) => (
              <div
                key={String(r.reaction_meddra_pt)}
                className="flex items-center justify-between px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-xs"
              >
                <span className="font-mono font-semibold">
                  {String(r.reaction_meddra_pt)}
                </span>
                <span>
                  <strong>{String(r.count)}</strong> reports
                  {r.percentage_of_reports
                    ? ` (${String(r.percentage_of_reports)}%)`
                    : ""}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* PubMed Articles */}
      {Array.isArray(output.articles) && (
        <div className="space-y-2.5">
          <div className="text-xs font-semibold uppercase tracking-wider">
            PubMed Articles ({String(output.total_count ?? output.articles.length)})
          </div>
          {(output.articles as Record<string, unknown>[]).map((art) => (
            <div
              key={String(art.pmid)}
              className="p-3.5 rounded-xl bg-white/5 border border-white/10 space-y-1"
            >
              <div className="flex items-center justify-between text-xs text-teal-400 font-mono">
                <span>PMID: {String(art.pmid)}</span>
                <span>{String(art.pub_date || "")}</span>
              </div>
              <p className="font-semibold text-sm">{String(art.title)}</p>
              {art.abstract_snippet ? (
                <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                  {String(art.abstract_snippet)}
                </p>
              ) : null}
            </div>
          ))}
        </div>
      )}

      {/* Fallback JSON preview for complex composite structures */}
      {!Array.isArray(output.trials) &&
        !Array.isArray(output.top_reactions) &&
        !Array.isArray(output.articles) && (
          <CodeBlock
            title="Structured Result"
            language="json"
            code={JSON.stringify(output, null, 2)}
          />
        )}

      {disclaimer && (
        <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-400/30 text-amber-800 dark:text-amber-200 text-xs flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{disclaimer}</span>
        </div>
      )}
    </div>
  );
};
