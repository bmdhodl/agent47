import { Shield, Lock, Database, Key, Users, Github, Mail } from "lucide-react";
import type { LucideIcon } from "lucide-react";

type Status = "current" | "planned";

interface TrustItem {
  area: string;
  status: Status;
  details: string;
}

interface TrustSection {
  title: string;
  icon: LucideIcon;
  items: TrustItem[];
}

const trustSections: TrustSection[] = [
  {
    title: "Authentication & Access",
    icon: Key,
    items: [
      { area: "User auth", status: "current", details: "Email/password with bcrypt hashing, NextAuth JWT sessions" },
      { area: "API key security", status: "current", details: "SHA-256 hashed before storage, prefix-only display, soft-delete revocation" },
      { area: "Password reset", status: "planned", details: "Token-based email reset flow (v0.6.0)" },
      { area: "API key rotation & expiry", status: "planned", details: "Key rotation, expiry dates, last-used tracking (v1.0)" },
      { area: "SSO / SAML", status: "planned", details: "Planned for Team tier (post-1.0)" },
    ],
  },
  {
    title: "Encryption",
    icon: Lock,
    items: [
      { area: "In transit", status: "current", details: "TLS 1.3 enforced by Vercel (dashboard) and Supabase (database)" },
      { area: "At rest", status: "current", details: "AES-256 via Supabase Postgres transparent encryption" },
      { area: "Secret handling", status: "current", details: "API keys never stored raw. Service secrets in env vars. No secrets in logs." },
    ],
  },
  {
    title: "Data Handling & Privacy",
    icon: Database,
    items: [
      { area: "Tenant isolation", status: "current", details: "All queries scoped by team_id. No cross-tenant access possible." },
      { area: "Data retention", status: "current", details: "Auto-cleanup cron per plan: 7d (Free), 30d (Pro), 90d (Team)" },
      { area: "Data capture", status: "current", details: "SDK never auto-captures prompts or responses. Only what you explicitly send." },
      { area: "On-demand deletion", status: "planned", details: "DELETE API for GDPR right-to-erasure (v1.0)" },
    ],
  },
  {
    title: "Team & Access Controls",
    icon: Users,
    items: [
      { area: "Team ownership", status: "current", details: "Single owner per team with full control" },
      { area: "RBAC", status: "planned", details: "Owner/admin/member roles with team_members table (v0.7.0)" },
      { area: "Audit logs", status: "planned", details: "API key CRUD, team changes, plan changes (v0.7.0)" },
    ],
  },
  {
    title: "Ingestion & Reliability",
    icon: Shield,
    items: [
      { area: "SDK transport", status: "current", details: "HttpSink: batched, background thread, atexit flush. Failures logged, never crash." },
      { area: "Rate limiting", status: "current", details: "100 requests/min per IP on ingest. Quota enforcement per plan." },
      { area: "Compression & retry", status: "planned", details: "Gzip compression, exponential backoff, idempotency keys (v0.8.0)" },
    ],
  },
  {
    title: "Supply Chain",
    icon: Github,
    items: [
      { area: "SDK dependencies", status: "current", details: "Zero runtime dependencies. Pure Python stdlib." },
      { area: "Open source", status: "current", details: "MIT-licensed. Full source on GitHub." },
    ],
  },
];

function StatusBadge({ status }: { status: Status }) {
  return (
    <span
      className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${
        status === "current"
          ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
          : "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400"
      }`}
    >
      {status === "current" ? "Current" : "Planned"}
    </span>
  );
}

export default function SecurityPage() {
  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Security & Trust</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Our security posture at a glance. We&apos;re transparent about what&apos;s shipped vs. planned.
        </p>
      </div>

      {trustSections.map((section) => (
        <div key={section.title} className="space-y-2">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-muted">
              <section.icon className="h-4 w-4 text-muted-foreground" />
            </div>
            <h2 className="text-lg font-semibold">{section.title}</h2>
          </div>
          <div className="rounded-xl border bg-card">
            <div className="divide-y">
              {section.items.map((item) => (
                <div key={item.area} className="flex items-start gap-3 px-4 py-3 text-sm">
                  <div className="shrink-0 pt-0.5">
                    <StatusBadge status={item.status} />
                  </div>
                  <div className="min-w-0">
                    <div className="font-medium">{item.area}</div>
                    <div className="text-muted-foreground">{item.details}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ))}

      <div className="rounded-xl border bg-card p-5 transition-colors hover:bg-accent/30">
        <div className="flex items-start gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
            <Mail className="h-4 w-4 text-muted-foreground" />
          </div>
          <div>
            <h3 className="font-medium">Security Contact</h3>
            <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
              Found a vulnerability? Email security@agentguard47.com. We respond within 48 hours.
            </p>
          </div>
        </div>
      </div>

      <p className="text-xs text-muted-foreground">
        Last updated: February 2026 (v0.5.0)
      </p>
    </div>
  );
}
