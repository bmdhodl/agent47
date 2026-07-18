# Benchmarks

Reproduce a local-LLM benchmark row on your own GPU. One script, stdlib only,
no API keys, no accounts.

## What it measures

`bench_ollama.py` runs one generation against a local
[Ollama](https://ollama.com) server and records:

- **Throughput**: output tokens per second over generation (eval) time.
- **Latency breakdown**: total, eval, prompt-eval, and model-load duration.
- **Power and VRAM**: watts and MiB used, sampled via `nvidia-smi` before and
  after the run.

Each run appends one CSV row in this schema:

```
date,model,quant,engine,workload,input_tokens,output_tokens,tokens_per_second,total_duration_s,eval_duration_s,prompt_eval_duration_s,load_duration_s,watts_before,watts_after,vram_before_mib,vram_after_mib,notes
```

Sample row (RTX-class GPU, 8B model, Q4_K_M):

```
2026-06-14,llama3.1:8b,Q4_K_M,Ollama,single-shot-generate,69,128,216.95,3.899,0.59,0.017,3.231,87.93,247.63,8539,9204,num_ctx=2048 num_predict=128 temp=0
```

## Hardware assumptions

- Any consumer NVIDIA GPU with enough VRAM for the model you pick. Model and
  context size are parameters, not hardcoded.
- `nvidia-smi` on PATH for the power/VRAM columns. Without it the script still
  runs and leaves those fields empty.
- Ollama installed with the model pulled (`ollama pull llama3.1:8b`).

## Run it

```bash
# sanity check, no GPU or network needed
python benchmarks/bench_ollama.py --selftest

# smallest real run
python benchmarks/bench_ollama.py --model llama3.1:8b

# full row appended to a CSV
python benchmarks/bench_ollama.py --model llama3.1:8b --quant Q4_K_M \
    --num-ctx 4096 --num-predict 256 \
    --notes "num_ctx=4096 num_predict=256 temp=0" --csv results.csv
```

The row prints to stdout either way. `--csv` appends to the file and writes
the header only when the file is new.

## Methodology notes

- `tokens_per_second` = `eval_count / eval_duration`. Generation time only.
  Prompt processing and model load are reported in their own columns, not
  mixed into throughput.
- Temperature defaults to 0 for repeatability. Same prompt + same model +
  same options should give stable timings within normal GPU variance.
- First run after `ollama pull` pays the model-load cost; `load_duration_s`
  makes that visible. Run twice and compare if you want warm numbers.
- Power sampling is two point-in-time reads, not an average over the run.
  Good enough to show idle-vs-load delta; not a power meter.

## llama.cpp

For raw llama.cpp numbers, use its built-in `llama-bench`:

```bash
llama-bench -m model.gguf -p 512 -n 128
```

Mapping to this schema: `pp512` throughput corresponds to prompt eval,
`tg128` to `tokens_per_second` (generation). Capture watts/VRAM with the same
`nvidia-smi --query-gpu=power.draw,memory.used --format=csv,noheader,nounits`
call before and after.

## Why this lives here

AgentGuard (`pip install agentguard47`) caps runtime cost for agents. Knowing
what your local hardware actually delivers is the other half of the cost
question: whether to route a workload to a local model or a paid API. These
scripts are the reproducible half of the local-inference reports we publish.
