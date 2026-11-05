# Worker model policy

This policy applies to specialists only. The user chooses the main AI model and effort; never change its configuration or active selection.

## Selection

Judge the actual scope, risk, complexity and uncertainty across all work: coding, debugging, testing, review, research, planning, documents and file operations. Task titles alone do not determine capability requirements. Choose the least expensive adequate attempt, considering retries as well as initial token usage. Do not add an LLM routing call, daemon or provider.

| Characteristics | Initial Codex choice |
|---|---|
| Simple, mechanical, bounded output | GPT-6 Luna, low |
| Normal bounded coding/review/research | GPT-6 Luna, medium |
| Complex scope or uncertainty | GPT-6 Luna, high |
| Security, concurrency, migration/data-loss risk | GPT-6 Sol, high |

Only models listed by that host's Codex catalogue are selectable. Supported effort levels come from the selected model's metadata. This is cached capability evidence, not proof of current account access; actual UI/CLI verification is still required. If the catalogue is missing or unsupported, stop and refresh `/model`, rather than guessing.

Known economical fallback for missing GPT-6 Luna is GPT-5.6 Luna. Stronger non-restricted choices prefer GPT-6 Sol, then GPT-5.6 Terra, then GPT-5.6 Sol. Do not interpret version numbers as prices. These preference tiers are a documented policy snapshot, not guaranteed token savings or API price estimates.

The main AI may explicitly choose any other visible catalogue model and any supported effort when justified by task evidence. Supply `--reason`. Automatic defaults avoid max/ultra; explicit use needs a concrete reason. Later user requests for a specific worker model are honored within the approval rules.

**GPT-6.1 Sol and GPT-6 Astra always require task-specific human approval**, at every effort level, including versioned IDs in those model families. High effort on other models does not itself require approval: this is the user's revised rule, replacing the earlier low/medium-only proposal.

After one failed bounded attempt, a focused retry can use Luna high. Complex work that failed once can use GPT-6 Sol medium. After two failed attempts, stop automatic retries and request a scoped escalation decision. Do not silently create duplicate workers or switch settings in an existing busy conversation. Inspect existing progress before reusing or replacing a worker.

## Visible-worker interface

Inside a real Herdr pane:

```bash
python3 ~/.local/share/neptune/herdr_agents.py spawn "Frontend Engineer" \
  --harness codex --cwd "$PWD" \
  --complexity bounded \
  --task "Implement the agreed small UI change; run its focused acceptance checks."
```

The default complexity is `bounded`; choose `simple`, `complex`, or `sensitive` from actual task evidence. `--failed-attempts 0|1|2` carries observed failures, not speculative estimates. `--model`, `--effort`, and `--reason` allow a justified explicit choice. The helper validates before creating a tab, then launches Codex with explicit model, `model_reasoning_effort`, and Standard service tier. It never changes the parent's configuration.

Records live at `~/.local/state/neptune/workers/<actual-worker-name>.json`. Compact output includes model/effort, submitted state, worker/pane IDs, and a details path. Scope and launch diagnostics stay in local records. The record describes launch settings, not proof that the running model never changed. Completion reports identify the worker and link to full local output; verify actual changes and checks before acceptance.

Initial dispatch remains non-blocking. Say submitted until activity is observed, and verified complete only after checking results and acceptance criteria. Keep context narrow, tool outputs bounded and evidence targeted; do not shorten away necessary validation.

## Restricted-model approval

An attempted restricted launch stops before creating a pane and emits `approval_request` containing `scope_digest`, `model`, and `effort`. Show the task, reason and proposed settings to the human. Only after an explicit approval for that task, save those exact fields plus `user_reference` identifying the actual human approval, then retry with `--approval-file <record.json>`.

The scope digest includes role, full assigned task, directory, model and effort. A change invalidates the record. Do not create a blanket approval, invent a human reference or treat approval of the environment as approval for a restricted worker. These local records enforce workflow consistency; with unrestricted filesystem access they are not a tamper-proof security boundary. Global agent instructions remain necessary for manual CLI launches and in-chat model changes.

## Ledger and FirstMate

`neptune.py route` returns model, effort, reason and approval status instead of `native CLI default`. It remains a recommendation and does not launch anything. It respects observed Codex availability and quota; a stale/unknown allowance is disclosed, not fabricated. Current automatic model selection uses Codex subscription models only. Claude requires an explicitly selected and supported Claude model/effort and a reason; it is never a silent provider fallback. OpenCode remains removed.

`firstmate-command ... relaunch` pins model and effort through FirstMate's existing `--model`/`--effort` flags. It emits a command rather than executing it. Inspect actual old-worker state and preserve work before any replacement. Direct FirstMate commands must follow the same documented worker policy.

## main AI acceptance gate

Every finished worker turn needs a critical main AI review before presenting its output as verified. Check the actual diff or findings, acceptance criteria, correctness, relevant edge cases, security, tests and unsupported claims. For research, challenge source quality and conclusions; for file/count tasks, verify scope and counting rules. Review does not mean automatically launching another full duplicate review.

Return specific defects and acceptance checks to the same visible worker, then inspect the corrected result. Keep the user's conversation responsive; share progress or an honest blocker when needed. Do not hide failures until everything appears perfect. Use another specialist only when independent expertise or review scope justifies it, selected under the same worker model policy.

For ledger-owned work, after a stable passing checkpoint record:

```bash
python3 <skill-directory>/scripts/neptune.py --home <FM_HOME> --project <git-root> \
  review-worker <task-id> accept "Reviewed actual changes and evidence; findings resolved; acceptance criteria met."
```

Use `changes-requested` instead of `accept` when issues remain. The note must reflect the real review, not a copied ceremonial phrase. `complete` refuses absent/rejected reviews or a review for another checkpoint. Any new checkpoint invalidates the old acceptance, even when the Git fingerprint is unchanged. A supervised worker cannot accept its own task. These are local workflow guards, not proof that a model's critique was competent.

## Verification limits

Tests cover capability selection, all supported effort choices, restricted approvals, invalid/missing/hidden catalogue entries, retries, explicit launch arguments, records, and preservation of main AI config. Live launch/UI and completion delivery require a real Herdr session. The desktop setup chat must not fake Herdr environment variables to perform that check.
