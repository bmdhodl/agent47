"use client";

import { useState } from "react";
import type { EventRow } from "@/lib/queries";

function classifyName(name: string): string {
  if (name.startsWith("reasoning")) return "reasoning";
  if (name.startsWith("tool")) return "tool";
  if (name.startsWith("llm")) return "llm";
  if (name.startsWith("guard")) return "guard";
  if (name.includes("error")) return "error";
  return "default";
}

const TYPE_COLORS: Record<string, string> = {
  reasoning: "#60a5fa",
  tool: "#4ade80",
  llm: "#a78bfa",
  guard: "#fbbf24",
  error: "#f87171",
  default: "#64748b",
};

interface GanttRow {
  name: string;
  startMs: number;
  durMs: number;
  type: string;
  event: EventRow;
  endEvent: EventRow | null;
  depth: number;
}

function buildStats(events: EventRow[]) {
  const spans = events.filter((e) => e.kind === "span");
  const spanStarts = spans.filter((e) => e.phase === "start");
  const spanEnds = spans.filter((e) => e.phase === "end");
  const evts = events.filter((e) => e.kind === "event");
  const reasoning = evts.filter((e) => e.name === "reasoning.step").length;
  const toolResults = evts.filter((e) => e.name === "tool.result").length;
  const llmResults = evts.filter((e) => e.name === "llm.result").length;
  const loops = evts.filter((e) => e.name === "guard.loop_detected").length;
  const errors = events.filter((e) => e.error != null).length;

  let totalMs = 0;
  spanEnds.forEach((e) => {
    if (e.duration_ms && e.duration_ms > totalMs) totalMs = e.duration_ms;
  });

  const totalTokens = events.reduce((acc, e) => {
    const d = (e.data || {}) as Record<string, Record<string, number>>;
    const u = d.token_usage || d.usage || {};
    return acc + (u.total_tokens || 0);
  }, 0);

  return {
    events: events.length,
    spans: spanStarts.length,
    runtime: totalMs > 0 ? `${totalMs.toFixed(1)}ms` : "-",
    reasoning,
    toolCalls: toolResults,
    llmCalls: llmResults,
    loops,
    errors,
    tokens: totalTokens || 0,
  };
}

function buildGanttRows(events: EventRow[]): {
  rows: GanttRow[];
  timeRange: number;
} {
  const spans = events.filter((e) => e.kind === "span");
  const spanEnds = spans.filter((e) => e.phase === "end");

  const minTs = Math.min(...events.map((e) => e.ts));
  const maxTs = Math.max(...events.map((e) => e.ts));
  const maxDur = Math.max(...spanEnds.map((e) => e.duration_ms || 0), 1);
  const timeRange = Math.max((maxTs - minTs) * 1000, maxDur, 1);

  const spanMap: Record<
    string,
    { start?: EventRow; end?: EventRow }
  > = {};
  spans.forEach((e) => {
    if (!spanMap[e.span_id]) spanMap[e.span_id] = {};
    if (e.phase === "start") spanMap[e.span_id].start = e;
    if (e.phase === "end") spanMap[e.span_id].end = e;
  });

  const rows: GanttRow[] = [];
  Object.values(spanMap).forEach((pair) => {
    const s = pair.start || pair.end;
    if (!s) return;
    const dur = pair.end ? pair.end.duration_ms || 0 : 0;
    const startMs = (s.ts - minTs) * 1000;
    rows.push({
      name: s.name,
      startMs,
      durMs: dur,
      type: classifyName(s.name),
      event: s,
      endEvent: pair.end || null,
      depth: s.parent_id ? 1 : 0,
    });
  });

  rows.sort((a, b) => a.startMs - b.startMs);
  return { rows, timeRange };
}

export function TraceGantt({ events }: { events: EventRow[] }) {
  const [selected, setSelected] = useState<GanttRow | null>(null);
  const stats = buildStats(events);
  const { rows, timeRange } = buildGanttRows(events);

  return (
    <div className="space-y-4">
      {/* Stats cards */}
      <div className="grid grid-cols-3 gap-3 sm:grid-cols-5 lg:grid-cols-9">
        {[
          { label: "Events", value: stats.events },
          { label: "Spans", value: stats.spans },
          { label: "Runtime", value: stats.runtime },
          { label: "Reasoning", value: stats.reasoning },
          { label: "Tool calls", value: stats.toolCalls },
          { label: "LLM calls", value: stats.llmCalls },
          {
            label: "Loop hits",
            value: stats.loops,
            warn: stats.loops > 0,
          },
          {
            label: "Errors",
            value: stats.errors,
            warn: stats.errors > 0,
          },
          { label: "Tokens", value: stats.tokens || "-" },
        ].map((card) => (
          <div
            key={card.label}
            className="rounded-md border bg-card p-3 text-center"
          >
            <div className="text-xs text-muted-foreground">{card.label}</div>
            <div
              className={`mt-1 text-lg font-semibold ${
                "warn" in card && card.warn
                  ? "text-red-400"
                  : ""
              }`}
            >
              {card.value}
            </div>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 text-xs">
        {Object.entries(TYPE_COLORS).map(([type, color]) => (
          <div key={type} className="flex items-center gap-1.5">
            <div
              className="h-2.5 w-2.5 rounded-sm"
              style={{ backgroundColor: color }}
            />
            <span className="capitalize text-muted-foreground">{type}</span>
          </div>
        ))}
      </div>

      {/* Gantt chart */}
      <div className="rounded-md border bg-card">
        {rows.length === 0 ? (
          <div className="p-8 text-center text-sm text-muted-foreground">
            No spans to display
          </div>
        ) : (
          <div className="divide-y">
            {rows.map((row, i) => {
              const left = (row.startMs / timeRange) * 100;
              const width =
                row.durMs > 0
                  ? Math.max((row.durMs / timeRange) * 100, 0.3)
                  : 0.3;

              return (
                <button
                  key={`${row.event.span_id}-${i}`}
                  className={`flex w-full items-center gap-3 px-4 py-2 text-left text-sm transition-colors hover:bg-accent/50 ${
                    selected?.event.span_id === row.event.span_id
                      ? "bg-accent/30"
                      : ""
                  }`}
                  onClick={() =>
                    setSelected(
                      selected?.event.span_id === row.event.span_id
                        ? null
                        : row,
                    )
                  }
                >
                  <div
                    className="w-48 shrink-0 truncate font-mono text-xs"
                    style={{ paddingLeft: row.depth * 16 }}
                  >
                    {row.name}
                  </div>
                  <div className="relative flex-1 h-5">
                    <div
                      className="absolute top-1 h-3 rounded-sm"
                      style={{
                        left: `${left}%`,
                        width: `${width}%`,
                        backgroundColor: TYPE_COLORS[row.type] ?? "#64748b",
                      }}
                    />
                  </div>
                  <div className="w-20 shrink-0 text-right font-mono text-xs text-muted-foreground">
                    {row.durMs > 0 ? `${row.durMs.toFixed(1)}ms` : "-"}
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Detail panel */}
      {selected && (
        <div className="rounded-md border bg-card p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-mono text-sm font-medium">{selected.name}</h3>
            <button
              className="text-xs text-muted-foreground hover:text-foreground"
              onClick={() => setSelected(null)}
            >
              Close
            </button>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
            <div>
              <span className="text-muted-foreground">Kind:</span>{" "}
              {selected.event.kind}
            </div>
            <div>
              <span className="text-muted-foreground">Phase:</span>{" "}
              {selected.event.phase}
            </div>
            <div>
              <span className="text-muted-foreground">Duration:</span>{" "}
              {selected.durMs > 0 ? `${selected.durMs.toFixed(1)}ms` : "-"}
            </div>
            <div>
              <span className="text-muted-foreground">Service:</span>{" "}
              {selected.event.service}
            </div>
          </div>
          {selected.event.error && (
            <div className="rounded-md bg-red-500/10 p-3 text-xs">
              <div className="font-medium text-red-400">
                {selected.event.error.type}
              </div>
              <div className="mt-1 text-red-300">
                {selected.event.error.message}
              </div>
            </div>
          )}
          {Object.keys(selected.event.data).length > 0 && (
            <pre className="max-h-48 overflow-auto rounded-md bg-muted p-3 text-xs">
              {JSON.stringify(selected.event.data, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
