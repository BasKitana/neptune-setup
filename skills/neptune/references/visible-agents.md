# Optional visible workers

Only run herdr_agents.py inside a genuine inherited Herdr pane. Never fabricate context from a desktop chat. Ordinary work can always proceed directly. Use FirstMate's installed instructions for FirstMate-owned tasks; retain its IDs, inboxes, and worktree ownership.

Commands: `spawn ROLE --task TASK --cwd EXISTING_WORKTREE --complexity simple|bounded|complex|sensitive`, `inspect NAME [--file RELATIVE_PATH] [--transcript] [--offset N] [--limit N]`, `send NAME --task TASK`, `interrupt NAME`, `doctor [--repair]`.

Choose workers only for separable work worth the overhead. Reuse suitable idle workers and keep concurrent writers in separate existing worktrees. Spawn returns identity, model/effort, submitted state, and a details path. It does not wait or fetch a transcript. Keep task role in the tab label; the AI display name is codex or claude. There is no mandatory supervisor role or takeover lease.

Inspect task-relevant changes/checks before acceptance. A stopped turn is not verified success. Send specific corrections to the same appropriate idle worker. Interrupt delivery alone does not prove background writers stopped; inspect and preserve partial work before direct recovery. Never blindly retry a failed launch: the helper preserves the worker/pane record.

Worker permission mode inherits NEPTUNE_FULL_ACCESS (1 = authorized full local access; 0 = native restricted/default mode). Native policies remain authoritative. The main AI model/effort is never changed. Read worker-models.md for model choices and scoped approvals.
