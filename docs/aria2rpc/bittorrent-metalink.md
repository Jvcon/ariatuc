# BitTorrent and Metalink Support in aria2rpc

This document demonstrates the BitTorrent and Metalink functionality added to the aria2rpc package.

## Overview

The aria2rpc package now supports:
- Adding BitTorrent downloads with `add_torrent()`
- Adding Metalink downloads with `add_metalink()`
- Fetching BitTorrent peer information with `get_peers()`
- Fetching server/tracker information with `get_servers()`

All functionality is available in both `HTTPRPCClient` and `WebSocketRPCClient`.

## BitTorrent Examples

### Adding a Torrent Download

```python
from aria2rpc import Aria2Client

async def add_torrent_example():
    async with Aria2Client("http://localhost:6800/jsonrpc") as client:
        # Read torrent file
        with open("ubuntu.torrent", "rb") as f:
            torrent_data = f.read()

        # Add the torrent download
        gid = await client.add_torrent(torrent_data)
        print(f"Torrent added with GID: {gid}")

        # Check status
        status = await client.tell_status(gid)
        print(f"Status: {status.status}")
        print(f"Upload speed: {status.upload_speed} bytes/s")
        print(f"Seeders: {status.num_seeders}")
```

### Adding Torrent with Options

```python
async def add_torrent_with_options():
    async with Aria2Client("http://localhost:6800/jsonrpc") as client:
        with open("file.torrent", "rb") as f:
            torrent_data = f.read()

        # Add with web seeds and custom options
        gid = await client.add_torrent(
            torrent_data,
            uris=["http://example.com/webseed"],  # Web seed URIs
            options={
                "dir": "/downloads/torrents",      # Download directory
                "seed-ratio": "2.0",                # Seed until ratio reaches 2.0
                "max-upload-limit": "1M",           # Limit upload to 1MB/s
            },
            position=0  # Add to front of queue
        )
        print(f"Torrent added: {gid}")
```

### Getting Peer Information

```python
from aria2rpc import Aria2Client

async def get_peer_info():
    async with Aria2Client("http://localhost:6800/jsonrpc") as client:
        # Get peers for a BitTorrent download
        peers = await client.get_peers("2089b05ecca3d829")

        for peer in peers:
            print(f"Peer: {peer.ip}:{peer.port}")
            print(f"  Download: {peer.download_speed} bytes/s")
            print(f"  Upload: {peer.upload_speed} bytes/s")
            print(f"  Seeder: {peer.seeder}")
            print(f"  Choking us: {peer.peer_choking}")
            print()
```

### Getting Server/Tracker Information

```python
async def get_server_info():
    async with Aria2Client("http://localhost:6800/jsonrpc") as client:
        # Get servers/trackers for a download
        file_servers = await client.get_servers("2089b05ecca3d829")

        for fs in file_servers:
            print(f"File {fs.index}:")
            for server in fs.servers:
                print(f"  URI: {server.uri}")
                print(f"  Current: {server.current_uri}")
                print(f"  Speed: {server.download_speed} bytes/s")
            print()
```

## Metalink Examples

### Adding a Metalink Download

```python
from aria2rpc import Aria2Client

async def add_metalink_example():
    async with Aria2Client("http://localhost:6800/jsonrpc") as client:
        # Read metalink file
        with open("file.metalink", "rb") as f:
            metalink_data = f.read()

        # Add metalink download (returns list of GIDs, one per file)
        gids = await client.add_metalink(metalink_data)
        print(f"Metalink added with {len(gids)} files:")
        for gid in gids:
            print(f"  - {gid}")

        # Check status of first file
        if gids:
            status = await client.tell_status(gids[0])
            print(f"First file: {status.files[0]['path']}")
```

### Adding Metalink with Options

```python
async def add_metalink_with_options():
    async with Aria2Client("http://localhost:6800/jsonrpc") as client:
        with open("linux.metalink", "rb") as f:
            metalink_data = f.read()

        # Add with custom options
        gids = await client.add_metalink(
            metalink_data,
            options={
                "dir": "/downloads/linux",
                "max-connection-per-server": "4",
            },
            position=0
        )

        print(f"Added {len(gids)} downloads from metalink")

        # Monitor all downloads
        for gid in gids:
            status = await client.tell_status(gid)
            print(f"{gid}: {status.completed_length}/{status.total_length}")
```

## Data Models

### Peer Model

The `Peer` model provides typed access to BitTorrent peer information:

```python
peer.peer_id        # Peer ID
peer.ip             # IP address
peer.port           # Port number
peer.download_speed # Download speed in bytes/sec
peer.upload_speed   # Upload speed in bytes/sec
peer.seeder         # Boolean: is this a seeder?
peer.am_choking     # Boolean: are we choking this peer?
peer.peer_choking   # Boolean: is this peer choking us?
peer.bitfield       # Hex representation of bitfield
```

### Server Model

The `Server` model provides information about download sources:

```python
server.uri            # Original URI
server.current_uri    # Current URI (after redirects)
server.download_speed # Download speed in bytes/sec
```

### FileServer Model

The `FileServer` model groups servers by file:

```python
file_server.index    # File index (1-based)
file_server.servers  # List of Server objects
```

## WebSocket Support

All BitTorrent and Metalink methods are also available with WebSocket connections:

```python
from aria2rpc import Aria2Client, Aria2Event

async def websocket_torrent_example():
    async with Aria2Client("ws://localhost:6800/jsonrpc") as client:
        # Subscribe to BitTorrent completion event
        async def on_bt_complete(event):
            print(f"BitTorrent download {event['gid']} completed!")

        client.on(Aria2Event.BT_DOWNLOAD_COMPLETE, on_bt_complete)

        # Add torrent
        with open("file.torrent", "rb") as f:
            gid = await client.add_torrent(f.read())

        # All BitTorrent methods work the same
        peers = await client.get_peers(gid)
        servers = await client.get_servers(gid)

        # Keep connection alive to receive events
        await asyncio.sleep(3600)
```

## Error Handling

All methods raise appropriate exceptions on errors:

```python
from aria2rpc import Aria2Client, Aria2RPCError

async def error_handling_example():
    try:
        async with Aria2Client("http://localhost:6800/jsonrpc") as client:
            with open("invalid.torrent", "rb") as f:
                gid = await client.add_torrent(f.read())
    except Aria2RPCError as e:
        print(f"RPC Error {e.code}: {e.message}")
    except FileNotFoundError:
        print("Torrent file not found")
```

## Notes

1. **Base64 Encoding**: The library automatically handles base64 encoding of torrent and metalink files. Just pass the raw bytes.

2. **BitTorrent-specific fields**: The `DownloadStatus` model already includes BitTorrent-specific properties like `upload_length`, `upload_speed`, and `num_seeders`.

3. **Peer information**: `get_peers()` only returns data for BitTorrent downloads. For non-BitTorrent downloads, it returns an empty list.

4. **Metalink returns multiple GIDs**: Unlike `add_uri()` or `add_torrent()` which return a single GID, `add_metalink()` returns a list of GIDs (one for each file in the metalink).

5. **Server information**: `get_servers()` works for both HTTP/FTP and BitTorrent downloads. For BitTorrent, it shows tracker information.
