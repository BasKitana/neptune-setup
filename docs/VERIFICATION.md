# Verification status

Portable export checks performed before initial publication: 48 Python tests passed, Node hook regressions passed, both WezTerm templates loaded through the installed CLI, PowerShell template parsed without execution, and JSON/TOML/Python structural checks passed. An allowlist and credential-pattern/machine-path scan passed. These checks do not replace live laptop setup tests.

This repository is a portable export of the source configuration, not a claim that the laptop is installed. It contains no automatic package installer: the destination AI follows START-HERE.md and merges templates after inspection.

The source helper suite passed 48 Python tests and cross-platform Node hook checks. It covers task/model selection, approval scoping, unavailable models, explicit effort arguments, mocked visible-agent registration, completion reporting, review rejection/acceptance, checkpoint invalidation, and preservation of the Orchestrator config. Actual catalogue checks were performed on both source hosts without model calls. The export also runs these tests independently; check its Git history for the packaged verification result.

Live model launch, clipboard operation, sidebar rendering, completion delivery and review handoff were not verified end-to-end by the desktop setup chat. Some source screenshots/user transcripts showed named visible agents; that does not verify every feature or this export's templates. Tests with mocks do not prove a real model followed its brief.

Laptop acceptance checks:

1. Open WezTerm: actual Projects directory and NEPTUNE/Herdr appear without starting coding work.
2. Verify clipboard and listed keyboard navigation.
3. Start primary Codex: sidebar shows Orchestrator once. Quota row shows only real supported data.
4. Submit one authorized bounded visible worker: it appears with task role, real pane and interactive chat. Verify actual model/effort.
5. Verify dispatch returns, worker reports a finished turn, and Orchestrator checks actual evidence rather than trusting the report.
6. Demonstrate a rejected review, correction and acceptance of the exact new checkpoint using a disposable fixture; preserve real projects.
7. Verify restricted model requests stop before creating a pane without scoped human approval. No protected model needs to be run merely for setup.
8. Detach/reattach without killing existing processes. Explain server/OS shutdown and disabled automatic agent restoration.
9. Report each component as Installed, Verified, Unsupported, Requires approval or Not tested.

## Directory resume and executable resolution

- In two distinct test directories, create different short manual chats, exit, and confirm bare `codex` resumes each directory's own chat. Check a directory with no prior conversation separately.
- Confirm `codex --help` and `codex resume --all` pass through, and supervised worker launches remain fresh with their assigned model/effort.
- After an update, confirm the PATH-selected Codex version matches the package-manager installation. Check for stale links or competing Windows/Ubuntu executables before retrying updates.

## Delegation gate regressions

The gate suite checks the reported `touch 'hi .txt'` regression, patches/MCP calls, validated visible dispatch with explicit task-based selection, inspection and corrections, shell-injection attempts, worker record/ownership checks, hidden-agent denial, outside-Herdr behavior and code-mode nested calls. Node tests confirm gate errors, timeouts and malformed output return explicit denial while optional display hooks remain nonblocking. Fixtures do not prove native tool interception or actual live workers.

Live acceptance inside a genuine managed pane: trust the installed hooks through the native CLI; request creation of `hi .txt` in a disposable directory; verify direct Orchestrator execution is denied, a visible File Systems Engineer starts with an advertised economical model/effort, the worker creates the exact file, and the Orchestrator inspects that worker/file before reporting success. Also check a busy worker refuses correction delivery, another supervising pane cannot inspect its private record through the helper, and naming/completion hooks still work. Do not manufacture environment IDs for this test.

Takeover fixtures also check refusal without inspection/quiescence, refusal while busy, one-time use, directory bounds, expiry, new-prompt revocation, overlapping worker dispatch refusal and interruption ownership. Native interruption/quiescence and end-to-end recovery still require an actual managed Herdr session; fixture states are not live evidence.

## Runtime recovery regression checks

The suite now covers absolute-interpreter dispatch with PowerShell’s call operator, denial of alternate interpreters and chained commands, Python alias repair, exact-bundle Codex helper repair, rejection of mismatching helpers, idempotent repair, and preservation of failed launch records. The real Node-to-Python denial fixture runs on Windows as well as Linux using synthetic IDs and never controls Herdr. Actual worker creation, model access and completion delivery still require a real NEPTUNE pane.
