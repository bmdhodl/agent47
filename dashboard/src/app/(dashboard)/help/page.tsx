import { HelpCircle } from "lucide-react";

const faqs = [
  {
    question: "How do I generate an API key?",
    answer:
      'Go to Settings, scroll to the API Keys section, and click "Generate key". Copy the full key immediately — it won\'t be shown again. You\'ll only see the prefix after that.',
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
      'Go to Settings, scroll to the Billing section, and click "Upgrade". You\'ll be taken to Stripe to complete your subscription. Changes take effect immediately.',
  },
  {
    question: "I need help — how do I contact support?",
    answer:
      "Open an issue on GitHub at github.com/bmdhodl/agent47 or email pat@bmdpat.com. We typically respond within 24 hours.",
  },
];

export default function HelpPage() {
  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Help</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Frequently asked questions and getting started guides.
        </p>
      </div>

      <div className="space-y-3">
        {faqs.map((faq) => (
          <details key={faq.question} className="group rounded-xl border bg-card">
            <summary className="flex cursor-pointer items-center gap-3 px-5 py-4 font-medium transition-colors hover:bg-accent/50 [&::-webkit-details-marker]:hidden">
              <HelpCircle className="h-4 w-4 shrink-0 text-muted-foreground transition-transform group-open:rotate-90" />
              {faq.question}
            </summary>
            <div className="border-t px-5 py-4 text-sm leading-relaxed text-muted-foreground">
              {faq.answer}
            </div>
          </details>
        ))}
      </div>
    </div>
  );
}
