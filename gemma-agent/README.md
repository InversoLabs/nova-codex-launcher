# Gemma E2B Codex lab

Server workspace: `C:\Users\justi\Documents\Projects\gemma-codex-lab`.

This is an experimental server-first coding-agent pipeline. It keeps Conductor,
the production provider settings, model files, and user Codex configuration intact.
The intended student is **Gemma 4 E2B instruction-tuned QAT**, text only, thinking off.
An 8GB M2 is the later deployment target; no Mac performance is claimed here.

Latest verified results: the compact adapter passed three actual Codex read/edit/test
fixtures in 18.812, 16.610, and 16.938 seconds, with independent grades. These are
small tasks, not a repository-scale coding benchmark. The updated private training
backend passed synthetic LoRA gradients, NF4 computation, shared-KV cache/no-cache
parity, and backward propagation with CPU-resident PLE embeddings.

GPT-OSS passed the native Codex fixture through Conductor's existing proxy module.
The corrected teacher collector passed 8/8 tasks with zero action errors and yielded
16 training/8 validation actions, excluding held-out test families. All 24 examples
passed the real tokenizer/masking preflight and fit within 408 tokens.

Real-weight pilot `runs/real-pilot-v2` completed two QLoRA optimizer steps and saved
1,228,800 trainable adapter parameters. Steps took 5.922 and 4.672 seconds; peak
PyTorch GPU allocation was 2,089,436,672 bytes. One validation example's loss moved
from 1.83157 to 1.76280. This confirms pipeline/memory feasibility only, not an
improvement in coding ability; the 16-action training set is far too small for that.

## What runs

- `server_session.py` owns a separate loopback llama.cpp process and reads existing
  Ollama blobs without copying, modifying, or requantizing them. It cleans up its
  child on normal completion or failure. CPU, shared GPU, dual GPU and single GPU
  experiments have separate output directories.
- `python -m lab evaluate` exercises inspect/edit/test/finish on eight original
  pure-Python micro-tasks. The bounded AST interpreter never executes generated
  Python using `eval` or `exec`. This is a pipeline test, not a repository benchmark.
- `native_codex.py` launches the real private Conductor Codex executable with a
  private home/catalog. Native mode uses Conductor's existing compatibility module
  read-only. `--compact` instead uses the lab's compact JSON-to-Codex adapter.
- `compact_proxy.py` translates read, write, exec, test and finish actions. Writes
  become hash-guarded file updates executed through Codex's sandboxed shell.
  The proxy itself does not execute commands or write model edits. Whole-file
  editing is limited to 32KB and hidden/out-of-workspace paths are rejected.
- Every evaluation saves source, tool evidence, timings, and outcomes. A final
  model claim or a Codex exit code of zero does not establish task success.

## Run on the server

From the lab directory with Python 3.12:

```powershell
py -3.12 -m unittest discover -s tests -v
py -3.12 server_session.py --mode single-gpu --context 8192 --tag e2b-it-qat --out runs/new-server-session --threads 4 --hold 3600
```

The second command holds the model for one hour on loopback port 18190. Run tests
from another terminal while it is alive. Use a new output directory each time.
The `single-gpu` profile uses the second P1000 and keeps the large per-layer
embedding lookup table in RAM. It requires enough free VRAM: don't start it while
GPT-OSS occupies both GPUs. The user explicitly authorized temporarily unloading
GPT-OSS during these experiments; production configuration is unchanged.

```powershell
py -3.12 -m lab evaluate --model gemma-e2b-lab --out runs/new-baseline --steps 6
py -3.12 native_codex.py --compact --context 8192 --out runs/new-codex-smoke
```

**Windows session requirement:** Run native Codex from the signed-in desktop
session. On this Windows build, launching its shell sandbox directly under SSH can
fail with `0xC0000142`. The observed working route uses a limited-privilege,
interactive-token one-shot task, like Conductor. Do not disable the sandbox.

For an actual explicitly selected repository, create a UTF-8 prompt file and use:

```powershell
py -3.12 native_codex.py --compact --context 8192 --out runs/my-change --workspace C:\path\to\repo --prompt-file C:\path\to\request.txt --test-command 'npm test'
```

This can modify that repository inside Codex's workspace-write sandbox. Make a
normal Git checkpoint first. Read `events.jsonl`, inspect the diff and run the
project tests before accepting changes. The built-in independent clamp grader only
applies to the smoke fixture, not arbitrary repositories.

## Teacher trajectories and training

Run a teacher that serves Chat Completions on a loopback URL with:

```powershell
py -3.12 -m lab evaluate --model TEACHER --url http://127.0.0.1:PORT/v1 --kind teacher --split train --out runs/teacher-train
py -3.12 -m lab evaluate --model TEACHER --url http://127.0.0.1:PORT/v1 --kind teacher --split validation --out runs/teacher-validation
py -3.12 -m lab dataset --inputs runs --out datasets/accepted-v1
```

Admission replays actions against pristine fixtures, validates task/protocol
hashes, independently re-runs tests, checks final source, detects several common
credential patterns and deduplicates trajectories. This is a basic credential
filter, not a comprehensive privacy review. Test families and deterministic
reference fixtures are excluded by default. Protocol errors are rejected by default.
With `--allow-recovery`, replay-verified failed actions remain in input history but
are never supervised targets. Registered protocol versions preserve the original
prompt for archived trajectories; unknown protocol hashes are rejected.

The original eight tasks are **far too small for useful fine-tuning**. Expand to
independent repository/task families and pass a real held-out repository suite.
Never split individual turns from the same trajectory across train and validation.
The compact native trace is also saved for successful-run collection; it uses a
different tool protocol and must not be blindly mixed with the micro-task dataset.

`training/train.py` prepares LoRA or NF4 QLoRA with only the final assistant action
supervised. It rejects leaked splits, changed dataset hashes, oversized examples,
insufficient families, reference fixtures in production mode and unpinned model
revisions. It does not download weights or train without `--execute`.

`training/pilot.py` is a separate experimental 1-10 step memory-fit pilot. It keeps
the large frozen per-layer embeddings on CPU, transfers looked-up rows, and computes
logits only for supervised tokens. Full-model fit and numerical behavior must be
measured before treating it as a supported 4GB recipe. A saved pilot adapter alone
does not establish improved quality. `download_base.py` fetches pinned metadata and
weights; `download_weights.py` is a resumable alternative for weights with a final
SHA-256 check. Both write only under the ignored `models/` directory.

For a fresh copy, first run `download_base.py --metadata-only`, then
`download_weights.py`. After verification and teacher-data preparation,
`run_pilot_job.py --out runs/unique-pilot-name` checks Conductor is idle, temporarily
unloads the originally resident GPT-OSS, runs a bounded backend check and a two-step
real-weight pilot, then restores GPT-OSS. Inspect `job.json` and `training/pilot-report.json`;
an adapter file by itself is not evidence of a successful or useful training run.

The first real pilot exposed an Accelerate placement hazard: a catch-all root GPU
entry moved the 4.38GiB PLE table before applying its CPU override. `placement.py`
now maps the text model's immediate child modules explicitly, with no root entry.
The synthetic loading/backward probe exercises this same mapping. Pascal cards use
FP32 NF4 compute with FP16 storage; their native FP16 arithmetic is unusually slow.

```powershell
py -3.12 training/train.py --data datasets/accepted-v1 --out runs/train-preflight
# Explicit, tiny backend compatibility test; does not train pretrained weights:
# .venv-training\Scripts\python.exe training/backend_probe.py --allow-backend-probe
```

`training/bootstrap_existing.ps1` borrows the existing ComfyUI Python 3.12 ML
libraries read-only and installs PEFT, Accelerate and bitsandbytes only into this
lab's private environment. `training/setup.ps1` is the larger standalone alternative.
`training/resolved-requirements.txt` records the installed environment. Never run
pip against the production ComfyUI environment for this lab.

The conservative full-model recipe requires 6GiB free on one CUDA device. Neither
4GB P1000 satisfies that, even though inference fits. The tiny synthetic backend
probe is intended to check architecture/gradient/NF4 compatibility, not full-model memory fit.
A measured CPU-embedding/two-GPU training recipe or a larger training GPU is still
needed before executing the full Gemma fine-tune. Do not equate two 4GB devices
with one 8GB device.

## Export and M2 stage

`training/merge_export.py` prepares a separate merged model and optional GGUF Q4_0
conversion, leaving the base and adapter intact. The llama.cpp source checkout and
matching converter are needed for conversion. Pin the model revision and converter
commit. Fine-tuning can change QAT behavior: re-benchmark the merged and quantized
models, rather than assuming the original QAT quality survives.

Start M2 verification with the text-only Q4_0 language model, no projector, one
request at a time, thinking disabled and 4096 context. Record total application
memory and macOS memory pressure/swap along with prompt throughput, generation
throughput, first-tool latency, task time and pass rate. Expand to 8192 context only
if the 8GB machine remains comfortable. Prefer the same llama.cpp protocol initially;
MLX is an optional later comparison, not a validated deployment in this repository.

## Rollback

All new code and logs live in this lab directory. Git commits are rollback points.
Stop only a PID owned by a lab run (verify its executable and port against its
`session.json`); do not kill all llama, Ollama, Python or Codex processes. Remove
only the temporary lab scheduled task after it completes. `Restore-GptOss.ps1`
reloads the original model with the recorded 8192 context and resident keep-alive.
No Conductor service or schedule needs changing.

## Sources used

- https://ai.google.dev/gemma/docs/core/model_card_4
- https://huggingface.co/google/gemma-4-E2B-it-qat-q4_0-unquantized
- https://huggingface.co/docs/peft/developer_guides/quantization
- https://huggingface.co/docs/bitsandbytes/installation
- https://github.com/ggml-org/llama.cpp
- https://learn.chatgpt.com/docs/developer-commands?surface=cli
