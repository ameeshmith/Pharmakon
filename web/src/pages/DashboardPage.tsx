import React, { useCallback, useEffect, useState } from "react";
import {
  Activity,
  Clock,
  KeyRound,
  Plus,
  RefreshCw,
  ShieldAlert,
  Trash2,
} from "lucide-react";
import { createApiKey, fetchApiKeys, fetchUsageStats, revokeApiKey } from "../api";
import {
  CodeBlock,
  GlassButton,
  GlassCard,
  GlassInput,
  GlassModal,
  Skeleton,
} from "../components/ui";
import type { APIKeyItem, PageRoute, UsageStatsResponse, UserProfile } from "../types";

export const DashboardPage: React.FC<{
  user: UserProfile | null;
  authToken: string | null;
  onNavigate: (page: PageRoute) => void;
  onNotify: (msg: string, type?: "success" | "error" | "info") => void;
}> = ({ user, authToken, onNavigate, onNotify }) => {
  const [keys, setKeys] = useState<APIKeyItem[]>([]);
  const [stats, setStats] = useState<UsageStatsResponse | null>(null);
  const [newKeyName, setNewKeyName] = useState("Claude Desktop");
  const [createdPlainKey, setCreatedPlainKey] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const loadDashboard = useCallback(async () => {
    if (!authToken) return;
    setLoading(true);
    try {
      const [keysRes, statsRes] = await Promise.all([
        fetchApiKeys(authToken),
        fetchUsageStats(authToken),
      ]);
      setKeys(keysRes.keys);
      setStats(statsRes);
    } catch (err) {
      onNotify(
        err instanceof Error ? err.message : "Failed to load dashboard",
        "error"
      );
    } finally {
      setLoading(false);
    }
  }, [authToken, onNotify]);

  useEffect(() => {
    if (authToken) {
      void loadDashboard();
    }
  }, [authToken, loadDashboard]);

  if (!user || !authToken) {
    return (
      <div className="max-w-xl mx-auto py-16 text-center">
        <GlassCard dense className="space-y-4">
          <KeyRound className="w-10 h-10 text-teal-400 mx-auto" />
          <h2 className="text-2xl font-bold">Sign In to Manage API Keys</h2>
          <p className="text-sm text-slate-600 dark:text-slate-300">
            Create personal Bearer API keys for Claude Desktop and Cursor, monitor per-key tool latency, and inspect your daily rate limit quotas.
          </p>
          <GlassButton onClick={() => onNavigate("auth")}>
            Sign In / Create Account
          </GlassButton>
        </GlassCard>
      </div>
    );
  }

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const created = await createApiKey(authToken, newKeyName);
      if (created.raw_key) {
        setCreatedPlainKey(created.raw_key);
      }
      onNotify("Created new API key", "success");
      await loadDashboard();
    } catch (err) {
      onNotify(
        err instanceof Error ? err.message : "Could not create key",
        "error"
      );
    }
  };

  const handleRevoke = async (id: number) => {
    try {
      await revokeApiKey(authToken, id);
      onNotify("API key revoked", "info");
      await loadDashboard();
    } catch (err) {
      onNotify(
        err instanceof Error ? err.message : "Could not revoke key",
        "error"
      );
    }
  };

  const maxDayCount = Math.max(
    1,
    ...(stats?.by_day.map((d) => d.count) || [1])
  );
  const maxToolCount = Math.max(
    1,
    ...(stats?.by_tool.map((t) => t.count) || [1])
  );

  return (
    <div className="space-y-8 pb-16">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold">
            Developer Dashboard
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-300">
            Signed in as <strong>{user.email}</strong> • Manage hashed MCP keys & inspect live tool telemetry.
          </p>
        </div>
        <GlassButton
          variant="secondary"
          size="sm"
          onClick={() => void loadDashboard()}
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh Telemetry</span>
        </GlassButton>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <GlassCard className="space-y-1">
          <span className="text-xs uppercase tracking-wider text-slate-500 dark:text-slate-300">
            Total Tool Calls
          </span>
          <p className="text-3xl font-extrabold text-teal-400">
            {stats ? stats.total_calls : "—"}
          </p>
        </GlassCard>
        <GlassCard className="space-y-1">
          <span className="text-xs uppercase tracking-wider text-slate-500 dark:text-slate-300">
            Average Latency
          </span>
          <p className="text-3xl font-extrabold text-cyan-400">
            {stats ? `${stats.average_latency_ms} ms` : "—"}
          </p>
        </GlassCard>
        <GlassCard className="space-y-1">
          <span className="text-xs uppercase tracking-wider text-slate-500 dark:text-slate-300">
            Minute Quota Remaining
          </span>
          <p className="text-3xl font-extrabold text-indigo-400">
            {stats
              ? `${stats.rate_limit.remaining_minute} / ${stats.rate_limit.limit_per_minute}`
              : "—"}
          </p>
        </GlassCard>
        <GlassCard className="space-y-1">
          <span className="text-xs uppercase tracking-wider text-slate-500 dark:text-slate-300">
            Daily Call Cap Remaining
          </span>
          <p className="text-3xl font-extrabold text-fuchsia-400">
            {stats
              ? `${stats.rate_limit.remaining_day} / ${stats.rate_limit.limit_per_day}`
              : "—"}
          </p>
        </GlassCard>
      </div>

      {/* API Keys Management */}
      <GlassCard dense className="space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 border-b border-white/10 pb-4">
          <div>
            <h2 className="text-lg font-bold flex items-center gap-2">
              <KeyRound className="w-5 h-5 text-teal-400" />
              <span>MCP Bearer API Keys</span>
            </h2>
            <p className="text-xs text-slate-600 dark:text-slate-300">
              Only the SHA-256 hash and a short prefix are stored in the database. Plaintext keys are shown once at creation.
            </p>
          </div>
          <form onSubmit={handleCreateKey} className="flex items-end gap-2">
            <GlassInput
              id="new-key-label"
              label="Key Label"
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              placeholder="e.g. Claude Desktop"
            />
            <GlassButton type="submit">
              <Plus className="w-4 h-4" />
              <span>Create Key</span>
            </GlassButton>
          </form>
        </div>

        {loading && keys.length === 0 ? (
          <Skeleton className="h-20 w-full" />
        ) : keys.length === 0 ? (
          <p className="text-sm text-slate-600 dark:text-slate-300">
            No API keys yet. Create your first key above to connect Claude Desktop or Cursor.
          </p>
        ) : (
          <div className="space-y-2.5">
            {keys.map((k) => (
              <div
                key={k.id}
                className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-xl bg-white/5 border border-white/10"
              >
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm">{k.name}</span>
                    <span
                      className={`text-[11px] px-2 py-0.5 rounded-full ${
                        k.is_active
                          ? "bg-teal-500/20 text-teal-300 border border-teal-400/30"
                          : "bg-rose-500/20 text-rose-300 border border-rose-400/30"
                      }`}
                    >
                      {k.is_active ? "Active" : "Revoked"}
                    </span>
                  </div>
                  <div className="text-xs font-mono text-slate-500 dark:text-slate-300">
                    Prefix: {k.key_prefix} • Created:{" "}
                    {new Date(k.created_at).toLocaleDateString()}
                  </div>
                </div>
                {k.is_active && (
                  <GlassButton
                    size="sm"
                    variant="danger"
                    onClick={() => void handleRevoke(k.id)}
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Revoke</span>
                  </GlassButton>
                )}
              </div>
            ))}
          </div>
        )}
      </GlassCard>

      {/* Usage Charts by Day and Tool */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GlassCard dense className="space-y-4">
          <h3 className="font-bold text-base flex items-center gap-2">
            <Activity className="w-4 h-4 text-teal-400" />
            <span>Calls Over Last 7 Days</span>
          </h3>
          <div className="space-y-2.5">
            {(stats?.by_day || []).map((item) => (
              <div key={item.date} className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="font-mono">{item.date}</span>
                  <span className="font-semibold">{item.count} calls</span>
                </div>
                <div className="w-full h-2.5 rounded-full bg-white/10 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-teal-400 to-indigo-500"
                    style={{
                      width: `${Math.max(4, (item.count / maxDayCount) * 100)}%`,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </GlassCard>

        <GlassCard dense className="space-y-4">
          <h3 className="font-bold text-base flex items-center gap-2">
            <Clock className="w-4 h-4 text-cyan-400" />
            <span>Usage Breakdown by MCP Tool</span>
          </h3>
          {stats && stats.by_tool.length === 0 ? (
            <p className="text-xs text-slate-500 dark:text-slate-300 py-6">
              No tool invocations logged for your API keys yet.
            </p>
          ) : (
            <div className="space-y-2.5">
              {(stats?.by_tool || []).map((item) => (
                <div key={item.tool} className="space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span className="font-mono font-semibold">{item.tool}</span>
                    <span>{item.count} calls</span>
                  </div>
                  <div className="w-full h-2.5 rounded-full bg-white/10 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-fuchsia-500"
                      style={{
                        width: `${Math.max(6, (item.count / maxToolCount) * 100)}%`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </GlassCard>
      </div>

      {/* Copy-once Modal for newly generated API key */}
      <GlassModal
        open={Boolean(createdPlainKey)}
        title="Copy Your New Pharmakon API Key"
        onClose={() => setCreatedPlainKey(null)}
      >
        <div className="space-y-4">
          <div className="p-3 rounded-xl bg-amber-500/15 border border-amber-400/35 text-xs text-amber-200 flex items-start gap-2">
            <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5" />
            <span>
              Copy this key now. For security, Pharmakon stores only its SHA-256 hash and cannot display the plaintext key again.
            </span>
          </div>
          {createdPlainKey && (
            <CodeBlock
              title="Bearer API Key (Copy Once)"
              language="text"
              code={createdPlainKey}
            />
          )}
          <div className="flex justify-end">
            <GlassButton onClick={() => setCreatedPlainKey(null)}>
              I&apos;ve Saved My Key
            </GlassButton>
          </div>
        </div>
      </GlassModal>
    </div>
  );
};
