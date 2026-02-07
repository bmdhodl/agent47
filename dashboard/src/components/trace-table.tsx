"use client";

import { useState } from "react";
import Link from "next/link";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
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
      <div className="rounded-md border p-6 sm:p-10">
        <h2 className="text-lg font-semibold">Get started in 4 steps</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Your first trace will appear here once connected.
        </p>

        <div className="mt-6 space-y-4">
          <div className="flex gap-3">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">1</span>
            <div>
              <p className="text-sm font-medium">Generate an API key</p>
              <p className="text-sm text-muted-foreground">
                Go to{" "}
                <Link href="/settings" className="underline hover:text-foreground">
                  Settings
                </Link>{" "}
                and create a new API key. Copy it immediately — you won&apos;t see it again.
              </p>
            </div>
          </div>

          <div className="flex gap-3">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">2</span>
            <div>
              <p className="text-sm font-medium">Install the SDK</p>
              <div className="mt-1 rounded-md bg-muted px-3 py-2">
                <code className="text-xs">pip install agentguard47</code>
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">3</span>
            <div>
              <p className="text-sm font-medium">Add 3 lines of Python</p>
              <div className="mt-1 rounded-md bg-muted p-3 overflow-x-auto">
                <pre className="text-xs leading-relaxed whitespace-pre">{`from agentguard47 import Tracer
from agentguard47.sinks import HttpSink

tracer = Tracer(sink=HttpSink(
    url="https://app.agentguard47.com/api/ingest",
    api_key="ag_YOUR_KEY_HERE",
))`}</pre>
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">4</span>
            <div>
              <p className="text-sm font-medium">Send a trace</p>
              <p className="text-sm text-muted-foreground">
                Run your agent — your first trace will appear here automatically.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <Input
        placeholder="Search traces..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="max-w-sm"
      />
      <div className="rounded-md border">
        <div className="divide-y">
          {filtered.map((trace) => (
            <Link
              key={trace.trace_id}
              href={`/traces/${trace.trace_id}`}
              className="flex items-center gap-3 px-3 py-3 text-sm transition-colors hover:bg-accent/50 sm:gap-4 sm:px-4"
            >
              <div
                className={`h-2 w-2 shrink-0 rounded-full ${
                  trace.error_count > 0 ? "bg-red-400" : "bg-green-400"
                }`}
              />
              <div className="flex-1 min-w-0">
                <div className="font-mono text-sm truncate">
                  {trace.root_name || trace.trace_id.slice(0, 8)}
                </div>
                <div className="text-xs text-muted-foreground">
                  {trace.service} &middot; {trace.event_count} events
                  {trace.duration_ms
                    ? ` · ${trace.duration_ms.toFixed(1)}ms`
                    : ""}
                  {trace.total_cost != null && trace.total_cost > 0 && (
                    <span className="text-green-600 dark:text-green-400">
                      {" · "}${trace.total_cost < 0.01 ? trace.total_cost.toFixed(4) : trace.total_cost.toFixed(2)}
                    </span>
                  )}
                  {trace.api_key_name && (
                    <span className="hidden sm:inline"> · {trace.api_key_name}</span>
                  )}
                </div>
              </div>
              {trace.error_count > 0 && (
                <Badge variant="destructive" className="text-xs shrink-0">
                  {trace.error_count} error{trace.error_count > 1 ? "s" : ""}
                </Badge>
              )}
              <div className="hidden text-xs text-muted-foreground shrink-0 sm:block">
                {new Date(trace.started_at).toLocaleString()}
              </div>
            </Link>
          ))}
          {filtered.length === 0 && (
            <div className="p-4 text-center text-sm text-muted-foreground">
              No matching traces
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
