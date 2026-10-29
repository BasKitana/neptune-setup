# Visible workers

Use the existing Herdr skill and environment guard. Install this skill's five scripts together under ~/.local/share/neptune/ on the destination.

```bash
python3 ~/.local/share/neptune/herdr_agents.py name "Orchestrator"
python3 ~/.local/share/neptune/herdr_agents.py spawn "Frontend Engineer" --harness codex --cwd "$PWD" --complexity bounded --task "Perform only the agreed change and its focused checks."
```

On Windows use Python and a resolved Windows path. The adapter creates a visible tab, publishes role metadata, starts an interactive CLI, verifies registration, submits the task once without a long wait, reads initial output and records the selection. Delivery is not task execution. Stop hooks notify the actual supervising pane; they do not prove completion. See worker-models.md for selection, approvals and critical acceptance.

Keep native worker chats open for user discussion. Do not promise a combined transcript interface. Use FirstMate's existing inbox for tasks it owns, preserve IDs and worktrees, and reconcile direct-discussion decisions. Never substitute hidden subagents or headless runs. OpenCode is not supported in this setup.
