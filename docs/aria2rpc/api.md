# aria2rpc — API reference

`aria2rpc` is the Python client library in this repository. It is the product;
the TUI is one of its consumers. This document is the canonical reference for
its public surface. Anything not listed under **Public API** is internal and
may change without notice.

> **Engine compatibility**: every method below works against upstream
> `aria2c`. Methods marked **aria2-next** require the
> [`AnInsomniacy/aria2-next`](https://github.com/AnInsomniacy/aria2-next)
> fork; gate them with [`is_aria2_next`](#capability-detection).

## Public API

| Symbol | Kind | Engine |
|------|------|--------|
| `Aria2Client(url, **kwargs)` | function (factory) | both |
| `is_aria2_next(client)` | async function | both (capability check) |
| `BaseRPCClient` | abstract class | both |
| `HTTPRPCClient` | class | both |
| `WebSocketRPCClient` | class | both |
| `Aria2Event` | enum | both |
| `Aria2Error`, `Aria2ConnectionError`, `Aria2TimeoutError`, `Aria2AuthenticationError`, `Aria2RPCError` | exception classes | both |
| `DownloadStatus`, `GlobalStat`, `Version`, `Peer`, `Server`, `FileServer` | response models | both |
| `MediaState`, `MediaTrack`, `MediaDownloadStatus`, `MediaFeatures` | response models | **aria2-next** |
| `__version__` | string | both |

## Connection

### `Aria2Client(url, **kwargs)`

Factory that returns the right client based on the URL scheme.

```python
from aria2rpc import Aria2Client

# WebSocket (events + RPC)
async with Aria2Client("ws://localhost:6800/jsonrpc", secret="token") as client:
    ...

# HTTP (RPC only, no events)
async with Aria2Client("http://localhost:6800/jsonrpc", secret="token") as client:
    ...
```

`Aria2Client` does not open a connection until the first call. Always use it
as an async context manager to ensure the underlying transport is closed.

| URL scheme | Returns |
|------------|---------|
| `ws://`, `wss://` | `WebSocketRPCClient` |
| `http://`, `https://`, other | `HTTPRPCClient` |

### Capability detection

```python
from aria2rpc import Aria2Client, is_aria2_next

async with Aria2Client("ws://localhost:6800/jsonrpc") as client:
    if await is_aria2_next(client):
        # aria2-next: HLS / DASH + finishMedia / retryMedia available
        ...
```

`is_aria2_next` calls `getVersion` and looks for the `mediaFeatures` field,
which is unique to aria2-next. It returns `False` against upstream `aria2c`.
It raises connection / authentication errors on transport failure; the bool is
returned only when the RPC succeeds.

## Standard RPC methods (both engines)

All standard methods are `async def` on the client. They delegate to the
abstract `BaseRPCClient._call(method, params)`, implemented by HTTP and
WebSocket transports.

### Download control

| Method | RPC name | Returns |
|--------|----------|---------|
| `add_uri(uris, options=None, position=None)` | `aria2.addUri` | `str` (gid) |
| `add_torrent(torrent, uris=None, options=None, position=None)` | `aria2.addTorrent` | `str` (gid) |
| `add_metalink(metalink, options=None, position=None)` | `aria2.addMetalink` | `str` (gid) |
| `remove(gid)` | `aria2.remove` | `str` (gid) |
| `force_remove(gid)` | `aria2.forceRemove` | `str` (gid) |
| `pause(gid)` | `aria2.pause` | `str` (gid) |
| `pause_all()` | `aria2.pauseAll` | `"OK"` |
| `force_pause(gid)` | `aria2.forcePause` | `str` (gid) |
| `force_pause_all()` | `aria2.forcePauseAll` | `"OK"` |
| `unpause(gid)` | `aria2.unpause` | `str` (gid) |
| `unpause_all()` | `aria2.unpauseAll` | `"OK"` |

### Status & information

| Method | RPC name | Returns |
|--------|----------|---------|
| `tell_status(gid, keys=None)` | `aria2.tellStatus` | `DownloadStatus` |
| `tell_active(keys=None)` | `aria2.tellActive` | `list[DownloadStatus]` |
| `tell_waiting(offset, num, keys=None)` | `aria2.tellWaiting` | `list[DownloadStatus]` |
| `tell_stopped(offset, num, keys=None)` | `aria2.tellStopped` | `list[DownloadStatus]` |
| `get_uris(gid)` | `aria2.getUris` | `list[dict]` |
| `get_files(gid)` | `aria2.getFiles` | `list[dict]` |
| `get_peers(gid)` | `aria2.getPeers` | `list[Peer]` |
| `get_servers(gid)` | `aria2.getServers` | `list[FileServer]` |
| `get_global_stat()` | `aria2.getGlobalStat` | `GlobalStat` |
| `get_version()` | `aria2.getVersion` | `Version` |
| `get_session_info()` | `aria2.getSessionInfo` | `dict` |

### Configuration

| Method | RPC name | Returns |
|--------|----------|---------|
| `get_option(gid)` | `aria2.getOption` | `dict[str, str]` |
| `change_option(gid, options)` | `aria2.changeOption` | `"OK"` |
| `get_global_option()` | `aria2.getGlobalOption` | `dict[str, str]` |
| `change_global_option(options)` | `aria2.changeGlobalOption` | `"OK"` |

### Utility

| Method | RPC name | Returns |
|--------|----------|---------|
| `change_position(gid, pos, how)` | `aria2.changePosition` | `int` |
| `change_uri(gid, file_index, del_uris, add_uris, position=None)` | `aria2.changeUri` | `list[int]` |
| `purge_download_result()` | `aria2.purgeDownloadResult` | `"OK"` |
| `remove_download_result(gid)` | `aria2.removeDownloadResult` | `"OK"` |
| `save_session()` | `aria2.saveSession` | `"OK"` |
| `shutdown()` | `aria2.shutdown` | `"OK"` |
| `force_shutdown()` | `aria2.forceShutdown` | `"OK"` |
| `multicall(calls)` | `system.multicall` | `list[Any]` |
| `list_methods()` | `system.listMethods` | `list[str]` |

## aria2-next extensions

These methods only exist on aria2-next. Calling them against upstream `aria2c`
raises `Aria2RPCError`. Always gate with `is_aria2_next`.

### `finish_media(gid)`

Ends an active or paused live recording and finalizes its completed media.

```python
if await is_aria2_next(client):
    await client.finish_media(gid)
```

- Pause retains the task; remove cancels it and discards recovery state.
- Finishing and deleting are separate operations.

### `retry_media(gid, options=None)`

Requeues a failed media task with the same GID and retained native recovery
data. Does not delete the stopped result until queue insertion succeeds.
Invalid or non-media results are rejected without mutation.

```python
await client.retry_media(gid)
# Or, change options while paused:
await client.retry_media(gid, {"media-format": "mkv"})
```

Use this instead of `remove_download_result` followed by `add_uri` — that path
intentionally discards media recovery data.

## Response models

All response models inherit from `RPCResponse`. They wrap the raw dict and
expose typed accessors. Access the raw payload with `model.raw` or
`model["key"]`.

### `DownloadStatus`

Fields from `aria2.tellStatus` etc. Includes a `.media` property that returns
a `MediaDownloadStatus` for media jobs and `None` otherwise.

```python
status = await client.tell_status(gid)
if status.media:
    print(f"{status.media.protocol}: {status.media.state}")
```

### `Version`

Adds `media_features: MediaFeatures | None` and `is_aria2_next: bool`
properties on top of the standard `version` and `enabledFeatures`.

### `MediaDownloadStatus` (aria2-next)

The `media` object on task status responses. Fields per
[aria2-next docs](https://github.com/AnInsomniacy/aria2-next/blob/main/docs/media-downloads.md):

| Property | Type | Meaning |
|----------|------|---------|
| `state` | `MediaState` | `waiting`, `probing`, `awaiting-selection`, `downloading`, `recording`, `finalizing`, `paused`, `complete`, `error`, `removed` |
| `protocol` | `str` | `hls`, `dash`, `file` |
| `live` | `bool` | live stream |
| `duration` | `int` (ms) | presentation duration, 0 for live |
| `completed_duration` | `int` (ms) | completed media duration; basis of media progress |
| `downloaded_length` | `int` (bytes) | retained media payload (independent of network speed) |
| `progress` | `float` | 0..1 media progress |
| `length_known` | `bool` | False until final length is known |
| `error`, `error_code` | `str` | diagnostic text + structured error code (empty on success) |
| `tracks` | `list[MediaTrack]` | available tracks (after probing) |

### `MediaTrack` (aria2-next)

| Property | Type | Meaning |
|----------|------|---------|
| `track_id` | `str` | opaque native ID; do not parse |
| `type` | `str` | `video`, `audio`, `subtitle` |
| `codec` | `str` | codec identifier (e.g. `avc1.640028`) |
| `language` | `str` | BCP-47 language tag |
| `bandwidth` | `int` (bps) | nominal bandwidth |
| `frame_rate` | `float` | decimal fps; `0` if unknown |
| `channels` | `int` | audio channel count |

### `MediaFeatures` (aria2-next)

Capability map from `getVersion.mediaFeatures`. Known flags:

| Property | Meaning |
|----------|---------|
| `request_contexts` | server supports scoped HTTP request contexts |
| `stable_track_ids` | track IDs remain stable across playlist refreshes |
| `structured_errors` | server returns structured `errorCode` values |

Unknown flags can be inspected via `.raw`.

## Events (WebSocket only)

`WebSocketRPCClient.on(event, callback)` registers an async callback for a
given `Aria2Event`. The callback receives the event's raw payload dict.

```python
client.on(Aria2Event.DOWNLOAD_COMPLETE, on_complete)
```

Available events: `DOWNLOAD_START`, `DOWNLOAD_PAUSE`, `DOWNLOAD_STOP`,
`DOWNLOAD_COMPLETE`, `DOWNLOAD_ERROR`, `BT_DOWNLOAD_COMPLETE`.

## Errors

| Exception | When |
|-----------|------|
| `Aria2ConnectionError` | TCP / WebSocket connection failure |
| `Aria2TimeoutError` | RPC timeout |
| `Aria2AuthenticationError` | secret token rejected |
| `Aria2RPCError` | aria2 returned a JSON-RPC error (has `.code`, `.message`) |

All inherit from `Aria2Error`, so a single `except Aria2Error` catches
everything from this library.

## Versioning

`aria2rpc` carries its own version in `src/aria2rpc/_version.py` (currently
`0.4.0`). It is independent of the TUI's `pyproject.toml` version. Bump it
when the library gains methods, models, or breaking changes — not for TUI-only
work.