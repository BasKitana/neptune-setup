---
name: neptune
description: "Run an approved NEPTUNE software project through the existing FirstMate supervisor: professional specialists, local-first routing, sprint checkpoints and orchestrator handoffs. Use when asked to build or continue a project with NEPTUNE, or switch its orchestrator."
---

# NEPTUNE

Extend the installed workflow. Do not replace the terminal, start an independent supervisor loop, or invent project work. Use Ponytail/K.I.S.S. when coding. This skill adds governance metadata; FirstMate remains authoritative for live workers, inboxes, worktrees and delivery. Never treat the metadata ledger as proof of a live agent's status.

## Orchestrator-first agent workflow
An interactive AI session opened directly by the user is the Orchestrator by default. Receive the user's goal, keep the plan and decisions, coordinate the work, and report results. Use the installed FirstMate/NEPTUNE workflow for delegation rather than building another orchestrator. Do not start project work merely because a session opens.

Delegate by default: use at least one visible Herdr specialist, named for its real work, for about 90% of substantive requests, including research, debugging, implementation and verification. The Orchestrator scopes and dispatches work, reviews evidence and reports results. Handle trivial answers, clarifications and tiny edits directly when delegation would add more overhead than value. Reuse suitable specialists; do not spawn extra agents just to meet the percentage. If genuine Herdr context is unavailable, disclose that limitation and complete authorized direct work when useful.

Create only the specialists needed for the requested work, named by their professional role: UI/UX Designer, Frontend Engineer, Backend Engineer, QA Engineer, or another relevant role. Never use fictional character names. Preserve each worker's role, scope, task, session reference and progress. Use the professional role as the visible pane/tab label where supported, and a unique CLI-safe name such as ui-ux-designer or frontend-engineer-2. Preserve FirstMate's own task IDs; do not rename its bookkeeping to force a label.
A spawned agent with an explicit worker brief is a specialist, not another Orchestrator. Its brief must identify its role, assigned task, acceptance checks, project/worktree and supervising Orchestrator. Workers report back to that Orchestrator. Keep parallel writers isolated, reconcile direct-discussion decisions, and archive completed roles without destroying unreviewed work. Do not create an entire fixed team or recursively delegate without a concrete need.

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
