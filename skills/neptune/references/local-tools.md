# Compact local tools

Use the installed Python interpreter and ~/.local/share/neptune/local_tools.py. These tools make no model calls.

- `check --cwd <directory> -- <executable> <arguments...>`: runs once without shell interpolation; returns exit code, timeout state, bounded stdout/stderr tails, and details_path. A failed check also exits nonzero. Full output stays in a local JSON file.
- `details <details_path> --field stdout --offset 0 --limit 2000`: retrieves a page. Omit field for a saved worker event. Follow next_offset; shortened explicitly indicates omissions. Limit is 1..12000 characters. To inspect stderr, use `--field stderr`.
- `usage <explicit-native-Codex-log.jsonl> ...`: returns the latest cumulative native token totals and reported rate-limit data. It does not return chat content, read credentials, estimate missing counts, or infer subscription savings. Treat absent evidence as unknown. Claude and other log formats remain unsupported.

Logs live under ~/.local/state/neptune/details, outside the project and Git. They can contain command output; preserve normal private host storage. Full native agent history remains in the native CLI session. Worker status does not fetch transcripts; `inspect NAME --transcript` explicitly requests the recent 120 lines, paginated. For complete older history use the native session, not this bounded recent view.

A short result is not a substitute for checking relevant code and failure evidence. FirstMate retains task history and compact briefs; these JSON files are diagnostic artifacts, not another task database.
