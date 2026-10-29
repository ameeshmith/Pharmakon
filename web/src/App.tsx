import React, { useEffect, useState } from "react";
import { ShieldAlert } from "lucide-react";
import {
  DEFAULT_TOOLS_FALLBACK,
  fetchCurrentUser,
  fetchToolsCatalog,
} from "./api";
import { GlassNavbar, Toast } from "./components/ui";
import { AuthPage } from "./pages/AuthPage";
import { DashboardPage } from "./pages/DashboardPage";
import { DocsPage } from "./pages/DocsPage";
import { LandingPage } from "./pages/LandingPage";
import { PlaygroundPage } from "./pages/PlaygroundPage";
import type { PageRoute, ToolSchema, UserProfile } from "./types";

export const App: React.FC = () => {
  const [activePage, setActivePage] = useState<PageRoute>("landing");
  const [darkMode, setDarkMode] = useState<boolean>(true);
  const [tools, setTools] = useState<ToolSchema[]>(DEFAULT_TOOLS_FALLBACK);
  const [rateLimits, setRateLimits] = useState({
    requests_per_minute: 30,
    requests_per_day: 1000,
  });
  const [authToken, setAuthToken] = useState<string | null>(() => {
    try {
      return localStorage.getItem("pharmakon_jwt");
    } catch {
      return null;
    }
  });
  const [user, setUser] = useState<UserProfile | null>(null);
  const [toast, setToast] = useState<{
    message: string | null;
    type: "success" | "error" | "info";
  }>({ message: null, type: "info" });

  useEffect(() => {
    const root = document.documentElement;
    if (darkMode) {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
  }, [darkMode]);

  useEffect(() => {
    void fetchToolsCatalog().then((res) => {
      if (res.tools?.length) {
        setTools(res.tools);
      }
      if (res.rate_limits) {
        setRateLimits(res.rate_limits);
      }
    });
  }, []);

  useEffect(() => {
    if (!authToken) {
      setUser(null);
      return;
    }
    void fetchCurrentUser(authToken)
      .then((u) => setUser(u))
      .catch(() => {
        setAuthToken(null);
        setUser(null);
        try {
          localStorage.removeItem("pharmakon_jwt");
        } catch {
          // ignore storage errors
        }
      });
  }, [authToken]);

  const handleNotify = (
    message: string,
    type: "success" | "error" | "info" = "info"
  ) => {
    setToast({ message, type });
  };

  const handleAuthenticated = (token: string, profile: UserProfile) => {
    setAuthToken(token);
    setUser(profile);
    try {
      localStorage.setItem("pharmakon_jwt", token);
    } catch {
      // ignore storage errors
    }
    setActivePage("dashboard");
  };

  const handleLogout = () => {
    setAuthToken(null);
    setUser(null);
    try {
      localStorage.removeItem("pharmakon_jwt");
    } catch {
      // ignore storage errors
    }
    setActivePage("landing");
    handleNotify("Signed out", "info");
  };

  return (
    <div className="min-h-screen flex flex-col relative">
      {/* Animated gradient mesh background */}
      <div className="mesh-bg" aria-hidden="true">
        <div className="mesh-blob mesh-blob-indigo" />
        <div className="mesh-blob mesh-blob-teal" />
        <div className="mesh-blob mesh-blob-magenta" />
      </div>

      <GlassNavbar
        activePage={activePage}
        onNavigate={setActivePage}
        darkMode={darkMode}
        onToggleDarkMode={() => setDarkMode((d) => !d)}
        user={user}
        onLogout={handleLogout}
      />

      <main className="flex-1 w-full max-w-7xl mx-auto px-3 sm:px-6 pt-8">
        {activePage === "landing" && (
          <LandingPage onNavigate={setActivePage} />
        )}
        {activePage === "playground" && (
          <PlaygroundPage
            tools={tools}
            authToken={authToken}
            onNotify={handleNotify}
          />
        )}
        {activePage === "dashboard" && (
          <DashboardPage
            user={user}
            authToken={authToken}
            onNavigate={setActivePage}
            onNotify={handleNotify}
          />
        )}
        {activePage === "docs" && (
          <DocsPage tools={tools} rateLimits={rateLimits} />
        )}
        {activePage === "auth" && (
          <AuthPage
            onAuthenticated={handleAuthenticated}
            onNotify={handleNotify}
          />
        )}
      </main>

      {/* Regulatory & Medical Disclaimer Footer */}
      <footer className="mt-auto px-3 sm:px-6 pb-6 pt-8">
        <div className="max-w-7xl mx-auto glass-dense-tint rounded-2xl p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-xs text-slate-600 dark:text-slate-300">
          <div className="flex items-start gap-2.5">
            <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <p className="leading-relaxed">
              <strong>Medical & Regulatory Disclaimer:</strong> Pharmakon is for informational and software engineering research only and does not provide medical advice. Adverse event reports from openFDA (FAERS) are unvalidated voluntary submissions and do not establish causation. Data sourced from openFDA, ClinicalTrials.gov API v2, NCBI PubMed E-utilities, and NLM RxNorm.
            </p>
          </div>
          <div className="shrink-0 font-mono text-[11px] text-slate-500 dark:text-slate-400">
            Pharmakon MCP • 100% Free Tier
          </div>
        </div>
      </footer>

      <Toast
        message={toast.message}
        type={toast.type}
        onDismiss={() => setToast((prev) => ({ ...prev, message: null }))}
      />
    </div>
  );
};

export default App;
