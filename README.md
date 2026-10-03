# ariatuc

**Terminal control surface for aria2 and aria2-next.**

A Python workspace that ships two things in one repo:

- **`aria2rpc`** — a standalone Python client library for the aria2 JSON-RPC interface, with
  first-class support for [`aria2-next`](https://github.com/AnInsomniacy/aria2-next) extensions
  (HLS / DASH media tasks, capability detection, `finishMedia`, `retryMedia`).
- **`ariatuc`** — a Textual TUI built on top of `aria2rpc`. A terminal alternative to AriaNg for
  anyone running `aria2c` or `aria2-next`.

The library is the product. The TUI is the reference application and the UX test bed.

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Why ariatuc

- 🚀 **One client, two engines** — speaks both upstream `aria2c` and the `aria2-next` fork
  transparently. Capability detection tells you which features are available.
- ⌨️ **Keyboard-driven** — Vim-style navigation and lazygit-inspired panels for download
  management.
- 📡 **Real-time updates** — WebSocket transport delivers `onDownloadStart`, `onDownloadComplete`
  and friends without polling.
- 🎞️ **Media-aware** (with `aria2-next`) — HLS / DASH downloads report a typed `media` object
  with track lists; the library exposes `finish_media()` and `retry_media()`.
- 🧱 **Library-first** — `aria2rpc` is reusable from any async Python program; the TUI is one
  consumer among many.

## Quick start

### 1. Pick your engine

```bash
# Vanilla aria2c
brew install aria2          # macOS
sudo apt install aria2      # Debian / Ubuntu
aria2c --enable-rpc

# Or aria2-next (fork with native HLS / DASH and ED2K)
# https://github.com/AnInsomniacy/aria2-next/releases
aria2-next --enable-rpc
```

### 2. Install ariatuc

```bash
git clone https://github.com/Jvcon/ariatuc.git
cd ariatuc
poetry install
poetry run ariatuc
```

## Using `aria2rpc` from your own code

```python
from aria2rpc import Aria2Client, is_aria2_next

async with Aria2Client("ws://localhost:6800/jsonrpc") as client:
    # Capability detection
    if await is_aria2_next(client):
        print("Connected to aria2-next; HLS / DASH available")

    # Standard aria2 RPC
    gid = await client.add_uri(["https://example.com/file.iso"])
    status = await client.tell_status(gid)
    print(f"Progress: {status.completed_length}/{status.total_length}")

    # aria2-next: media-aware progress + finish / retry
    if status.media is not None:
        print(f"Media state: {status.media.state}, "
              f"protocol: {status.media.protocol}")
        if status.media.state == "awaiting-selection":
            await client.change_option(gid, {"media-pause-after-probe": "false"})
```

See [`docs/aria2rpc/api.md`](docs/aria2rpc/api.md) for the full reference and
[`docs/aria2rpc/aria2-next.md`](docs/aria2rpc/aria2-next.md) for the media flow.

## Documentation

📖 **[Full documentation](docs/)**

| Audience | Start here |
|----------|-----------|
| Users running the TUI | [docs/quick-start.md](docs/quick-start.md) |
| Engineers integrating `aria2rpc` | [docs/aria2rpc/getting-started.md](docs/aria2rpc/getting-started.md) |
| Anyone interested in where this is going | [docs/ROADMAP.md](docs/ROADMAP.md) |
| AI coding agents | [AGENTS.md](AGENTS.md) |

## Development

```bash
mise run lint          # ruff check
mise run format        # ruff format
mise run mypy          # static type check
mise run test:unit     # fast tests, no aria2c daemon
mise run test          # full suite (auto-manages aria2c)
```

See [docs/development.md](docs/development.md) for the toolchain.

## Project status (2026-10)

| Component | State |
|-----------|-------|
| `aria2rpc` library | Mature; aria2-next extensions landed in R1 |
| `ariatuc` TUI | Usable; media-aware features land in R2 |
| Roadmap | [docs/ROADMAP.md](docs/ROADMAP.md) |

## Acknowledgments

- [aria2](https://aria2.github.io/) — the upstream download utility
- [aria2-next](https://github.com/AnInsomniacy/aria2-next) — maintained fork with HLS / DASH and ED2K
- [Textual](https://textual.textualize.io/) — Python TUI framework
- [AriaNg](https://github.com/mayswind/AriaNg) — feature reference
- [lazygit](https://github.com/jesseduffield/lazygit) — UX inspiration

## License

MIT License — see [LICENSE](LICENSE) for details.