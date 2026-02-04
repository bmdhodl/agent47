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

    const fromEmail = process.env.RESEND_FROM_EMAIL || "AgentGuard <onboarding@resend.dev>";
    const toEmail = process.env.RESEND_TO_EMAIL || "pat@bmdpat.com";

    const payload = {
      from: fromEmail,
      to: toEmail,
      subject: "New AgentGuard early access",
      text: `Email: ${email}\nSource: ${source || "site"}`,
    };

    const resp = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!resp.ok) {
      const errText = await resp.text();
      return res.status(500).json({ error: "Resend error", detail: errText });
    }

    return res.status(200).json({ ok: true });
  } catch (err) {
    return res.status(500).json({ error: "Server error", detail: String(err) });
  }
}
