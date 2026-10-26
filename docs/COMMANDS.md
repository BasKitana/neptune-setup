# Daily commands

| Command | Action |
|---|---|
| neptune | Open/attach NEPTUNE in configured Projects |
| proj | Go to Projects |
| pwd / ls / cd folder / cd .. | Navigate |
| codex / claude | Start that agent in current pane; not a new specialist |

Herdr prefix: Ctrl+B, release, then key. Verify destination bindings in prefix+?.

| Key after prefix | Action |
|---|---|
| v / - | Split side-by-side / top-bottom |
| h j k l | Focus left/down/up/right |
| Tab / z | Next pane / zoom toggle |
| c / n / p | New / next / previous tab |
| 1..9 | Select tab |
| Shift+T / Shift+W | Rename tab / Space |
| w | Space picker |
| [ | Keyboard copy mode: Space selects, movement extends, y copies, Esc exits |
| Shift+R | Reload config |
| q | Detach, keeping session running |
| x / Shift+X | Close pane / tab; may terminate its processes |

Clipboard: Shift-drag selects/copies in WezTerm; Ctrl+Shift+C copies a host selection; Ctrl+V or Ctrl+Shift+V pastes. Herdr mouse selection can copy independently. Test both paths on the laptop.

For visible workers, use the NEPTUNE skill and ~/.local/share/neptune/herdr_agents.py, inside genuine Herdr context. Keep real pane/tab references and inspect actual chat output.
