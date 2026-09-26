# Trained Gemma pilot in the NOVA launcher

Choose **Gemma E2B - trained pilot + compact adapter**, select a workspace, and
click Launch Codex. Keep your existing NOVA URL and API key. The launcher starts
a local compact-action adapter; it forwards authenticated chat requests through
the existing NOVA bridge. Codex executes tools on this PC in its selected sandbox.
No new SSH tunnel or remote inference service is used by this profile.

The model name is `gemma4-codex:pilot-v1`. It contains the actual two-step LoRA
checkpoint merged into the pinned Gemma E2B IT QAT base and quantized for Ollama.
This is an experimental training checkpoint, not a claim of improved coding
quality. Start with small tasks in a test workspace. The compact adapter supports
read, whole-file write (32KB limit), exec, test, and finish. Without a configured
test command it asks the model to discover and execute the project's checks.

The GUI retains the existing model options and bridge. API credentials are reused
from the current user's Conductor credential store when available, passed through
process environments, and never included in source, model artifacts, or logs.
Session logs are private local files under `%LOCALAPPDATA%/NOVA-Gemma/sessions`.

The `gemma-agent` source includes the evaluator, teacher dataset collector,
training recipes, and export code. `evidence` contains generated test fixtures,
verified seed data and pilot measurements, not private repository transcripts.
The pilot adapter/tokenizer is backed up as a separate GitHub release asset.
Large pretrained base weights are reproducible from the pinned Hugging Face
revision and are not duplicated in Git.
