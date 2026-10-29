import React, { useState } from "react";
import {
  Activity,
  Check,
  Copy,
  KeyRound,
  LogOut,
  Menu,
  Moon,
  Sparkles,
  Sun,
  X,
} from "lucide-react";
import type { PageRoute, UserProfile } from "../types";

export const GlassCard: React.FC<{
  children: React.ReactNode;
  className?: string;
  dense?: boolean;
}> = ({ children, className = "", dense = false }) => (
  <div
    className={`${
      dense ? "glass-dense-tint" : "glass-surface"
    } rounded-2xl p-6 transition-all duration-200 ${className}`}
  >
    {children}
  </div>
);

export const GlassButton: React.FC<
  React.ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: "primary" | "secondary" | "danger" | "ghost";
    size?: "sm" | "md" | "lg";
  }
> = ({
  children,
  variant = "primary",
  size = "md",
  className = "",
  ...props
}) => {
  const variantClasses: Record<string, string> = {
    primary:
      "bg-gradient-to-r from-teal-500 via-cyan-500 to-indigo-500 text-white shadow-lg shadow-teal-500/20 hover:brightness-110 border border-white/25",
    secondary:
      "glass-surface text-slate-900 dark:text-slate-100 hover:bg-white/20 dark:hover:bg-white/15",
    danger:
      "bg-rose-500/20 hover:bg-rose-500/30 text-rose-700 dark:text-rose-200 border border-rose-400/35",
    ghost:
      "bg-transparent hover:bg-white/10 text-slate-700 dark:text-slate-200 border border-transparent",
  };
  const sizeClasses: Record<string, string> = {
    sm: "px-3 py-1.5 text-xs rounded-xl",
    md: "px-4 py-2.5 text-sm rounded-xl",
    lg: "px-6 py-3 text-base rounded-2xl",
  };

  return (
    <button
      className={`inline-flex items-center justify-center gap-2 font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-teal-400/70 disabled:opacity-50 disabled:cursor-not-allowed ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};

export const GlassInput: React.FC<
  React.InputHTMLAttributes<HTMLInputElement> & {
    label?: string;
    helperText?: string;
  }
> = ({ label, helperText, id, className = "", ...props }) => {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label
          htmlFor={inputId}
          className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-200"
        >
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={`w-full rounded-xl px-3.5 py-2.5 text-sm bg-white/80 dark:bg-slate-950/65 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 border border-slate-300/70 dark:border-white/15 focus:outline-none focus:ring-2 focus:ring-teal-400/70 transition-all ${className}`}
        {...props}
      />
      {helperText && (
        <span className="text-xs text-slate-600 dark:text-slate-300">
          {helperText}
        </span>
      )}
    </div>
  );
};

export const GlassModal: React.FC<{
  open: boolean;
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}> = ({ open, title, onClose, children }) => {
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-md"
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <GlassCard dense className="w-full max-w-lg relative">
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-200/20">
          <h3 className="text-lg font-bold text-slate-900 dark:text-white">
            {title}
          </h3>
          <button
            onClick={onClose}
            aria-label="Close modal"
            className="p-1.5 rounded-lg hover:bg-white/15 text-slate-500 dark:text-slate-300"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        {children}
      </GlassCard>
    </div>
  );
};

export const Toast: React.FC<{
  message: string | null;
  type?: "success" | "error" | "info";
  onDismiss: () => void;
}> = ({ message, type = "info", onDismiss }) => {
  if (!message) return null;
  const badgeColor =
    type === "error"
      ? "border-rose-400/50 bg-rose-950/90 text-rose-100"
      : type === "success"
      ? "border-teal-400/50 bg-teal-950/90 text-teal-100"
      : "border-indigo-400/50 bg-slate-900/90 text-slate-100";
  return (
    <div
      role="status"
      className={`fixed bottom-5 right-5 z-50 flex items-center gap-3 px-4 py-3 rounded-2xl border shadow-2xl backdrop-blur-xl ${badgeColor}`}
    >
      <span className="text-sm font-medium">{message}</span>
      <button
        onClick={onDismiss}
        aria-label="Dismiss notification"
        className="p-1 rounded-lg hover:bg-white/10"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};

export const Skeleton: React.FC<{ className?: string }> = ({
  className = "h-6 w-full",
}) => (
  <div
    aria-hidden="true"
    className={`animate-pulse rounded-xl bg-slate-400/20 dark:bg-white/10 ${className}`}
  />
);

export const Tabs: React.FC<{
  tabs: { id: string; label: string }[];
  activeTab: string;
  onChange: (id: string) => void;
}> = ({ tabs, activeTab, onChange }) => (
  <div
    role="tablist"
    className="inline-flex flex-wrap gap-1.5 p-1.5 rounded-2xl glass-surface"
  >
    {tabs.map((t) => {
      const active = t.id === activeTab;
      return (
        <button
          key={t.id}
          role="tab"
          aria-selected={active}
          onClick={() => onChange(t.id)}
          className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
            active
              ? "bg-gradient-to-r from-teal-500 to-indigo-500 text-white shadow-md"
              : "text-slate-700 dark:text-slate-300 hover:bg-white/10"
          }`}
        >
          {t.label}
        </button>
      );
    })}
  </div>
);

export const CodeBlock: React.FC<{
  code: string;
  language?: string;
  title?: string;
}> = ({ code, language = "json", title }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  };

  return (
    <div className="rounded-2xl overflow-hidden border border-slate-300/60 dark:border-white/15 bg-slate-950/90 text-slate-100">
      <div className="flex items-center justify-between px-4 py-2 bg-white/5 border-b border-white/10 text-xs text-slate-300">
        <span className="font-mono uppercase tracking-wider">
          {title || language}
        </span>
        <button
          type="button"
          onClick={handleCopy}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/10 hover:bg-white/20 text-slate-100 transition"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-teal-400" />
              <span>Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <pre className="p-4 text-xs font-mono overflow-x-auto leading-relaxed">
        <code>{code}</code>
      </pre>
    </div>
  );
};

export const GlassNavbar: React.FC<{
  activePage: PageRoute;
  onNavigate: (page: PageRoute) => void;
  darkMode: boolean;
  onToggleDarkMode: () => void;
  user: UserProfile | null;
  onLogout: () => void;
}> = ({
  activePage,
  onNavigate,
  darkMode,
  onToggleDarkMode,
  user,
  onLogout,
}) => {
  const [mobileOpen, setMobileOpen] = useState(false);

  const navItems: { id: PageRoute; label: string }[] = [
    { id: "landing", label: "Overview" },
    { id: "playground", label: "Playground" },
    { id: "docs", label: "Docs & Connect" },
    { id: "dashboard", label: "Dashboard" },
  ];

  return (
    <header className="sticky top-0 z-40 px-3 sm:px-6 pt-3">
      <nav
        aria-label="Main navigation"
        className="max-w-7xl mx-auto glass-surface rounded-2xl px-4 py-3 flex items-center justify-between"
      >
        <button
          type="button"
          onClick={() => onNavigate("landing")}
          className="flex items-center gap-2.5 text-left focus:outline-none"
        >
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-teal-400 via-cyan-500 to-indigo-600 flex items-center justify-center shadow-md shadow-teal-500/30">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="font-extrabold tracking-tight text-base sm:text-lg bg-gradient-to-r from-teal-400 via-cyan-300 to-indigo-400 bg-clip-text text-transparent">
              Pharmakon
            </span>
            <span className="hidden sm:inline-block ml-2 text-[11px] font-mono uppercase px-2 py-0.5 rounded-full bg-teal-500/15 text-teal-600 dark:text-teal-300 border border-teal-400/30">
              MCP v0.1
            </span>
          </div>
        </button>

        {/* Desktop links */}
        <div className="hidden md:flex items-center gap-1">
          {navItems.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => onNavigate(item.id)}
              className={`px-3.5 py-2 rounded-xl text-sm font-medium transition-all ${
                activePage === item.id
                  ? "bg-white/20 dark:bg-white/15 text-teal-600 dark:text-teal-300 font-semibold"
                  : "text-slate-700 dark:text-slate-300 hover:bg-white/10"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onToggleDarkMode}
            aria-label={darkMode ? "Switch to light mode" : "Switch to dark mode"}
            className="p-2 rounded-xl glass-surface hover:bg-white/20 text-slate-700 dark:text-slate-200"
          >
            {darkMode ? (
              <Sun className="w-4 h-4 text-amber-300" />
            ) : (
              <Moon className="w-4 h-4 text-indigo-700" />
            )}
          </button>

          {user ? (
            <div className="hidden sm:flex items-center gap-2">
              <GlassButton
                size="sm"
                variant="secondary"
                onClick={() => onNavigate("dashboard")}
              >
                <KeyRound className="w-3.5 h-3.5" />
                <span>{user.email.split("@")[0]}</span>
              </GlassButton>
              <GlassButton
                size="sm"
                variant="ghost"
                onClick={onLogout}
                aria-label="Sign out"
              >
                <LogOut className="w-3.5 h-3.5" />
              </GlassButton>
            </div>
          ) : (
            <GlassButton
              size="sm"
              variant="primary"
              onClick={() => onNavigate("auth")}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Get API Key</span>
            </GlassButton>
          )}

          <button
            type="button"
            onClick={() => setMobileOpen((prev) => !prev)}
            aria-label="Toggle mobile menu"
            className="md:hidden p-2 rounded-xl glass-surface text-slate-700 dark:text-slate-200"
          >
            <Menu className="w-4 h-4" />
          </button>
        </div>
      </nav>

      {mobileOpen && (
        <div className="md:hidden max-w-7xl mx-auto mt-2 glass-dense-tint rounded-2xl p-3 flex flex-col gap-1.5">
          {navItems.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => {
                onNavigate(item.id);
                setMobileOpen(false);
              }}
              className="w-full text-left px-3.5 py-2 rounded-xl text-sm font-medium hover:bg-white/10"
            >
              {item.label}
            </button>
          ))}
        </div>
      )}
    </header>
  );
};
