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
numbered read ranges, whole-file write (32K character limit), exact-text edit,
exec, check, test, and finish. Edits replace one unique match and preserve the
rest of the file; both writes and edits reject concurrent file changes. New
parent folders are created inside the workspace by Codex's sandboxed command.

The GUI retains the existing model options and bridge. API credentials are reused
from the current user's Conductor credential store when available, passed through
process environments, and never included in source, model artifacts, or logs.
Session logs are private local files under `%LOCALAPPDATA%/NOVA-Gemma/sessions`.

The adapter streams the model's separate reasoning field into Codex's reasoning
display, without changing the server's thinking setting. It never executes partial
JSON. Responses have a 2048-token allowance (the existing bridge maximum); an
invalid action receives corrective feedback, with at most two retries. Repeated
invalid actions end with an explicit incomplete result instead of a success claim.
Keep source files small: thinking and the action share that response allowance.
Bundled skills are disabled only in this profile's isolated Codex home. Auxiliary
tool-free chat-title requests are answered locally rather than queued on NOVA.
Restart the Gemma Codex session after an adapter update to load the new code.

Before finishing after file changes, the adapter requests real checks through
Codex: JavaScript/Python syntax, JSON parsing, local HTML asset existence, and
file existence for other types. A configured test command must also succeed.
Failed or still-running checks do not authorize completion. Changes after a pass
invalidate that pass. Arbitrary shell output saying "passed" does not satisfy
this gate. Without a configured functional test, the final response explicitly
states that application behavior and visuals are not independently verified.
These checks cannot prove that all user requirements were met, and do not yet
validate CSS semantics, browser behavior, HTTP routes, or project-folder intent.
The bounded source scan skips hidden/dependency/build directories; use a focused
workspace (up to 1000 supported source files / 32MB) for this experimental profile.
Unchanged writes are rejected; repeated near-identical edits require a successful
check before continuing. This is a loop guard, not a guarantee of convergence.

Context options are 4K, 8K (default), 16K and 32K. The larger options are for
server testing, not yet validated for long-context coding quality or the 8GB Mac.
The bridge's chat API does not accept `num_ctx`, so the launcher chooses matching
Ollama tags `gemma4-codex:pilot-v1-4k`, `-16k`, or `-32k`; 8K retains the original
tag. These profiles share the same weight blobs and preserve the existing model.
Create them on NOVA with `training/register_context_profiles.ps1` before use.
Selecting 8K returns to the original profile. Larger contexts do not increase the
bridge's per-response 2048-token limit.

The `gemma-agent` source includes the evaluator, teacher dataset collector,
training recipes, and export code. `evidence` contains generated test fixtures,
verified seed data and pilot measurements, not private repository transcripts.
The pilot adapter/tokenizer is backed up as a separate GitHub release asset.
Large pretrained base weights are reproducible from the pinned Hugging Face
revision and are not duplicated in Git.
