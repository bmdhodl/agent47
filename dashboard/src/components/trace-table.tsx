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
      <div className="rounded-md border p-6 text-center sm:p-12">
        <p className="text-lg font-medium text-muted-foreground">No traces yet</p>
        <p className="mt-2 text-sm text-muted-foreground">
          Install the SDK and point it at your dashboard to start collecting traces.
        </p>
        <div className="mx-auto mt-4 max-w-lg rounded-md bg-muted p-3 text-left overflow-x-auto sm:p-4">
          <p className="mb-2 text-xs font-medium text-muted-foreground">Quick start — 4 lines of Python:</p>
          <pre className="text-xs leading-relaxed whitespace-pre-wrap break-all sm:whitespace-pre sm:break-normal">{`from agentguard47 import Tracer
from agentguard47.sinks import HttpSink

tracer = Tracer(sink=HttpSink(
    url="https://your-dashboard.vercel.app/api/events",
    api_key="ag_YOUR_KEY_HERE",
))`}</pre>
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
