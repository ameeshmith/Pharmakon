export type PageRoute = "landing" | "playground" | "dashboard" | "docs" | "auth";

export interface ToolParameter {
  name: string;
  type: "string" | "integer" | "array";
  required: boolean;
  placeholder?: string;
  description: string;
  enum?: string[];
  default?: number | string;
  min?: number;
  max?: number;
}

export interface ToolSchema {
  name: string;
  title: string;
  category: string;
  description: string;
  parameters: ToolParameter[];
  example_args: Record<string, unknown>;
}

export interface UserProfile {
  id: number;
  email: string;
  created_at: string;
}

export interface APIKeyItem {
  id: number;
  name: string;
  key_prefix: string;
  raw_key?: string;
  is_active: boolean;
  created_at: string;
  revoked_at?: string | null;
  last_used_at?: string | null;
  notice?: string;
}

export interface UsageStatsResponse {
  total_calls: number;
  average_latency_ms: number;
  active_keys_count: number;
  by_day: { date: string; count: number }[];
  by_tool: { tool: string; count: number }[];
  recent_calls: {
    id: number;
    tool_name: string;
    latency_ms: number;
    status: string;
    key_name: string;
    key_prefix: string;
    timestamp: string;
  }[];
  rate_limit: {
    limit_per_minute: number;
    remaining_minute: number;
    limit_per_day: number;
    remaining_day: number;
  };
}
