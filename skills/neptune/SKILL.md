---
name: neptune
description: "Run an approved NEPTUNE software project through the existing FirstMate supervisor: professional specialists, local-first routing, sprint checkpoints and orchestrator handoffs. Use when asked to build or continue a project with NEPTUNE, or switch its orchestrator."
---

# NEPTUNE

Scope: All NEPTUNE workflow rules below apply only when the NEPTUNE hook explicitly identifies an active NEPTUNE session, launched with NEPTUNE_ACTIVE=1 inside a genuine Herdr pane. In ordinary Codex Desktop/CLI, Claude, and other Herdr sessions, these NEPTUNE rules do not apply: do not require delegation, mention missing Herdr context, or change their models or workflow. Explicit requests to maintain NEPTUNE may use its skill for setup and offline checks without activating its worker workflow.


Extend the installed workflow. Do not replace the terminal, start an independent supervisor loop, or invent project work. Use Ponytail/K.I.S.S. when coding. This skill adds governance metadata; FirstMate remains authoritative for live workers, inboxes, worktrees and delivery. Never treat the metadata ledger as proof of a live agent's status.

## Orchestrator-first agent workflow
An interactive AI session opened directly by the user is the Orchestrator by default. Use the strongest available model for this role, as selected by the user; never downgrade it automatically. Receive the user's goal, keep the plan and decisions, coordinate the work, and report results. Use the installed FirstMate/NEPTUNE workflow for delegation rather than building another orchestrator. Do not start project work merely because a session opens.

Delegate by default: use at least one visible Herdr specialist, named for its real work, for about 90% of substantive requests, including research, debugging, implementation and verification. The Orchestrator scopes and dispatches work, reviews evidence and reports results. The Orchestrator has direct tool access for planning, reading instructions, coordinating visible workers, reviewing files and diffs, running verification, and diagnosing or recovering failures. Delegate implementation and routine coding to visible specialists by default; the 90% preference does not block Orchestrator management or review. The Orchestrator may take over stalled work only as a rare exception after inspecting and quiescing the worker; preserve work, record the reason and finish only that scoped task. Reuse suitable specialists; do not spawn extra agents just to meet the percentage. If genuine Herdr context is unavailable, disclose that limitation and complete authorized direct work when useful.

Create only the specialists needed for the requested work, named by their professional role: UI/UX Designer, Frontend Engineer, Backend Engineer, QA Engineer, or another relevant role. Never use fictional character names. Preserve each worker's role, scope, task, session reference and progress. Use the professional role as the visible pane/tab label where supported, and a unique CLI-safe name such as ui-ux-designer or frontend-engineer-2. Preserve FirstMate's own task IDs; do not rename its bookkeeping to force a label.
A spawned agent with an explicit worker brief is a specialist, not another Orchestrator. Its brief must identify its role, assigned task, acceptance checks, project/worktree and supervising Orchestrator. Workers report back to that Orchestrator. Keep parallel writers isolated, reconcile direct-discussion decisions, and archive completed roles without destroying unreviewed work. Do not create an entire fixed team or recursively delegate without a concrete need.

## Runtime recovery

On Windows, use the absolute Python interpreter and helper command supplied by the current NEPTUNE prompt hook, including PowerShell's `&` call operator. Do not resolve `python3` through PATH for dispatch. Append `doctor --repair` to that helper command for diagnostics and bounded repairs. Spawn automatically checks its portable runtime before opening a worker. Missing Python aliases and Codex helpers can be restored locally; Codex helpers must come from a bundle whose Codex executable exactly matches the installed executable. No downloads, credential changes, permission changes, model changes or live session restarts are part of self-repair.

A failed launch records the actual worker identifier, pane and error. Inspect that preserved worker before another launch; do not blindly retry task submission, create a duplicate agent, or silently bypass delegation. An unknown failure is reported with the evidence needed for a repair decision. Runtime repairs do not prove that a live model worker ran successfully.

## Delegation tool gate

In active NEPTUNE panes, UserPromptSubmit supplies routing guidance. PreToolUse validates worker identity and rejects hidden-agent tools; it does not blanket-block Orchestrator tools. The Orchestrator can read its instructions, plan, coordinate workers, inspect/review results, run checks and diagnose recovery directly. Routine implementation remains delegated by workflow instructions. Native platform permissions still apply; this hook does not grant filesystem, IPC or administrator permissions.

On Windows, do not infer administrator elevation from PermissionDenied. Check actual process token evidence. Herdr IPC may be denied inside the Codex sandbox even when server and client run as the same non-administrator user. Use native permission requests when available. A destination may explicitly authorize full local access for NEPTUNE only; that local choice must not become a portable permission default.

Use single shell commands to the installed `herdr_agents.py` helper:

```bash
python3 "$HOME/.local/share/neptune/herdr_agents.py" spawn "File Systems Engineer" --complexity simple --cwd "/actual/task/directory" --task "Create hi .txt and verify the exact filename."
python3 "$HOME/.local/share/neptune/herdr_agents.py" inspect <actual-worker-name> --file "hi .txt"
python3 "$HOME/.local/share/neptune/herdr_agents.py" send <actual-worker-name> --task "Correct the specific defect and repeat the acceptance check."
```

`inspect` returns native activity/transcript evidence plus a Git diff summary or a bounded file read inside the assigned directory. `send` accepts only owned, idle/done workers; unknown or busy states refuse delivery. Reuse a suitable worker only when its observed model, effort and scope fit; otherwise spawn the necessary specialist. Worker reports do not require a new worker merely to acknowledge them. Native Codex code-mode wrappers may carry calls; every nested executable tool still passes through the gate.

Worker execution requires its actual pane and supervisor to match a registered launch record. Hidden native agents remain blocked. Outside Herdr the gate does not enforce delegation or control an existing session; disclose that limitation. Trusted, enabled, supported hooks are required. This is a workflow guard, not a tamper-proof sandbox; an unrestricted user can disable it and some hosted tools bypass local hooks. Do not fabricate hook-trust hashes.

### Rare stalled-worker takeover

The strongest Orchestrator reviews actual output, sends specific corrections to the same specialist and verifies its response before reporting to the user. Slow work alone is not failure. Inspect progress and preserve partial work; do not start competing writers.

If a worker has actually stalled, `interrupt NAME` sends Ctrl+C without claiming it stopped. Inspect again. Only after verifying the worker and any background writers are quiescent may the Orchestrator request:

```bash
python3 "$HOME/.local/share/neptune/herdr_agents.py" takeover <actual-worker-name> --reason "specific stall evidence and why direct recovery is needed" --quiescent
```

The helper requires a recent inspection, owned worker, idle/done native state, explicit quiescence attestation and a specific reason. It permits one exceptional takeover per worker, records the reason, scopes the lease to the assigned directory and expires it after ten minutes or a new user prompt. Finish the scoped recovery, verify it and run `finish-takeover`. Overlapping worker dispatch is refused while that lease is active. Background quiescence is a reviewed attestation, not something idle/done alone proves. Shell working-directory checks are not a filesystem sandbox; platform permissions remain authoritative. If state is unknown or safe takeover cannot be established, report the blocker instead of guessing.

## Start or resume

1. Read the target project's instructions and actual Git state. Locate the existing FirstMate operational home; require an explicit `FM_HOME`, never guess another home's ownership. Installed Ubuntu home on this PC: `<UBUNTU_HOME>/.local/share/firstmate`. Native Windows can use the portable ledger with an explicit local home, but FirstMate's live backend here is Ubuntu; do not pretend it is native Windows.
2. Use the bundled `scripts/neptune.py` with Python 3.11+:
   `python <skill-directory>/scripts/neptune.py --home <FM_HOME> --project <exact-git-root> <command>`.
   Run `--help` for commands. Keep SQLite on that host's local filesystem. Do not share a live SQLite file across Windows/WSL, a network drive or a synchronization tool.
3. Existing project: read `status`, then `handoff`. Resume the recorded FirstMate/native sessions only after reconciling current runtime and worktrees. New project: `init "vision"`; research reuse, draft architecture, sprint tasks, acceptance criteria and specialist suggestions in a plan file. See [plan example](references/plan.json).
4. `plan <file>` validates IDs, dependencies and limits and emits a changed digest in `status`. Show the human the plan, specialists, checks, permitted actions and limits. Only after their explicit approval, record `approve <digest> "<actual human approval reference>"`. Never invent that reference or approve your own proposal. A changed plan requires fresh approval. APIs are disabled; only zero API budget is accepted.

## Reuse before substantial code

Use the installed gh-axi integration/public official sources to find existing solutions. Before substantial imports record source URL, pinned release/commit, license, attribution, maintenance evidence, dependencies/security considerations, compatibility, and the reason to reuse or reject. Ask before copying substantial third-party code. Do not publish anything. Prefer a dependency or supported adapter over an upstream fork. [Implementation/reuse boundaries](references/integration.md).

## Specialists and sprints

### Visible Herdr role names
Use [visible agents](references/visible-agents.md) when a user requests visible specialists, task-related names or direct worker conversations. The bundled `scripts/herdr_agents.py` implements actual interactive Herdr tab creation and name reporting; do not substitute a background process for that request.
Inside a real Herdr-managed pane (`HERDR_ENV=1`), give the primary the display name `Orchestrator`. After discovering each worker's actual pane ID, set its human-readable professional role with `herdr pane report-metadata <actual-pane-id> --source neptune-role --display-agent "Frontend Engineer"` (replace that role as appropriate). This changes display only: preserve existing FirstMate task IDs, native session references, agent bindings and lifecycle state. Report a name when a new pane occupant starts; never label an unrelated or guessed pane. The sidebar's built-in `agent` row displays this name below the project title. Follow the installed Herdr skill's environment guard and current command help.



- Suggest only specialists needed by the approved tasks. Use professional role names and concrete responsibilities, not fictional characters. `specialist <id> "<role>" "<responsibility>"` stores the persistent role.
- FirstMate's installed `fm-tasks-axi.sh` owns backlog changes; `fm-brief.sh` owns brief scaffolding; `fm-spawn.sh` owns workers and Treehouse leases. Consult their installed help and FirstMate harness instructions before dispatch. Put the professional role, responsibilities, relevant context, acceptance checks and checkpoint instructions in the brief. Use `--mode local-only --yolo off`. No No Mistakes/GNHF run, push, PR, merge or teardown is authorized by this skill.
- Bind the observed native session ID, actual worktree and FirstMate task ID using `bind`. Never fabricate references. `assign` checks approved scope, dependencies, current sprint, parallel limit and separate worktrees for concurrent workers. It records assignment; it does not start a process or create a backlog item. Create/bind/assign before sending the approved task to a worker. Record the assignment failure if upstream launch fails; do not say it is running.
- Read `ready` after each verified task; continue later approved sprints without asking again. New scope/limits, merges into **any** branch, destructive operations, credentials, publishing, deployment and spending require human approval. A plan approval does not waive those gates.

## Routing

- Follow [worker model policy](references/worker-models.md) across all task categories. Worker model/effort selection is explicit and task-aware; the Orchestrator's settings are controlled only by the user. GPT-6.1 Sol and GPT-6 Astra require scoped human approval; other supported models/efforts may be chosen automatically with a task-based reason. No OpenCode or paid API fallback.
- Use `route <task> <provider-evidence.json>` for a small deterministic recommendation; inspect the explanation. Model/task judgment stays with the existing orchestrator, not a second model API router. Example evidence: [providers](references/providers.json).
- Provider availability must be observed, not assumed. For quota, use the already-approved local monitor/native status evidence. Do not invoke a credential-fetching quota collector without the user's approval. Evidence older than five minutes or missing values is unknown. Never combine context usage with subscription allowance.
- OpenCode is removed. Route only to available subscribed Codex/Claude agents; if unavailable, wait or discuss options. Ollama remains available directly, without an automatic coding-agent host. Never enable paid API fallback.
- On October 25 the user explicitly replaced the earlier manual-permission preference with always-allow local tool permissions. Check that home's explicit authorization before selecting its Codex/Claude worker mode. Claude still needs the human's subscription sign-in. Platform/managed policies remain authoritative; model escalation approval is a separate requirement.
- This module never calls a paid API, reads authentication files, changes CLI permissions or turns on an automatic approval reviewer. Unknown quota is disclosed uncertainty; observed zero blocks that provider. Sensitive work must not silently downgrade to a local model.

## Direct conversations without conflicting work

1. `discuss <specialist> "<message>"` durably queues the request, even when busy. It does not deliver or interrupt anything.
2. Wait until the current task is actually finished according to FirstMate's runtime and verification, then `conversation <specialist>` returns its original native session reference and queued messages. A ledger value alone is insufficient: check `fm-crew-state.sh <task-id>` with `FM_CREW_STATE_NO_FORGE=1` and the harness's current busy-state source. Unknown means wait/investigate, never assume idle.
3. Open/focus that existing conversation using Herdr inside `HERDR_ENV=1`; if stopped, use the CLI's native exact-session resume. Never launch two writers into the same native session or substitute a new chat and claim the entire transcript was retained.
4. Record significant decisions using `decision <specialist> "<summary>" --affected <task-ids>`. Read the decisions as orchestrator, update pending FirstMate briefs, then `reconcile <specialist> "<what changed>"`. Out-of-scope decisions require a revised approved plan. Affected tasks remain blocked until reconciled.
5. `archive` only archives idle, reconciled metadata. Preserve native transcripts and task history; do not delete or return dirty worktrees.

## Verification, recovery and switching orchestrator

- Run actual approved task checks in its worktree using `checkpoint <task> "<completed/incomplete/next actions>" --check <argv...>`. No shell interpolation is performed. The caller remains responsible for approving the command's effects. Review acceptance criteria and inspect actual diffs; a passing placeholder command is not a quality review.
- Before `complete`, the Orchestrator must critically inspect actual worker output, acceptance evidence and relevant edge cases. Send concrete defects to the same worker and verify corrections. Record `review-worker <task> accept|changes-requested "<actual review findings and evidence>"`. `complete <task>` requires a stable passing check, unchanged Git fingerprint and Orchestrator acceptance of that exact checkpoint. New checkpoints invalidate prior acceptance. Workers cannot approve themselves. Native transcripts and review history remain preserved.
- For interruption/context exhaustion, save a checkpoint before planned replacement. Reconcile real Git/worktree/runtime state after a crash; never destroy partial work. `handoff` includes actual current Git state and concise durable metadata, with full history retained in SQLite. Carry the handoff into the replacement subscribed orchestrator. Different provider conversations are never interchangeable.
- If an assignment failed or its worker died, first obtain concrete upstream runtime evidence that no old writer remains. Then `recover <task> "<observed runtime evidence>"` preserves the previous assignment/checkpoint in history, returns the task to pending, and makes the role unbound. Rebind the observed recovered/replacement session before assigning again. This command records the caller's evidence; it neither stops processes nor independently authenticates that evidence.
- `firstmate-command <specialist> state` or `... relaunch --harness codex|claude` emits the installed upstream command as an argv array, **does not execute it**. Relaunch pins worker model/effort and checks scoped model approval. Existing home permission checks remain. Read FirstMate's recovery instructions and establish the old worker's state before replacement; never duplicate a live worker or destroy partial work.
- Do not claim native transcript resume, automatic escalation, direct chat or cross-provider recovery is end-to-end verified unless tested against actual agents. The shipped tests use disposable Git repos and an interrupted fixture process, not a real model worker.

Outside a genuine Herdr pane, distinguish the desktop host from the NEPTUNE installation. Do not repeatedly announce "Herdr context is unavailable" or keep checking execution options. When visible workers are needed, explain once: open WezTerm, run `neptune` from the project directory, then run `codex` inside the resulting Herdr pane. Authorized setup edits and offline checks can proceed in the desktop chat. Never fabricate pane context, control Herdr from outside it, or substitute hidden workers.
