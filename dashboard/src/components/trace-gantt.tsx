"use client";

import { useState } from "react";
import { X } from "lucide-react";
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

  const spanMap: Record<string, { start?: EventRow; end?: EventRow }> = {};
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

function StatCard({
  label,
  value,
  warn,
}: {
  label: string;
  value: string | number;
  warn?: boolean;
}) {
  return (
    <div className="rounded-lg border bg-card p-3">
      <div className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground/70">
        {label}
      </div>
      <div
        className={`mt-1 text-lg font-semibold tabular-nums truncate ${
          warn ? "text-red-400" : ""
        }`}
      >
        {value}
      </div>
    </div>
  );
}

export function TraceGantt({ events }: { events: EventRow[] }) {
  const [selected, setSelected] = useState<GanttRow | null>(null);
  const stats = buildStats(events);
  const { rows, timeRange } = buildGanttRows(events);

  return (
    <div className="space-y-5">
      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-5 lg:grid-cols-9 sm:gap-3">
        <StatCard label="Events" value={stats.events} />
        <StatCard label="Spans" value={stats.spans} />
        <StatCard label="Runtime" value={stats.runtime} />
        <StatCard label="Reasoning" value={stats.reasoning} />
        <StatCard label="Tool calls" value={stats.toolCalls} />
        <StatCard label="LLM calls" value={stats.llmCalls} />
        <StatCard label="Loop hits" value={stats.loops} warn={stats.loops > 0} />
        <StatCard label="Errors" value={stats.errors} warn={stats.errors > 0} />
        <StatCard label="Tokens" value={stats.tokens || "-"} />
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
      <div className="rounded-xl border bg-card overflow-x-auto">
        {rows.length === 0 ? (
          <div className="p-12 text-center text-sm text-muted-foreground">
            No spans to display
          </div>
        ) : (
          <div className="divide-y min-w-[480px]">
            {rows.map((row, i) => {
              const left = (row.startMs / timeRange) * 100;
              const width =
                row.durMs > 0
                  ? Math.max((row.durMs / timeRange) * 100, 0.5)
                  : 0.5;
              const isSelected =
                selected?.event.span_id === row.event.span_id;

              return (
                <button
                  key={`${row.event.span_id}-${i}`}
                  className={`group flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm transition-colors hover:bg-accent/50 sm:gap-3 ${
                    isSelected ? "bg-accent/40" : ""
                  }`}
                  onClick={() => setSelected(isSelected ? null : row)}
                >
                  <div
                    className="w-28 shrink-0 truncate font-mono text-xs text-muted-foreground group-hover:text-foreground sm:w-44"
                    style={{ paddingLeft: row.depth * 16 }}
                  >
                    {row.name}
                  </div>
                  <div className="relative flex-1 h-6">
                    <div
                      className="absolute top-1.5 h-3 rounded-full transition-all"
                      style={{
                        left: `${left}%`,
                        width: `${width}%`,
                        backgroundColor: TYPE_COLORS[row.type] ?? "#64748b",
                        opacity: isSelected ? 1 : 0.75,
                      }}
                    />
                  </div>
                  <div className="w-16 shrink-0 text-right font-mono text-xs text-muted-foreground sm:w-20">
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
        <div className="rounded-xl border bg-card overflow-hidden">
          <div className="flex items-center justify-between border-b px-4 py-3">
            <div className="flex items-center gap-2">
              <div
                className="h-3 w-3 rounded-sm"
                style={{
                  backgroundColor:
                    TYPE_COLORS[selected.type] ?? "#64748b",
                }}
              />
              <h3 className="font-mono text-sm font-medium">
                {selected.name}
              </h3>
            </div>
            <button
              className="rounded-lg p-1 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
              onClick={() => setSelected(null)}
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="p-4 space-y-4">
            <div className="grid grid-cols-2 gap-3 text-xs sm:grid-cols-3 md:grid-cols-5">
              {[
                { label: "Kind", value: selected.event.kind },
                { label: "Phase", value: selected.event.phase },
                {
                  label: "Duration",
                  value:
                    selected.durMs > 0
                      ? `${selected.durMs.toFixed(1)}ms`
                      : "-",
                },
                { label: "Service", value: selected.event.service },
                {
                  label: "Key",
                  value: selected.event.api_key_name || "\u2014",
                },
              ].map((item) => (
                <div key={item.label}>
                  <span className="text-muted-foreground">{item.label}</span>
                  <div className="mt-0.5 font-medium">{item.value}</div>
                </div>
              ))}
            </div>

            {selected.event.error && (
              <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-xs">
                <div className="font-medium text-red-400">
                  {selected.event.error.type}
                </div>
                <div className="mt-1 text-red-300">
                  {selected.event.error.message}
                </div>
              </div>
            )}

            {(() => {
              const data = (selected.endEvent?.data ||
                selected.event.data ||
                {}) as Record<string, unknown>;
              const tokenUsage = (data.token_usage || data.usage) as
                | Record<string, number>
                | undefined;
              const isLlm = selected.type === "llm";
              const isTool = selected.type === "tool";
              const isGuard = selected.type === "guard";

              return (
                <>
                  {isLlm && tokenUsage && (
                    <div className="rounded-lg bg-purple-500/10 border border-purple-500/20 p-3 text-xs">
                      <span className="font-medium text-purple-400">
                        Tokens:{" "}
                      </span>
                      {tokenUsage.total_tokens ?? "?"}
                      {tokenUsage.prompt_tokens != null && (
                        <span className="text-muted-foreground">
                          {" "}
                          (prompt: {tokenUsage.prompt_tokens}, completion:{" "}
                          {tokenUsage.completion_tokens ?? "?"})
                        </span>
                      )}
                    </div>
                  )}
                  {isTool &&
                    (data.input != null || data.output != null) && (
                      <div className="space-y-2">
                        {data.input != null && (
                          <div className="rounded-lg bg-green-500/10 border border-green-500/20 p-3 text-xs">
                            <span className="font-medium text-green-400">
                              Input:{" "}
                            </span>
                            <span className="text-green-300">
                              {String(data.input).slice(0, 500)}
                            </span>
                          </div>
                        )}
                        {data.output != null && (
                          <div className="rounded-lg bg-green-500/10 border border-green-500/20 p-3 text-xs">
                            <span className="font-medium text-green-400">
                              Output:{" "}
                            </span>
                            <span className="text-green-300">
                              {String(data.output).slice(0, 500)}
                            </span>
                          </div>
                        )}
                      </div>
                    )}
                  {isGuard && (
                    <div className="rounded-lg bg-yellow-500/10 border border-yellow-500/20 p-3 text-xs">
                      {data.tokens_used != null && (
                        <div>
                          <span className="font-medium text-yellow-400">
                            Budget:{" "}
                          </span>
                          {String(data.tokens_used)}/
                          {String(data.tokens_limit ?? "?")} tokens,{" "}
                          {String(data.calls_used ?? 0)}/
                          {String(data.calls_limit ?? "?")} calls
                        </div>
                      )}
                      {data.tool_name != null && (
                        <div>
                          <span className="font-medium text-yellow-400">
                            Loop:{" "}
                          </span>
                          Tool{" "}
                          <code className="rounded bg-muted px-1 py-0.5">
                            {String(data.tool_name)}
                          </code>{" "}
                          repeated {String(data.repeat_count ?? "?")} times
                        </div>
                      )}
                    </div>
                  )}
                  {Object.keys(data).length > 0 && (
                    <details>
                      <summary className="cursor-pointer text-xs text-muted-foreground transition-colors hover:text-foreground">
                        Raw data
                      </summary>
                      <pre className="mt-2 max-h-48 overflow-auto rounded-lg bg-muted p-3 text-xs">
                        {JSON.stringify(data, null, 2)}
                      </pre>
                    </details>
                  )}
                </>
              );
            })()}
          </div>
        </div>
      )}
    </div>
  );
}
