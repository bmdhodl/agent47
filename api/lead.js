export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  try {
    const { email, source } = req.body || {};
    if (!email || typeof email !== "string") {
      return res.status(400).json({ error: "Missing email" });
    }

    const apiKey = process.env.RESEND_API_KEY;
    if (!apiKey) {
      return res.status(500).json({ error: "Missing RESEND_API_KEY" });
    }

    const fromEmail = process.env.RESEND_FROM_EMAIL || "AgentGuard <pat@bmdpat.com>";
    const notifyEmail = process.env.RESEND_TO_EMAIL || "pat@bmdpat.com";

    const headers = {
      "Authorization": `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    };

    // 1. Notify you about the new signup
    await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers,
      body: JSON.stringify({
        from: fromEmail,
        to: notifyEmail,
        subject: `New AgentGuard signup: ${email}`,
        text: `New signup: ${email}\nSource: ${source || "site"}\nTime: ${new Date().toISOString()}`,
      }),
    });

    // 2. Send welcome email to the user
    const welcomeResp = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers,
      body: JSON.stringify({
        from: fromEmail,
        to: email,
        subject: "You're in — here's how to get your first trace in 60 seconds",
        html: welcomeEmailHtml(),
      }),
    });

    if (!welcomeResp.ok) {
      const errText = await welcomeResp.text();
      return res.status(500).json({ error: "Resend error", detail: errText });
    }

    return res.status(200).json({ ok: true });
  } catch (err) {
    return res.status(500).json({ error: "Server error", detail: String(err) });
  }
}

function welcomeEmailHtml() {
  return `<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:600px;margin:0 auto;padding:20px;color:#1a1a1a;line-height:1.6">

<p>Hey,</p>

<p>Thanks for signing up for AgentGuard.</p>

<p>Here's the fastest way to see what your agents are actually doing:</p>

<pre style="background:#f4f4f5;padding:16px;border-radius:8px;overflow-x:auto;font-size:14px"><code>pip install agentguard47</code></pre>

<pre style="background:#f4f4f5;padding:16px;border-radius:8px;overflow-x:auto;font-size:14px"><code>from agentguard import Tracer, BudgetGuard, JsonlFileSink

tracer = Tracer(
    sink=JsonlFileSink("traces.jsonl"),
    service="my-agent",
    guards=[BudgetGuard(max_cost_usd=5.00)],
)

with tracer.trace("agent.run") as span:
    span.event("step", data={"thought": "search docs"})
    # your agent code here</code></pre>

<p>Then view your traces:</p>

<pre style="background:#f4f4f5;padding:16px;border-radius:8px;overflow-x:auto;font-size:14px"><code>agentguard report traces.jsonl   # summary
agentguard view traces.jsonl     # Gantt timeline in browser</code></pre>

<p><strong>What you get right now (free tier):</strong></p>
<ul>
  <li>10,000 events/month</li>
  <li>7-day retention</li>
  <li>Loop detection, budget enforcement, cost tracking</li>
  <li>Gantt timeline visualization</li>
</ul>

<p>The SDK is MIT-licensed with zero dependencies — nothing to audit, nothing that can break.</p>

<p>Using LangChain? We have a drop-in callback handler: <code>pip install agentguard47[langchain]</code></p>

<p style="margin:24px 0">
  <a href="https://app.agentguard47.com" style="background:#2563eb;color:#fff;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600">Open Dashboard</a>
</p>

<p>Questions? Just reply to this email.</p>

<p>— Pat</p>

<hr style="border:none;border-top:1px solid #e5e7eb;margin:32px 0">
<p style="font-size:12px;color:#6b7280">
  AgentGuard by BMD PAT LLC<br>
  <a href="https://github.com/bmdhodl/agent47" style="color:#6b7280">GitHub</a> · <a href="https://agentguard47.com" style="color:#6b7280">Website</a>
</p>

</body>
</html>`;
}
