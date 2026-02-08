"use client";

import { useState } from "react";
import { Share2, Check, Loader2 } from "lucide-react";

export function ShareButton({ traceId }: { traceId: string }) {
  const [state, setState] = useState<"idle" | "loading" | "copied">("idle");
  const [url, setUrl] = useState<string | null>(null);

  async function handleShare() {
    if (state === "copied" && url) {
      await navigator.clipboard.writeText(url);
      return;
    }

    setState("loading");
    try {
      const res = await fetch(`/api/v1/traces/${encodeURIComponent(traceId)}/share`, {
        method: "POST",
      });

      if (!res.ok) {
        const data = await res.json();
        alert(data.error || "Failed to create share link");
        setState("idle");
        return;
      }

      const data = await res.json();
      setUrl(data.url);
      await navigator.clipboard.writeText(data.url);
      setState("copied");
      setTimeout(() => setState("idle"), 3000);
    } catch {
      alert("Failed to create share link");
      setState("idle");
    }
  }

  return (
    <button
      onClick={handleShare}
      disabled={state === "loading"}
      className="inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground disabled:opacity-50"
    >
      {state === "loading" ? (
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
      ) : state === "copied" ? (
        <Check className="h-3.5 w-3.5 text-green-500" />
      ) : (
        <Share2 className="h-3.5 w-3.5" />
      )}
      {state === "copied" ? "Link copied" : "Share"}
    </button>
  );
}
