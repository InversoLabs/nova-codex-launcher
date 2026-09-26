# Browser-project training corpus

24 original, runnable browser tools; 48 tasks (implement missing logic or repair a deliberate defect). This is a larger **curriculum seed**, not evidence that Gemma has learned useful website development.

The set includes a catalog search, priority board, contrast checker, quiz scorer, reading planner, inventory alerts, event capacity planner, and other small interactive tools. Each has an HTML interface, CSS, application state handling, calculation logic, and a README. Open any reference `index.html` directly. There are no third-party assets, build steps, accounts, or remote requests.

## Provenance and splits

- Reference implementations, specifications, and expected cases were authored by the assistant in this chat. They are **not** represented as teacher trajectories.
- 16 project families train, 4 validation, 4 test. Both variants of a project remain in the same split. The collector excludes every test-family task.
- Most apps share an interface scaffold; the split is by domain, not by independent UI architecture. Scores will therefore overestimate generalization to completely different repositories.
- Each task exposes one example plus a written behavioral contract. The grader keeps additional cases outside the student's workspace. This is a practical evaluation boundary, not a guarantee against deliberate test inspection.
- The current production training thresholds require 20 train and 5 validation families. This first set does **not** meet those thresholds. Do not lower them or start meaningful training just to make this set qualify. Add diverse project families and more independent tasks first.

## Build and verify

Use Python 3 and Node with Playwright available on `NODE_PATH`. The grader defaults to installed Microsoft Edge in a fresh headless context; set `CORPUS_BROWSER_CHANNEL` for another installed Playwright channel.

```powershell
python build.py --out my-suite
python verify_suite.py --suite my-suite --out verification --starters
```

Verification requires every reference to pass and every starter to fail a behavior case. Checks cover actual form interaction and rendered outputs, numeric validation, reset, local state persistence/clear (password tool excludes persistence), associated labels, keyboard focus, and mobile horizontal overflow. This is not an accessibility audit or a visual design grade.

Candidate JavaScript executes in an isolated browser context, not in the Node host. Routing permits only the four local application files; network requests are blocked, service workers disabled, and no user profile or credentials are loaded into the browser.

## Real teacher collection

GPT-OSS should use `native_collect.py`, which calls native Codex through the existing proxy without the Gemma compact adapter. The compact collector below is retained for models that reliably speak that protocol. Its GPT-OSS smoke attempts were rejected because of action-shape mismatches; they are not training examples. Native event histories need a separately verified conversion before compact-protocol training.

```powershell
python native_collect.py --suite my-suite --out native-run --task reading-planner--repair --model gpt-oss:20b
```

```powershell
python collect.py --suite my-suite --out teacher-run --model gpt-oss:20b --limit 1
python export.py --suite my-suite --runs teacher-run --out admitted-data
```

Use the existing `NOVA_DESKTOP_API_KEY` environment established by the launcher and the existing proxy. The collector calls the real Codex CLI with the compact adapter and a fresh copy of each starter. Model edits run under Codex's workspace sandbox. Trusted browser tests are outside the candidate workspace. The collector stops on the first failed run, independently regrades the final files, records evidence hashes, and retains rejected runs locally for diagnosis. Raw traces are ignored by Git.

The exporter accepts only successful teacher runs, rechecks final files in a fresh browser, verifies hashes and family splits, excludes retries and adapter-substituted actions, and filters common credential patterns. It uses observed tool histories; it does **not** invent command output or replay arbitrary shell commands. The evidence boundary is weaker than a full deterministic action replay and the credential filter is not a comprehensive privacy review.

Do not publish raw collected traces without review. Tokenize and inspect sequence lengths before fine-tuning; full project histories will exceed the old 1,024-token pilot limit. Preserve the compact-native protocol identifier rather than silently mixing these histories with the old one-file micro-task protocol.

## Authored demonstrations

`demonstrate.py` executes assistant-authored action plans against fresh starters and records actual file reads, edits, and browser test output. It excludes test families. These are **reference-aware deterministic expert demonstrations**, not autonomous teacher runs. Their manifest has `reference_allowed: true`, so the production training gate rejects them until explicitly reviewed. The application code is original; tool outcomes are measured, never fabricated. Keep this provenance when using the examples in a future supervised curriculum.

```powershell
python demonstrate.py --suite my-suite --out authored-demonstrations
```

## Next quality milestones

1. Get the teacher transport to complete one admitted end-to-end run.
2. Collect a small batch and manually inspect every accepted trajectory.
3. Add independent UI architectures, navigation, asynchronous requests against fixtures, storage migrations, and multi-file feature tasks.
4. Expand to at least 20 train / 5 validation families, with untouched test families.
5. Compare base Gemma and the current pilot on identical held-out tasks before training a candidate.
6. Resolve adapter reload, context fit, and memory limits before training. Promote a model only after held-out improvement, keeping the current model as rollback.
