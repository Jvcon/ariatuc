# AGENTS.md — Guide for AI coding agents working on ariatuc

> **Cross-tool**: This file follows the [AGENTS.md convention](https://agents.md) and is read by
> OpenCode, Claude Code, Cursor, Aider, Continue, and any other agent that respects it. Do not
> assume agent-specific tools — no `mcp__ide__getDiagnostics`, no `.claude/`-only paths, no IDE
> lock-in. Use `mise run` / `poetry run` commands that any agent can drive.
>
> **Scope**: the entire repository. If a subdirectory needs different rules, it can ship its own
> `AGENTS.md`; lower in the tree wins.

## What this project is

`ariatuc` is a **terminal control surface for aria2 and aria2-next**. It is **two packages in one
repo**, and the library is the product, not the TUI:

| Package | Purpose | Publish? |
|---------|---------|----------|
| `src/aria2rpc/` | Python client library: 28+ aria2 JSON-RPC methods over HTTP and WebSocket, with first-class `aria2-next` extensions (HLS / DASH media tasks, capability detection, `finishMedia`, `retryMedia`). Designed for any async Python program that talks to aria2. | **No** — internal dependency for `ariatuc`. Not on PyPI yet. |
| `src/ariatuc/` | A Textual TUI that uses `aria2rpc`. Reference application and primary UX test bed. The TUI is the showpiece; the library is the product. | Yes — to PyPI as `ariatuc`. |

aria2-next is `AnInsomniacy/aria2-next` (2026). It is a maintained fork of upstream aria2 with
native HLS / DASH media downloads and native ED2K / eMule, and its JSON-RPC surface is a
superset of upstream aria2. Existing aria2 clients (including `aria2rpc`) already work against
it; Phase R1 of the roadmap adds explicit capability detection and typed access to the new
fields.

## Architecture invariants

These are load-bearing — do not change without an ADR in `docs/aria2rpc/` or `docs/ariatuc/`.

1. **`aria2rpc` knows nothing about `ariatuc`.** Its imports are stdlib + `httpx` + `websockets`
   + `pydantic`. The TUI must never be imported from the library.
2. **`ariatuc` depends on `aria2rpc` via project layout** (`pythonpath = ["src"]` in pytest
   config). It does not vendor the library source.
3. **No fork of aria2 RPC protocol.** All method names are upstream-compatible. aria2-next
   extensions are exposed as *additions*, never renames.
4. **Single Python target: 3.11+** (see `pyproject.toml` + `.mise.toml`). No type-backports.
5. **Async-first.** All `aria2rpc` entry points are `async def`. No blocking wrappers.
6. **One config, one CLI per concern.** UI lives in `src/ariatuc/ui/`, business logic in
   `src/ariatuc/core/`. Don't put logic in widgets.

## Standard workflow for any change

```text
1. Edit code
2. mise run lint            # ruff check --fix
3. mise run format          # ruff format
4. mise run mypy            # static types
5. mise run test:unit       # fast tests, no aria2c daemon
6. (only if RPC changed)    mise run test
```

**Do not run tests until lint + mypy are clean.** A task is not complete until all six steps
above are green for the changed files. This applies to every agent, including follow-up agents.

## Routing work to specialist agents

Route by **what kind of work** it is, not by file path:

| Lane | Use for |
|------|---------|
| `@explorer` | Reconnaissance: find files, search patterns, summarize code. Read-only. |
| `@librarian` | External docs: aria2 RPC spec, aria2-next extensions, Textual, pydantic. Use when the answer depends on a library's current behavior. |
| `@oracle` | Architecture review, risky refactors, debugging after 2+ failed attempts. Use when the cost of being wrong is high. |
| `@designer` | UI/UX: layout, motion, themes, screens, widgets, interaction feel. **Never** touch backend logic in the same change. |
| `@fixer` | Mechanical execution: given a precise spec, write or edit bounded code. No research, no architecture choices.**

**Default to doing it yourself** when the change is one isolated, obvious edit. Delegate when
the work has separable lanes or exceeds ~50 lines across files.

## Adding a new RPC method

When upstream aria2 or aria2-next gains a method:

1. Add the method to `src/aria2rpc/base.py` as `async def` with full type hints.
2. Add a typed response model in `src/aria2rpc/models.py` if the response is non-trivial.
3. Export it from `src/aria2rpc/__init__.py`.
4. Add a unit test in `tests/aria2rpc/unit/` mocking the JSON-RPC envelope.
5. Document the method in `docs/aria2rpc/api.md`.
6. Bump `aria2rpc` version in `src/aria2rpc/_version.py`.

**Do not** add RPC wrappers speculatively. Methods are added only when upstream ships them or
when the TUI has a concrete design need.

## Adding UI features

When the change is user-visible (new screen, widget, keybinding, theme):

1. Hand it to `@designer` with the user goal, not the implementation sketch.
2. After `@designer` ships, review for **copy** (its known weakness) and tighten wording. Do not
   change layout or interaction intent.
3. Add UI tests in `tests/ariatuc/ui/` using Textual's pilot harness.
4. Update `docs/ariatuc/user-guide.md` keybinding table.

## Forbidden patterns

- **`# noqa`, `# type: ignore`, `cast(...)`** in committed code without a comment explaining
  why. Fix the type instead.
- **`Any`** in new public function signatures. Use `Unknown`, a precise union, or a typed model.
- **Synchronous wrappers around `aria2rpc` async calls** in the TUI. Push async up; never block.
- **Hardcoded RPC endpoints, secrets, or paths** in source. Use `core/config_manager`.
- **Creating `notes/`, `backlog/`, `.claude/agents/`, `.opencode/agents/`** directories. This
  project uses **`docs/`** and the GitHub issue tracker. There is no local markdown-only backlog.
- **Touching `pyproject.toml` `[tool.poetry] packages`** without keeping both `aria2rpc` and
  `ariatuc` listed.

## Project layout

```text
src/aria2rpc/                  # standalone-feeling library
  base.py                       # all 28+ RPC method implementations
  http.py                       # HTTP JSON-RPC transport
  websocket.py                  # WebSocket JSON-RPC transport + events
  client.py                     # Aria2Client(url) factory
  models.py                     # response models (incl. aria2-next)
  option_types.py               # aria2 option enums
  exceptions.py                 # error hierarchy
  _version.py                   # library version (independent of ariatuc)

src/ariatuc/                    # Textual TUI
  main.py                       # CLI entry
  core/                         # service, download/rpc/event managers
  ui/                           # screens, widgets, themes
  utils/                        # logger, helpers

tests/aria2rpc/{unit,integration}/
tests/ariatuc/{unit,ui,integration}/
docs/
  aria2rpc/                     # library docs (api.md, aria2-next.md, ...)
  ariatuc/                      # TUI docs (user-guide.md, architecture/, ...)
  ROADMAP.md                    # project roadmap
scripts/                        # test orchestration, aria2c lifecycle
examples/                       # usage samples (kept thin)
```

## Useful commands

```bash
mise run lint              # ruff check
mise run format            # ruff format
mise run format:check      # ruff format --check
mise run test:unit         # unit tests, no daemon
mise run test              # all tests, auto-manages aria2c daemon
mise run aria2:start       # start aria2c for manual tinkering
mise run aria2:status      # check aria2c daemon
mise run dev               # run the TUI with logs to file
```

## When you are unsure

- **Ask the user** — do not guess on: package structure changes, new RPC methods, new
  keybindings, brand or positioning language, deleting files.
- **Use `@oracle`** for: refactors that span multiple files, debugging that has failed twice,
  decisions about backward compatibility.
- **Use `@librarian`** for: aria2-next's current RPC extensions, Textual API behavior, new
  aria2 option semantics.

## External resources

- aria2 RPC spec: <https://aria2.github.io/manual/en/html/aria2c.html#rpc-interface>
- aria2-next docs: <https://github.com/AnInsomniacy/aria2-next/tree/main/docs>
- Textual: <https://textual.textualize.io/>