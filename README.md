# NEPTUNE v2

An update to the existing `neptune` launcher, not another agent framework. Open WezTerm -> NEPTUNE/Herdr -> use Codex or Claude directly. Delegate to visible workers only when useful.

- Compact worker/check output; full local diagnostic logs available on demand.
- FirstMate is the task authority on supported hosts. No duplicate active NEPTUNE ledger.
- Keep native session resume, isolated worktrees, meaningful verification, and recovery history.
- Economical task-fit workers; the user's main AI model and effort stay unchanged.
- Full local tool permissions are the requested default inside NEPTUNE, with native limits and explicit overrides preserved. This is not permission for spending or publishing.
- CLI labels appear at startup. No mandatory Orchestrator role or delegation gate.

Read START-HERE.md for installation/update. This repository contains source/config templates, not credentials, chats, binaries, or an automatic installer. Existing Windows runtime fixes must be preserved. FirstMate is not established as supported on this Windows host; do not install another OS to force it.

Offline verification:

```text
python -m unittest discover -s scripts/intelligence -p 'test_*.py'
node scripts/intelligence/test_hook_entry.cjs
python scripts/intelligence/benchmark_output.py
```

Tests use disposable files and mocked workers. Output reduction is measurable; subscription savings and live worker behavior require separate native evidence. See docs/VERIFICATION.md.
