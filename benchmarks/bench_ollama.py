#!/usr/bin/env python3
# MIT License (see repo LICENSE).
"""Reproducible local-LLM benchmark: one CSV row per run.

Measures single-shot generation throughput on a local Ollama server and
captures GPU power/VRAM via nvidia-smi before and after the run. Appends
one row to a CSV in the published report schema:

date,model,quant,engine,workload,input_tokens,output_tokens,
tokens_per_second,total_duration_s,eval_duration_s,prompt_eval_duration_s,
load_duration_s,watts_before,watts_after,vram_before_mib,vram_after_mib,notes

Works on any consumer NVIDIA GPU (model and context are parameters).
Zero dependencies: stdlib only. GPU capture degrades gracefully if
nvidia-smi is not on PATH (fields are left empty and a warning is printed).

Usage:
    python benchmarks/bench_ollama.py --model llama3.1:8b
    python benchmarks/bench_ollama.py --model llama3.1:8b --quant Q4_K_M \
        --num-ctx 4096 --num-predict 256 --csv results.csv
    python benchmarks/bench_ollama.py --selftest   # offline sanity check
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import io
import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

CSV_FIELDS = [
    "date",
    "model",
    "quant",
    "engine",
    "workload",
    "input_tokens",
    "output_tokens",
    "tokens_per_second",
    "total_duration_s",
    "eval_duration_s",
    "prompt_eval_duration_s",
    "load_duration_s",
    "watts_before",
    "watts_after",
    "vram_before_mib",
    "vram_after_mib",
    "notes",
]

DEFAULT_PROMPT = (
    "Summarize in one paragraph why runtime budget enforcement matters "
    "for autonomous AI agents."
)

NS_PER_S = 1_000_000_000


def sample_gpu() -> tuple[str, str]:
    """Return (watts, vram_mib) from nvidia-smi, or ("", "") if unavailable."""
    if shutil.which("nvidia-smi") is None:
        print("warning: nvidia-smi not found; GPU fields left empty", file=sys.stderr)
        return "", ""
    try:
        out = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=power.draw,memory.used",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        ).stdout
    except (subprocess.SubprocessError, OSError) as exc:
        print(f"warning: nvidia-smi failed ({exc}); GPU fields left empty", file=sys.stderr)
        return "", ""
    # First GPU only; format: "123.45, 8192"
    first = out.strip().splitlines()[0] if out.strip() else ""
    parts = [p.strip() for p in first.split(",")]
    if len(parts) != 2:
        print(f"warning: unexpected nvidia-smi output: {first!r}", file=sys.stderr)
        return "", ""
    return parts[0], parts[1]


def call_ollama(
    host: str,
    model: str,
    prompt: str,
    num_ctx: int,
    num_predict: int,
    temperature: float,
    timeout_s: float,
) -> dict:
    """POST /api/generate (stream=false) and return the parsed JSON response."""
    payload = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_ctx": num_ctx,
                "num_predict": num_predict,
                "temperature": temperature,
            },
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{host.rstrip('/')}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise SystemExit(
            f"error: cannot reach Ollama at {host} ({exc}). "
            "Is `ollama serve` running and the model pulled?"
        )


def build_row(
    response: dict,
    *,
    model: str,
    quant: str,
    engine: str,
    workload: str,
    gpu_before: tuple[str, str],
    gpu_after: tuple[str, str],
    notes: str,
    date: str,
) -> dict:
    """Turn an Ollama /api/generate response into one report-schema CSV row.

    Ollama durations are nanoseconds; token counts are prompt_eval_count
    (input) and eval_count (output). tokens_per_second = output tokens over
    generation (eval) time only, matching the published reports.
    """
    input_tokens = int(response.get("prompt_eval_count", 0))
    output_tokens = int(response.get("eval_count", 0))
    eval_ns = int(response.get("eval_duration", 0))
    tok_per_sec = round(output_tokens / (eval_ns / NS_PER_S), 2) if eval_ns else 0.0

    def _secs(key: str) -> float:
        return round(int(response.get(key, 0)) / NS_PER_S, 3)

    return {
        "date": date,
        "model": model,
        "quant": quant,
        "engine": engine,
        "workload": workload,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "tokens_per_second": tok_per_sec,
        "total_duration_s": _secs("total_duration"),
        "eval_duration_s": _secs("eval_duration"),
        "prompt_eval_duration_s": _secs("prompt_eval_duration"),
        "load_duration_s": _secs("load_duration"),
        "watts_before": gpu_before[0],
        "watts_after": gpu_after[0],
        "vram_before_mib": gpu_before[1],
        "vram_after_mib": gpu_after[1],
        "notes": notes,
    }


def format_csv_line(values: list) -> str:
    """Render one properly quoted CSV line (no trailing newline)."""
    buf = io.StringIO()
    csv.writer(buf).writerow(values)
    return buf.getvalue().rstrip("\r\n")


def append_row(csv_path: str, row: dict) -> None:
    """Append one row, writing the header only when the file is new/empty."""
    try:
        with open(csv_path, "r", encoding="utf-8") as fh:
            needs_header = fh.read(1) == ""
    except FileNotFoundError:
        needs_header = True
    with open(csv_path, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        if needs_header:
            writer.writeheader()
        writer.writerow(row)


def selftest() -> int:
    """Offline check: build a row from a canned response and validate it."""
    canned = {
        "prompt_eval_count": 69,
        "eval_count": 128,
        "eval_duration": 590_000_000,
        "prompt_eval_duration": 17_000_000,
        "load_duration": 3_231_000_000,
        "total_duration": 3_899_000_000,
    }
    row = build_row(
        canned,
        model="llama3.1:8b",
        quant="Q4_K_M",
        engine="Ollama",
        workload="selftest",
        gpu_before=("87.93", "8539"),
        gpu_after=("247.63", "9204"),
        notes="selftest canned response",
        date="2026-01-01",
    )
    assert list(row) == CSV_FIELDS, "row keys must match CSV_FIELDS order"
    assert row["input_tokens"] == 69
    assert row["output_tokens"] == 128
    assert row["tokens_per_second"] == 216.95, row["tokens_per_second"]  # 128 / 0.59 s
    assert row["total_duration_s"] == 3.899
    assert row["eval_duration_s"] == 0.59
    assert format_csv_line(["a", "b,c"]) == 'a,"b,c"', "CSV quoting must survive commas"
    print("selftest OK")
    print(format_csv_line(CSV_FIELDS))
    print(format_csv_line([row[f] for f in CSV_FIELDS]))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark a local Ollama model and append a report-schema CSV row."
    )
    parser.add_argument("--model", help="Ollama model tag, e.g. llama3.1:8b")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help="prompt to generate from")
    parser.add_argument("--host", default="http://localhost:11434", help="Ollama base URL")
    parser.add_argument("--num-ctx", type=int, default=2048, help="context window")
    parser.add_argument("--num-predict", type=int, default=128, help="max tokens to generate")
    parser.add_argument("--temperature", type=float, default=0.0, help="sampling temperature")
    parser.add_argument("--quant", default="", help="quantization label for the CSV row")
    parser.add_argument("--workload", default="single-shot-generate", help="workload label")
    parser.add_argument("--notes", default="", help="free-text notes column")
    parser.add_argument("--csv", default="", help="CSV file to append to (default: stdout only)")
    parser.add_argument("--timeout", type=float, default=600.0, help="request timeout seconds")
    parser.add_argument("--selftest", action="store_true", help="run offline sanity check")
    args = parser.parse_args(argv)

    if args.selftest:
        return selftest()
    if not args.model:
        parser.error("--model is required (or use --selftest)")

    gpu_before = sample_gpu()
    response = call_ollama(
        args.host, args.model, args.prompt, args.num_ctx, args.num_predict,
        args.temperature, args.timeout,
    )
    gpu_after = sample_gpu()

    if not response.get("done", False):
        print("warning: response reports done=false; timings may be partial", file=sys.stderr)
    if not response.get("eval_count"):
        print("warning: eval_count missing from response; throughput will read 0", file=sys.stderr)

    row = build_row(
        response,
        model=args.model,
        quant=args.quant,
        engine="Ollama",
        workload=args.workload,
        gpu_before=gpu_before,
        gpu_after=gpu_after,
        notes=args.notes,
        date=_dt.date.today().isoformat(),
    )
    print(format_csv_line(CSV_FIELDS))
    print(format_csv_line([row[f] for f in CSV_FIELDS]))
    if args.csv:
        append_row(args.csv, row)
        print(f"appended to {args.csv}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
