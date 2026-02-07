const securityTopics = [
  {
    title: "Zero-dependency SDK",
    description:
      "Pure Python stdlib. No transitive dependencies, no supply chain risk. One package to audit.",
  },
  {
    title: "Transport security",
    description:
      "All API traffic encrypted with TLS 1.3. No plaintext data in transit.",
  },
  {
    title: "Data at rest",
    description:
      "Supabase Postgres with AES-256 encryption. Your trace data is encrypted on disk.",
  },
  {
    title: "API key security",
    description:
      "Keys are hashed with SHA-256 before storage. Only the prefix is visible in the dashboard.",
  },
  {
    title: "Data retention",
    description:
      "Automatic cleanup per plan tier: 7 days (Free), 30 days (Pro), 90 days (Team). No indefinite data hoarding.",
  },
  {
    title: "Access isolation",
    description:
      "All queries are scoped to your team. No cross-tenant data access is possible.",
  },
  {
    title: "Open source",
    description:
      "The SDK is MIT-licensed and available on GitHub. Audit the source code anytime.",
  },
  {
    title: "Responsible disclosure",
    description:
      "Found a vulnerability? Email security@agentguard47.com. We respond within 48 hours.",
  },
];

export default function SecurityPage() {
  return (
    <div className="max-w-3xl space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Security</h1>
        <p className="mt-1 text-muted-foreground">
          AgentGuard is designed with security as a first principle. Zero
          dependencies means zero supply chain risk.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {securityTopics.map((topic) => (
          <div key={topic.title} className="rounded-md border p-4">
            <h3 className="font-medium">{topic.title}</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {topic.description}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
