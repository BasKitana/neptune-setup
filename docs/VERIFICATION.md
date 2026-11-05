# NEPTUNE v2 verification

Verified on this Windows host:

- 59 Python tests passed: existing legacy history/checkpoint/model-policy coverage plus compact output, lossless retrieval, failure exit codes, timeout partial logs, missing executables, native usage parsing, explicit transcript retrieval, path bounds, and inherited worker permissions.
- Node regression checks passed for both CLI labels/platform paths, native session registration, optional worker reports, retired delegation handlers, inactive/foreign-host skips, and nonblocking hook failures.
- PowerShell and Git Bash launcher tests passed with intercepted/stub CLIs: NEPTUNE-only full-access defaults, native resume argument preservation, explicit permission overrides, and restricted opt-out. PowerShell environment restoration is also checked. No fixture pane IDs reach real Herdr.
- Before/after offline benchmark uses the same bounded mocked task and fixed 60-line transcript. Worker-launch response: 4,735 -> 312 bytes (93.4% smaller in this fixture); brief: 1,008 -> 381 bytes; Herdr calls: 9 -> 6; transcript reads at launch: 1 -> 0. No model calls. This is not a token/quota/billing measurement.
- Usage parser read the current chat's native Codex token totals and rate-limit snapshot without returning chat text. This is observational telemetry, not a controlled savings comparison.

Reproduce:

```text
python -m unittest discover -s scripts/intelligence -p 'test_*.py'
node scripts/intelligence/test_hook_entry.cjs
pwsh -NoProfile -File scripts/intelligence/test_profile.ps1
bash scripts/intelligence/test_profile.sh
python scripts/intelligence/benchmark_output.py
```

Preserved: legacy neptune.py/SQLite history, native sessions, existing runtimes and repairs, Herdr/clipboard/navigation configuration, optional task-fit workers, worktree isolation and recovery evidence. No new agent framework, API service, daemon, credentials, or billing was introduced.

Not established: live sidebar naming, native permission behavior and actual worker completion delivery in a genuine Herdr session; actual model adherence to a brief; subscription allowance savings. Existing running CLIs retain their launch settings; open a new CLI to load updated defaults. Hook changes may need legitimate native trust review; stored trust hashes were not changed.

FirstMate live integration is unavailable on this host: no configured FM_HOME or supported Ubuntu backend was found. No replacement ledger or OS workaround was introduced. Its task ownership is documented for supported installations.

For a controlled live comparison, use disposable equivalent task copies, the same main model/effort and acceptance checks, and the same worker policy. Record all worker/main usage and retries, success/quality, elapsed time, and native rate-limit snapshots. Exclude unrelated activity where possible; report incomplete or aggregate quota evidence as inconclusive. Do not infer subscription savings from output bytes or summed token counts alone. Live tests must run inside genuine Herdr; never synthesize pane context.
