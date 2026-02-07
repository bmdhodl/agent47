const faqs = [
  {
    question: "How do I generate an API key?",
    answer:
      'Go to Settings, scroll to the API Keys section, and click "Generate new key". Copy the full key immediately — it won\'t be shown again. You\'ll only see the prefix after that.',
  },
  {
    question: "How do I send traces?",
    answer:
      "Install the SDK with pip install agentguard47, then use the Tracer with an HttpSink pointed at the ingest endpoint. See the code example on the Traces page when you have no traces yet.",
  },
  {
    question: "What counts as an event?",
    answer:
      "Every call to span.event() or span.span() in the SDK counts as one event. A single trace with 5 spans and 3 events = 8 events total against your quota.",
  },
  {
    question: "What's the retention policy?",
    answer:
      "Free plan: 7 days. Pro plan: 30 days. Team plan: 90 days. After the retention window, trace data is automatically deleted. This cannot be changed per-trace.",
  },
  {
    question: "How do I upgrade my plan?",
    answer:
      'Go to Settings, scroll to the Billing section, and click "Manage subscription". You\'ll be taken to Stripe to change your plan. Changes take effect immediately.',
  },
  {
    question: "I need help — how do I contact support?",
    answer:
      "Open an issue on GitHub at github.com/bmdhodl/agent47 or email support@agentguard47.com. We typically respond within 24 hours.",
  },
];

export default function HelpPage() {
  return (
    <div className="max-w-2xl space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Help</h1>
        <p className="mt-1 text-muted-foreground">
          Frequently asked questions and getting started guides.
        </p>
      </div>

      <div className="space-y-3">
        {faqs.map((faq) => (
          <details key={faq.question} className="group rounded-md border">
            <summary className="cursor-pointer px-4 py-3 font-medium hover:bg-accent/50">
              {faq.question}
            </summary>
            <div className="border-t px-4 py-3 text-sm text-muted-foreground">
              {faq.answer}
            </div>
          </details>
        ))}
      </div>
    </div>
  );
}
