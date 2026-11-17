# NEPTUNE v2

Work directly; delegate only when substantial separable work justifies the overhead. Never require an Orchestrator role or delegation gate. Keep the user's main model/effort unchanged. Display the active CLI name (codex/claude) only at CLI startup. Do not prefix replies or sentences with a CLI label such as [codex].

In an active Neptune session, once the task is clear, name your own Herdr pane with a short role such as Research Assistant or Test Debugger. Use the existing naming command early in the turn and update the name only when the purpose changes. Choose a label without private details. Run this only when NEPTUNE_ACTIVE and HERDR_ENV are both 1 and HERDR_PANE_ID is set. On PowerShell use `python "$HOME/.local/share/neptune/herdr_agents.py" name "Research Assistant"`. On Bash use `python3 "$HOME/.local/share/neptune/herdr_agents.py" name "Research Assistant"`. If naming fails, continue the task.

Use K.I.S.S. and Ponytail for coding. Use Graphify for codebase mapping and graph queries. Consult an existing `graphify-out/` graph when it can answer an architecture or dependency question. Load skills/references on demand. Use local code for mechanical work, bounded tool output with retrievable full logs, and targeted file reads. Avoid unchanged polling, duplicate reviews, and redundant checks; retain meaningful verification and error handling.

FirstMate owns tracked tasks, compact briefs, and recovery/worktree references on supported hosts. Briefs: goal, decisions, files, verified check/revision, blocker, next action. Retrieve history on demand. No parallel NEPTUNE task ledger; preserve legacy data. If FirstMate is unavailable, report it and work directly.

Full local access is this user's NEPTUNE default, within native limits; respect explicit flags and NEPTUNE_FULL_ACCESS=0. No unrelated credentials, new spending, publishing, or deployment. Other destinations authorize their own permissions. Preserve sessions, partial work, and recovery records; isolate concurrent writers. Verify worker changes/checks before acceptance. Never equate token counts with subscription allowance or invent savings.
