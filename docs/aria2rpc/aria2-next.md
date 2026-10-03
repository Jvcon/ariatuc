# aria2-next integration

[`AnInsomniacy/aria2-next`](https://github.com/AnInsomniacy/aria2-next) is an
actively maintained fork of upstream `aria2c` (since 2026). Its JSON-RPC
surface is a **superset** of upstream aria2 — every method on vanilla
`aria2c` continues to work, plus a few additions for HLS / DASH media tasks
and ED2K / eMule. This document covers the additions and how `aria2rpc`
exposes them.

## What aria2-next adds

| Capability | Upstream `aria2c` | aria2-next |
|------------|--------------------|------------|
| HTTP / FTP / SFTP / BitTorrent / Metalink | yes | yes (modernized) |
| HLS / DASH media tasks | no | **yes** (native GPAC + libcurl + FFmpeg) |
| ED2K / eMule | no | **yes** |
| `getVersion.mediaFeatures` field | absent | present |
| `aria2.finishMedia` RPC | no | yes |
| `aria2.retryMedia` RPC | no | yes |
| `media` object on task status | no | yes |

Existing `aria2rpc` users do not need to switch clients to talk to aria2-next
— every standard RPC method already works against it. The R1 work
(`AGENTS.md`, this file, the new models) makes that compatibility **explicit**
and **typed**.

## Capability detection

Use `is_aria2_next` to gate calls to aria2-next-only methods:

```python
from aria2rpc import Aria2Client, is_aria2_next

async with Aria2Client("ws://localhost:6800/jsonrpc") as client:
    if await is_aria2_next(client):
        # aria2-next-specific flows
        ...
```

Internally `is_aria2_next` calls `aria2.getVersion` and looks for the
`mediaFeatures` field. There is no DNS handshake or version-string parsing —
the presence of `mediaFeatures` is the contract. It returns `False` against
any upstream aria2c, including very old or very new releases.

## Media task lifecycle

HLS / DASH downloads share the standard aria2 task lifecycle (`active`,
`waiting`, `paused`, `complete`, `error`, `removed`) but add an inner media
state machine exposed via `MediaDownloadStatus.state`:

```text
waiting → probing → awaiting-selection → downloading / recording
                                              ↓
                                         finalizing → complete
```

`MediaState` is an enum with every documented phase:

```python
from aria2rpc import MediaState

MediaState.WAITING              # "waiting"
MediaState.PROBING              # "probing"
MediaState.AWAITING_SELECTION   # "awaiting-selection"
MediaState.DOWNLOADING          # "downloading"
MediaState.RECORDING            # "recording"
MediaState.FINALIZING           # "finalizing"
MediaState.PAUSED               # "paused"
MediaState.COMPLETE             # "complete"
MediaState.ERROR                # "error"
MediaState.REMOVED              # "removed"
```

### Selecting tracks

To choose tracks before download:

1. Add the task with `media-pause-after-probe=true`.
2. Inspect `status.media.tracks`.
3. Call `change_option(gid, {"media-track-selection": "..."})` (consult
   upstream aria2-next docs for the exact selection syntax).
4. Clear the pause: `change_option(gid, {"media-pause-after-probe": "false"})`.
5. `unpause(gid)`.

Task options affecting selection or output **must** change while paused.

### Finishing a live recording

`finish_media(gid)` finalizes a paused or active live recording into the
output container. It is distinct from pause (which retains the task) and
remove (which cancels and discards recovery state).

```python
if status.media and status.media.live:
    await client.finish_media(gid)
```

### Retrying a failed media task

`retry_media(gid, options=None)` requeues a failed media task with the same
GID and retained native recovery data. Use it instead of
`remove_download_result` followed by `add_uri` — the latter path discards
media recovery data.

```python
# After a media task fails:
status = await client.tell_status(gid)
if status.status == "error" and status.media:
    # Optionally change options while paused first
    await client.retry_media(gid, {"media-format": "mkv"})
```

## Media fields

Every task status response from aria2-next carries a `media` object on media
tasks. `aria2rpc` exposes it via `DownloadStatus.media`, which is `None` for
ordinary downloads and a `MediaDownloadStatus` for media tasks:

```python
status = await client.tell_status(gid)

if status.media is None:
    # Ordinary HTTP / FTP / BitTorrent / Metalink download
    print(f"{status.completed_length}/{status.total_length} bytes")
else:
    # HLS / DASH task — media progress is based on completed_duration
    print(
        f"{status.media.protocol} "
        f"{status.media.state.value} "
        f"{status.media.completed_duration}/{status.media.duration} ms"
    )
```

`MediaDownloadStatus` distinguishes media progress (`completed_duration`) from
payload length (`downloaded_length`). For media tasks, `completedLength` on the
outer `DownloadStatus` is **not** the meaningful progress metric — use the
media fields.

## MediaFeatures

`getVersion().media_features` is a `MediaFeatures` object advertising the
capabilities of the running aria2-next:

```python
version = await client.get_version()
features = version.media_features

if features and features.structured_errors:
    # You can rely on status.media.error_code being a stable identifier
    ...
```

Known flags per upstream docs: `request_contexts`, `stable_track_ids`,
`structured_errors`. New flags can be inspected via `features.raw` without
needing a library upgrade.

## ED2K URLs

aria2-next accepts `ed2k://|file|...|/` links via the same `add_uri` flow as
any other URI. The `aria2rpc` library does not parse them specially — pass
the URL as-is:

```python
gid = await client.add_uri(["ed2k://|file|ubuntu-24.04.iso|abc...|/"])
```

Upstream `aria2c` will reject ED2K links with an `Aria2RPCError`; gate the
add with `is_aria2_next` if you want to fail early with a friendly message
instead of an RPC error.

## Recommended client code

A safe pattern when you want to support both engines:

```python
from aria2rpc import Aria2Client, is_aria2_next, Aria2RPCError

async with Aria2Client("ws://localhost:6800/jsonrpc") as client:
    next_features = await is_aria2_next(client)

    uri = "https://example.com/stream.m3u8"
    options: dict = {}

    if next_features:
        options["media-pause-after-probe"] = "true"

    try:
        gid = await client.add_uri([uri], options=options)
    except Aria2RPCError as exc:
        # aria2c does not understand HLS / DASH
        ...
```

## See also

- [`docs/aria2rpc/api.md`](api.md) — full API reference
- [aria2-next media docs](https://github.com/AnInsomniacy/aria2-next/blob/main/docs/media-downloads.md)
- [aria2-next releases](https://github.com/AnInsomniacy/aria2-next/releases)