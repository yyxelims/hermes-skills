# Debugging Hermes TUI Slash Commands

Hermes slash commands span three layers — Python command registry, tui_gateway JSON-RPC bridge, and the Ink/TypeScript frontend. When a command misbehaves, the bug is almost always one layer being out of sync with another.

## Architecture Overview

```
Python backend (hermes_cli/commands.py)     ← canonical COMMAND_REGISTRY
       │
       ▼
TUI gateway (tui_gateway/server.py)         ← slash.exec / command.dispatch
       │
       ▼
TUI frontend (ui-tui/src/app/slash/)        ← local handlers + fallthrough
```

## Investigation Steps

1. Check if command exists in TUI frontend: `search_files --pattern "/commandname" --file_glob "*.ts" --path ui-tui/`
2. Examine TUI command definition: `read_file ui-tui/src/app/slash/commands/core.ts`
3. Check if command exists in Python backend: `search_files --pattern "CommandDef" --file_glob "*.py" --path hermes_cli/`
4. Examine gateway: `search_files --pattern "slash.exec" --path tui_gateway/`

## Fix: Missing Command Autocomplete

1. Add `CommandDef` entry to `COMMAND_REGISTRY` in `hermes_cli/commands.py`:
   ```python
   CommandDef("commandname", "Description", "Category",
              cli_only=True, aliases=("alias",),
              args_hint="[arg1|arg2]",
              subcommands=("arg1", "arg2")),
   ```
2. Pick `cli_only` vs gateway carefully
3. Ensure `subcommands` matches tab-completion options
4. Add handler in `cli.py::process_command()` (server-side)
5. For gateway-available commands, add handler in `gateway/run.py`

## Common Issues

1. **Command shows in TUI but not in autocomplete.** Missing from `COMMAND_REGISTRY`.
2. **Command shows in autocomplete but doesn't work.** Check handler in `tui_gateway/server.py` and frontend handler.
3. **Command behavior differs between CLI and TUI.** Different implementations in `cli.py` and TUI local handler.
4. **Command persists config but doesn't apply live.** Update nanostore state immediately with `patchUiState(...)`.
5. **Gateway dispatch silently ignores.** Check `GATEWAY_KNOWN_COMMANDS` includes the canonical name.

## Pitfalls

- Don't forget the category in `CommandDef` (Session, Configuration, Tools & Skills, Info, Exit)
- Aliases in the `aliases` tuple — all downstream consumers derive from it
- `cli_only=True` commands won't work in gateway unless you add `gateway_config_gate`
- After adding live UI state, check all render paths (StreamingAssistant + MessageLine)
- Rebuild TUI (`npm --prefix ui-tui run build`) before testing

## Verification

1. Rebuild TUI: `npm --prefix ui-tui run build`
2. Run TUI: `hermes --tui`
3. Verify command appears in `/` autocomplete
4. Execute and confirm behavior + config + live UI state
5. Test gateway-available commands from messaging platforms
