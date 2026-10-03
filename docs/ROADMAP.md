# Roadmap

The single source of truth for what `ariatuc` is building next. Backlog lives in the GitHub
issue tracker; this file is the orientation layer.

## Why a roadmap now (2026-10)

`AnInsomniacy/aria2-next` shipped in 2026 as an actively maintained aria2 fork with:

- **Native HLS / DASH media tasks** — `addUri` extension surfaces a `media` object on task
  status responses; new RPC methods `finishMedia` and `retryMedia`; `getVersion` now exposes a
  `mediaFeatures` map.
- **Native ED2K / eMule** support.
- **Same JSON-RPC surface as upstream aria2**, plus extensions. Existing aria2 clients already
  work.

Our `aria2rpc` library already speaks the upstream aria2 RPC, which means it **already works**
with aria2-next without code changes. The work is to:

1. Make that compatibility **explicit** — capability detection, typed models for the new
   fields, two new RPC methods exposed as additions.
2. Make the TUI **take advantage** of the new fields — media-aware progress, track selection,
   ED2K URLs.
3. Refocus the project around `aria2rpc` as the product and `ariatuc` as the reference
   application.

## Phase R1 — Split + recalibrate (in progress)

**Goal**: structurally separate the library from the TUI; expose aria2-next extensions in the
library; replace the 1061-line `CLAUDE.md` with a focused, cross-tool `AGENTS.md`.

### Acceptance criteria

- [x] `AGENTS.md` exists and replaces `CLAUDE.md`.
- [x] `CLAUDE.md` deleted.
- [x] `pyproject.toml` declares both `aria2rpc` and `ariatuc` as packages.
- [x] `src/aria2rpc/_version.py` carries an independent library version.
- [x] `src/aria2rpc/__init__.py` exposes `is_aria2_next`, `finish_media`, `retry_media`,
      `MediaDownloadStatus`, `MediaTrack`, `MediaState`, `MediaFeatures`.
- [x] `tests/aria2rpc/unit/test_aria2_next.py` covers the new methods and capability detection
      with mocked JSON-RPC envelopes.
- [x] `docs/ROADMAP.md` (this file) exists.
- [x] `docs/aria2rpc/api.md` documents the public surface of `aria2rpc`.
- [x] `docs/aria2rpc/aria2-next.md` documents the aria2-next integration (capability detection
      + media flow).
- [x] `README.md` rewritten around the new positioning (aria2 + aria2-next, dual package).
- [x] `mise run lint && mise run format:check && mise run mypy && mise run test:unit` green.

## Phase R2 — TUI meets aria2-next (next)

**Goal**: the TUI discovers aria2-next capabilities at connection time and surfaces the new
flows.

### Acceptance criteria

- [ ] On connect, the TUI calls `is_aria2_next()` and shows a "Media" tab only when the
      server is aria2-next.
- [ ] "Add Download" dialog detects `.m3u8` / `.mpd` URLs and exposes `media-*` options
      (`media`, `media-format`, `media-video`, `media-audio`, `media-record-time`).
- [ ] Download list row shows `media.state` and progress based on `completedDuration` for
      media tasks.
- [ ] Detail panel shows media `tracks` for paused-selection media tasks.
- [ ] `f` key (`finishMedia`) and `R` key (`retryMedia`) on selected media tasks.
- [ ] ED2K URLs (`ed2k://|file|...|/`) parse and are accepted in "Add Download".

## Phase R3 — Brand and release (later)

**Goal**: cut a real 1.0 release; ship the library to PyPI as a follow-up if demand exists.

### Acceptance criteria

- [ ] `ariatuc` 1.0 released (TUI).
- [ ] Migration guide for users coming from vanilla `aria2c` only.
- [ ] Migration guide for users coming from AriaNg / webui-aria2.
- [ ] (Optional) `aria2rpc` 1.0 to PyPI based on measured demand.

## Non-goals

- **Forking aria2 RPC protocol.** We are downstream of `aria2/aria2` and
  `AnInsomniacy/aria2-next`. New methods are added when upstream ships them.
- **A web frontend.** AriaNg already exists and is excellent. `ariatuc` is the terminal
  counterpart.
- **A browser extension or GUI.** Out of scope.
- **Re-implementing BitTorrent / Metalink / DASH protocols.** aria2 and aria2-next already do
  this; we expose their state.

## Status snapshot (2026-10)

| Component | State | Notes |
|-----------|-------|-------|
| `aria2rpc` HTTP transport | Mature | All 18 standard RPC methods, retries, timeouts |
| `aria2rpc` WebSocket transport | Mature | Same methods + 6 event types |
| `aria2rpc` models | Mature | Dict-wrapper style, type-safe accessors |
| `aria2rpc` aria2-next extensions | **New in R1** | `is_aria2_next`, media models, `finishMedia`, `retryMedia` |
| `ariatuc` core (service + state) | Mature | Service layer 1390 lines, RPC + event managers |
| `ariatuc` UI (screens, widgets, themes) | Usable | 5 screens, 11 widgets, dracula theme |
| `ariatuc` media awareness | **Not started** | Phase R2 |