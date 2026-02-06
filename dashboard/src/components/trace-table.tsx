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
      t.service?.toLowerCase().includes(search.toLowerCase()),
  );

  if (traces.length === 0) {
    return (
      <div className="rounded-md border p-12 text-center">
        <p className="text-muted-foreground">No traces yet.</p>
        <p className="mt-2 text-sm text-muted-foreground">
          Connect the SDK with{" "}
          <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
            HttpSink
          </code>{" "}
          to start sending traces.
        </p>
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
              className="flex items-center gap-4 px-4 py-3 text-sm transition-colors hover:bg-accent/50"
            >
              <div
                className={`h-2 w-2 rounded-full ${
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
                </div>
              </div>
              {trace.error_count > 0 && (
                <Badge variant="destructive" className="text-xs">
                  {trace.error_count} error{trace.error_count > 1 ? "s" : ""}
                </Badge>
              )}
              <div className="text-xs text-muted-foreground shrink-0">
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
