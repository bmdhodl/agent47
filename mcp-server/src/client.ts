const DEFAULT_URL = "https://app.agentguard47.com";

export class AgentGuardClient {
  private baseUrl: string;
  private apiKey: string;

  constructor() {
    const apiKey = process.env.AGENTGUARD_API_KEY;
    if (!apiKey) {
      throw new Error(
        "AGENTGUARD_API_KEY environment variable is required. " +
        "Generate one at your AgentGuard dashboard under Settings > API Keys."
      );
    }
    this.apiKey = apiKey;
    this.baseUrl = (process.env.AGENTGUARD_URL || DEFAULT_URL).replace(/\/$/, "");
  }

  private async fetch<T>(path: string, params?: Record<string, string>): Promise<T> {
    const url = new URL(`${this.baseUrl}${path}`);
    if (params) {
      for (const [key, value] of Object.entries(params)) {
        if (value) url.searchParams.set(key, value);
      }
    }

    const res = await fetch(url.toString(), {
      headers: { Authorization: `Bearer ${this.apiKey}` },
    });

    if (!res.ok) {
      const body = await res.text();
      throw new Error(`AgentGuard API error (${res.status}): ${body}`);
    }

    return res.json() as Promise<T>;
  }

  async getTraces(opts?: {
    limit?: string;
    offset?: string;
    service?: string;
    since?: string;
    until?: string;
  }) {
    return this.fetch<{ traces: unknown[] }>("/api/v1/traces", opts);
  }

  async getTrace(traceId: string) {
    return this.fetch<{ trace_id: string; events: unknown[] }>(
      `/api/v1/traces/${encodeURIComponent(traceId)}`
    );
  }

  async getAlerts(opts?: { limit?: string; since?: string }) {
    return this.fetch<{ alerts: unknown[] }>("/api/v1/alerts", opts);
  }

  async getUsage() {
    return this.fetch<{
      plan: string;
      current_month: string;
      event_count: number;
      event_limit: number;
      retention_days: number;
      max_keys: number;
      max_users: number;
    }>("/api/v1/usage");
  }

  async getCosts() {
    return this.fetch<{
      monthly: { total_cost: number; trace_count: number };
      by_model: Array<{ model: string; total_cost: number; call_count: number }>;
      savings: { guard_events: number; estimated_savings: number };
    }>("/api/v1/costs");
  }
}
