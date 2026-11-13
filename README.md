# Neptune

Neptune is a terminal workspace for coding with Codex and Claude. It brings project shells and coding agents into one WezTerm window using Herdr.

[Watch the 20-second Neptune demo](docs/neptune-demo.mp4).

## What you can do

- Open a shell beside an agent using the **+** button in the pane tab strip.
- Drag a tab to a pane edge to split the view, or drop it on a pane to stack it.
- Switch terminals from the sidebar. Use **×** to close a terminal tab.
- See agent activity and supported shell commands in the tab labels.

## Get started

1. Set up WezTerm and Herdr using [START-HERE.md](START-HERE.md).
2. Open a terminal in your project directory and run `neptune`.
3. Run `codex` or `claude` in a Neptune shell. Use your CLI's resume command to return to an existing conversation.

The custom tab interface uses the Neptune Herdr build. On Ubuntu or WSL, use the [checkout launcher](docs/SETUP.md#keep-the-custom-terminal-ui-in-sync-on-ubuntu-or-wsl) to pick up the pinned build after a pull. For native Windows mouse input, see the [WezTerm ConPTY repair](docs/WINDOWS-MOUSE-FIX.md).

## Development

Run the offline checks from the repository root:

```sh
python -m unittest discover -s scripts/intelligence -p 'test_*.py'
node scripts/intelligence/test_hook_entry.cjs
```

See [Verification](docs/VERIFICATION.md) for details.
