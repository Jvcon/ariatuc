"""Example: Integration of all core managers.

This example demonstrates how to use the core managers together:
1. ConfigManager - Load configuration
2. RPCManager - Connect to aria2 server (auto protocol selection)
3. EventManager - Subscribe to events (if WebSocket)
4. DownloadManager - Track download states

Run with:
    poetry run python examples/manager_integration.py
"""

import asyncio
import logging
from pathlib import Path

from aria2rpc import Aria2Event
from ariatuc.core import (
    ConfigManager,
    RPCManager,
    EventManager,
    DownloadManager,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main example function."""
    logger.info("=== Manager Integration Example ===\n")

    # 1. Initialize ConfigManager
    logger.info("1. Initializing ConfigManager...")
    config_dir = Path.home() / ".config" / "ariatuc-example"
    config_mgr = ConfigManager(config_dir=config_dir)
    config = config_mgr.load()
    logger.info(f"   Config loaded from: {config_mgr.config_path}")
    logger.info(f"   Servers: {len(config.servers)}")
    logger.info(f"   Prefer WebSocket: {config.prefer_websocket}")

    # 2. Initialize RPCManager
    logger.info("\n2. Initializing RPCManager...")
    rpc_mgr = RPCManager(connection_timeout=10)

    # Add a server (try WebSocket first, fallback to HTTP)
    # Note: You should have aria2c running with:
    #   aria2c --enable-rpc --rpc-listen-all=false --rpc-allow-origin-all=true
    server_url = "ws://localhost:6800/jsonrpc"  # WebSocket URL
    # server_url = "http://localhost:6800/jsonrpc"  # HTTP URL alternative

    rpc_mgr.add_server(
        name="local",
        url=server_url,
        secret=None  # Add your secret if configured
    )

    # Check protocol
    protocol = rpc_mgr.get_protocol("local")
    logger.info(f"   Server protocol: {protocol.value}")
    logger.info(f"   Is WebSocket: {rpc_mgr.is_websocket('local')}")

    # 3. Connect to server
    logger.info("\n3. Connecting to aria2 server...")
    connected = await rpc_mgr.connect("local")

    if not connected:
        logger.error("   ❌ Failed to connect to aria2 server")
        logger.error("   Make sure aria2c is running with RPC enabled:")
        logger.error("   aria2c --enable-rpc")
        return

    logger.info("   ✅ Connected successfully")

    # 4. Initialize EventManager (only works with WebSocket)
    logger.info("\n4. Initializing EventManager...")
    event_mgr = EventManager()

    ws_client = rpc_mgr.get_websocket_client("local")
    if ws_client:
        event_mgr.set_client(ws_client)
        logger.info(f"   ✅ Event monitoring active: {event_mgr.is_active()}")

        # Register event callbacks
        async def on_download_complete(event_data):
            gid = event_data.get('gid', 'unknown')
            logger.info(f"   🎉 Download completed: GID {gid}")

        async def on_download_error(event_data):
            gid = event_data.get('gid', 'unknown')
            logger.error(f"   ❌ Download error: GID {gid}")

        event_mgr.on(Aria2Event.DOWNLOAD_COMPLETE, on_download_complete)
        event_mgr.on(Aria2Event.DOWNLOAD_ERROR, on_download_error)
        logger.info("   Registered callbacks for DOWNLOAD_COMPLETE and DOWNLOAD_ERROR")
    else:
        logger.info("   ℹ️  No WebSocket client, events unavailable (using HTTP)")

    # 5. Initialize DownloadManager
    logger.info("\n5. Initializing DownloadManager...")
    download_mgr = DownloadManager()
    logger.info("   ✅ DownloadManager initialized")

    # 6. Test RPC operations
    logger.info("\n6. Testing RPC operations...")
    client = rpc_mgr.get_client("local")

    if client:
        # Get version
        version = await client.get_version()
        logger.info(f"   aria2 version: {version.version}")

        # Get global stats
        stats = await client.get_global_stat()
        logger.info(f"   Active downloads: {stats.num_active}")
        logger.info(f"   Waiting downloads: {stats.num_waiting}")
        logger.info(f"   Stopped downloads: {stats.num_stopped}")
        logger.info(f"   Download speed: {stats.download_speed} bytes/s")

        # Get active downloads
        active_downloads = await client.tell_active()
        logger.info(f"\n7. Active downloads: {len(active_downloads)}")

        for dl in active_downloads:
            # Update download manager
            download_mgr.update_download(dl.gid, {
                'status': dl.status,
                'totalLength': dl.total_length,
                'completedLength': dl.completed_length,
                'downloadSpeed': dl.download_speed,
                'uploadSpeed': dl.upload_speed,
                'files': [],
                'connections': dl.connections,
            })

            download = download_mgr.get_download(dl.gid)
            if download:
                logger.info(f"   GID: {dl.gid[:8]}... - Progress: {download.progress:.1f}%")

        # Example: Add a download (commented out to avoid unwanted downloads)
        # logger.info("\n8. Adding a test download...")
        # gid = await client.add_uri(["http://example.com/test.zip"])
        # logger.info(f"   Download added with GID: {gid}")

        # If using WebSocket, wait a bit for events
        if ws_client and event_mgr.is_active():
            logger.info("\n9. Waiting for events (10 seconds)...")
            logger.info("   (Events will be logged as they arrive)")
            await asyncio.sleep(10)

            # Show event statistics
            event_counts = event_mgr.get_event_counts()
            logger.info("\n   Event statistics:")
            for event_name, count in event_counts.items():
                if count > 0:
                    logger.info(f"     {event_name}: {count}")

    # 7. Cleanup
    logger.info("\n10. Cleaning up...")
    await rpc_mgr.disconnect("local")
    event_mgr.disable()
    logger.info("   ✅ Disconnected and cleaned up")

    logger.info("\n=== Example Complete ===")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
