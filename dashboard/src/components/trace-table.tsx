"use client";

import { useState } from "react";
import Link from "next/link";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Activity, Search, ArrowRight } from "lucide-react";
import type { TraceRow } from "@/lib/queries";

export function TraceTable({ traces }: { traces: TraceRow[] }) {
  const [search, setSearch] = useState("");

  const filtered = traces.filter(
    (t) =>
      t.root_name?.toLowerCase().includes(search.toLowerCase()) ||
      t.trace_id.toLowerCase().includes(search.toLowerCase()) ||
      t.service?.toLowerCase().includes(search.toLowerCase()) ||
      t.api_key_name?.toLowerCase().includes(search.toLowerCase()),
  );

  if (traces.length === 0) {
    return (
      <div className="rounded-xl border bg-card p-8 sm:p-12">
        <div className="mx-auto max-w-md text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-muted">
            <Activity className="h-6 w-6 text-muted-foreground" />
          </div>
          <h2 className="text-lg font-semibold">Get started in 4 steps</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Your first trace will appear here once connected.
          </p>
        </div>

        <div className="mx-auto mt-8 max-w-lg space-y-4">
          {[
            {
              step: 1,
              title: "Generate an API key",
              content: (
                <p className="text-sm text-muted-foreground">
                  Go to{" "}
                  <Link
                    href="/settings"
                    className="font-medium text-foreground underline underline-offset-4 hover:no-underline"
                  >
                    Settings
                  </Link>{" "}
                  and create a new key. Copy it immediately.
                </p>
              ),
            },
            {
              step: 2,
              title: "Install the SDK",
              content: (
                <div className="mt-1.5 rounded-lg bg-muted/50 px-3 py-2">
                  <code className="text-xs sm:text-sm">pip install agentguard47</code>
                </div>
              ),
            },
            {
              step: 3,
              title: "Add 3 lines of Python",
              content: (
                <div className="mt-1.5 rounded-lg bg-muted/50 p-3 overflow-x-auto">
                  <pre className="text-xs leading-relaxed whitespace-pre sm:text-sm">{`from agentguard47 import Tracer
from agentguard47.sinks import HttpSink

tracer = Tracer(sink=HttpSink(
    url="https://app.agentguard47.com/api/ingest",
    api_key="ag_YOUR_KEY_HERE",
))`}</pre>
                </div>
              ),
            },
            {
              step: 4,
              title: "Send a trace",
              content: (
                <p className="text-sm text-muted-foreground">
                  Run your agent — your first trace appears here automatically.
                </p>
              ),
            },
          ].map(({ step, title, content }) => (
            <div key={step} className="flex gap-4">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
                {step}
              </div>
              <div className="flex-1 pt-0.5">
                <p className="text-sm font-medium">{title}</p>
                {content}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search traces..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>
      <div className="rounded-xl border bg-card">
        <div className="divide-y">
          {filtered.map((trace) => (
            <Link
              key={trace.trace_id}
              href={`/traces/${trace.trace_id}`}
              className="group flex items-center gap-3 px-4 py-3.5 text-sm transition-colors hover:bg-accent/50 sm:gap-4 sm:px-5"
            >
              <div
                className={`h-2.5 w-2.5 shrink-0 rounded-full ring-2 ring-offset-2 ring-offset-card ${
                  trace.error_count > 0
                    ? "bg-red-500 ring-red-500/20"
                    : "bg-emerald-500 ring-emerald-500/20"
                }`}
              />
              <div className="flex-1 min-w-0">
                <div className="font-mono text-sm font-medium truncate">
                  {trace.root_name || trace.trace_id.slice(0, 8)}
                </div>
                <div className="mt-0.5 flex flex-wrap items-center gap-x-2 text-xs text-muted-foreground">
                  <span>{trace.service}</span>
                  <span className="text-border">|</span>
                  <span>{trace.event_count} events</span>
                  {trace.duration_ms != null && (
                    <>
                      <span className="text-border">|</span>
                      <span>{trace.duration_ms.toFixed(1)}ms</span>
                    </>
                  )}
                  {trace.api_key_name && (
                    <span className="hidden sm:inline">
                      <span className="text-border">|</span>{" "}
                      {trace.api_key_name}
                    </span>
                  )}
                </div>
              </div>
              {trace.error_count > 0 && (
                <Badge variant="destructive" className="shrink-0 text-xs">
                  {trace.error_count} error{trace.error_count > 1 ? "s" : ""}
                </Badge>
              )}
              <div className="hidden shrink-0 text-right text-xs text-muted-foreground sm:block">
                {new Date(trace.started_at).toLocaleString()}
              </div>
              <ArrowRight className="hidden h-4 w-4 shrink-0 text-muted-foreground/50 transition-transform group-hover:translate-x-0.5 group-hover:text-foreground sm:block" />
            </Link>
          ))}
          {filtered.length === 0 && (
            <div className="p-8 text-center text-sm text-muted-foreground">
              No matching traces
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
