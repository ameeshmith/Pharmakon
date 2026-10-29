import React, { useState } from "react";
import { Lock, Mail, Sparkles } from "lucide-react";
import { loginUser, signupUser } from "../api";
import { GlassButton, GlassCard, GlassInput, Tabs } from "../components/ui";
import type { UserProfile } from "../types";

export const AuthPage: React.FC<{
  onAuthenticated: (token: string, user: UserProfile) => void;
  onNotify: (msg: string, type?: "success" | "error" | "info") => void;
}> = ({ onAuthenticated, onNotify }) => {
  const [mode, setMode] = useState<string>("signup");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res =
        mode === "signup"
          ? await signupUser(email, password)
          : await loginUser(email, password);
      onAuthenticated(res.access_token, res.user);
      onNotify(
        mode === "signup"
          ? "Account created! Generate your first MCP API key below."
          : "Welcome back to Pharmakon!",
        "success"
      );
    } catch (err) {
      onNotify(
        err instanceof Error ? err.message : "Authentication failed",
        "error"
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-md mx-auto py-12">
      <GlassCard dense className="space-y-6">
        <div className="flex flex-col items-center text-center space-y-2">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-teal-400 to-indigo-600 flex items-center justify-center shadow-lg">
            <Lock className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-2xl font-extrabold">
            {mode === "signup"
              ? "Create Your Pharmakon Account"
              : "Sign In to Pharmakon"}
          </h1>
          <p className="text-xs text-slate-600 dark:text-slate-300">
            100% free tier • Generate hashed Bearer API keys for Claude Desktop & Cursor.
          </p>
          <Tabs
            tabs={[
              { id: "signup", label: "Sign Up" },
              { id: "login", label: "Log In" },
            ]}
            activeTab={mode}
            onChange={setMode}
          />
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <GlassInput
            id="auth-email"
            label="Email Address"
            type="email"
            required
            placeholder="researcher@university.edu"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <GlassInput
            id="auth-password"
            label="Password"
            type="password"
            required
            minLength={8}
            placeholder="Minimum 8 characters"
            helperText="Hashed with bcrypt (12 rounds). Never stored in plaintext."
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          <GlassButton
            type="submit"
            disabled={submitting}
            className="w-full"
            size="lg"
          >
            {mode === "signup" ? (
              <>
                <Sparkles className="w-4 h-4" />
                <span>
                  {submitting ? "Creating Account..." : "Create Free Account"}
                </span>
              </>
            ) : (
              <>
                <Mail className="w-4 h-4" />
                <span>{submitting ? "Signing In..." : "Sign In"}</span>
              </>
            )}
          </GlassButton>
        </form>
      </GlassCard>
    </div>
  );
};
