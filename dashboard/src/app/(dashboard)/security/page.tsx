import { Shield, Lock, Database, Key, Clock, Users, Github, Mail } from "lucide-react";
import type { LucideIcon } from "lucide-react";

const securityTopics: {
  title: string;
  description: string;
  icon: LucideIcon;
}[] = [
  {
    title: "Zero-dependency SDK",
    description:
      "Pure Python stdlib. No transitive dependencies, no supply chain risk. One package to audit.",
    icon: Shield,
  },
  {
    title: "Transport security",
    description:
      "All API traffic encrypted with TLS 1.3. No plaintext data in transit.",
    icon: Lock,
  },
  {
    title: "Data at rest",
    description:
      "Supabase Postgres with AES-256 encryption. Your trace data is encrypted on disk.",
    icon: Database,
  },
  {
    title: "API key security",
    description:
      "Keys are hashed with SHA-256 before storage. Only the prefix is visible in the dashboard.",
    icon: Key,
  },
  {
    title: "Data retention",
    description:
      "Automatic cleanup per plan tier: 7 days (Free), 30 days (Pro), 90 days (Team). No indefinite data hoarding.",
    icon: Clock,
  },
  {
    title: "Access isolation",
    description:
      "All queries are scoped to your team. No cross-tenant data access is possible.",
    icon: Users,
  },
  {
    title: "Open source",
    description:
      "The SDK is MIT-licensed and available on GitHub. Audit the source code anytime.",
    icon: Github,
  },
  {
    title: "Responsible disclosure",
    description:
      "Found a vulnerability? Email security@agentguard47.com. We respond within 48 hours.",
    icon: Mail,
  },
];

export default function SecurityPage() {
  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Security</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          AgentGuard is designed with security as a first principle. Zero
          dependencies means zero supply chain risk.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {securityTopics.map((topic) => (
          <div
            key={topic.title}
            className="rounded-xl border bg-card p-5 transition-colors hover:bg-accent/30"
          >
            <div className="flex items-start gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
                <topic.icon className="h-4 w-4 text-muted-foreground" />
              </div>
              <div>
                <h3 className="font-medium">{topic.title}</h3>
                <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                  {topic.description}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
