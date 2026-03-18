"""Example: Using Aria2Service layer.

This example demonstrates the high-level Service API that coordinates
all managers and provides business logic for the UI layer.

Run with:
    poetry run python examples/service_usage.py
"""

import asyncio
import logging

from ariatuc.core import Aria2Service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main example function."""
    logger.info("=== Aria2Service Usage Example ===\n")

    # 1. Create and initialize service
    logger.info("1. Creating and initializing service...")
    service = Aria2Service()
    await service.initialize()
    logger.info("   ✅ Service initialized")

    # 2. Add a server
    logger.info("\n2. Adding aria2 server...")
    service.add_server(
        name="local",
        url="ws://localhost:6800/jsonrpc",  # WebSocket for events
        secret=None
    )
    logger.info("   ✅ Server added")

    # 3. Connect to server
    logger.info("\n3. Connecting to server...")
    try:
        connected = await service.connect("local")
        if connected:
            logger.info(f"   ✅ Connected successfully")
            logger.info(f"   Protocol: {'WebSocket' if service.is_websocket else 'HTTP'}")
            logger.info(f"   Event monitoring: {'Active' if service.event_monitoring_active else 'Inactive'}")
        else:
            logger.error("   ❌ Connection failed")
            return
    except Exception as e:
        logger.error(f"   ❌ Connection error: {e}")
        logger.error("   Make sure aria2c is running with: aria2c --enable-rpc")
        return

    # 4. Get aria2 version
    logger.info("\n4. Getting aria2 version...")
    version = await service.get_version()
    if version:
        logger.info(f"   aria2 version: {version.version}")
        logger.info(f"   Features: {', '.join(version.enabled_features)}")

    # 5. Get global statistics
    logger.info("\n5. Getting global statistics...")
    stats = await service.get_global_stat()
    if stats:
        logger.info(f"   Active: {stats.num_active}")
        logger.info(f"   Waiting: {stats.num_waiting}")
        logger.info(f"   Stopped: {stats.num_stopped}")
        logger.info(f"   Download speed: {stats.download_speed} bytes/s")
        logger.info(f"   Upload speed: {stats.upload_speed} bytes/s")

    # 6. Setup UI callback (simulate)
    logger.info("\n6. Setting up callbacks...")

    def ui_refresh():
        """Simulated UI refresh callback."""
        logger.debug("UI refresh triggered")

    def notification(data):
        """Simulated notification callback."""
        logger.info(f"Notification: {data['title']} - {data['message']}")

    service.set_ui_refresh_callback(ui_refresh)
    service.set_notification_callback(notification)
    logger.info("   ✅ Callbacks registered")

    # 7. Add a download (commented to avoid unwanted downloads)
    logger.info("\n7. Download operations example...")
    logger.info("   (Skipping actual download to avoid unwanted files)")

    # Example of adding a download:
    """
    options = DownloadOptions(
        dir="/tmp/ariatuc-test",
        max_connection_per_server=4,
        split=4
    )
    gid = await service.add_download(
        ["http://example.com/test.zip"],
        options=options
    )
    logger.info(f"   Download added: {gid}")
    """

    # 8. Query downloads
    logger.info("\n8. Querying downloads...")
    await service.refresh_downloads()

    active = service.get_active_downloads()
    waiting = service.get_waiting_downloads()
    paused = service.get_paused_downloads()
    stopped = service.get_stopped_downloads()

    logger.info(f"   Active downloads: {len(active)}")
    logger.info(f"   Waiting downloads: {len(waiting)}")
    logger.info(f"   Paused downloads: {len(paused)}")
    logger.info(f"   Stopped downloads: {len(stopped)}")

    # Show details of active downloads
    if active:
        logger.info("\n   Active download details:")
        for dl in active[:3]:  # Show first 3
            logger.info(f"     GID: {dl.gid[:8]}...")
            logger.info(f"     Status: {dl.status.value}")
            logger.info(f"     Progress: {dl.progress:.1f}%")
            logger.info(f"     Speed: {dl.download_speed} bytes/s")
            logger.info(f"     Size: {dl.completed_length}/{dl.total_length} bytes")
            logger.info("")

    # 9. Start auto-refresh
    logger.info("9. Starting auto-refresh...")
    await service.start_auto_refresh(interval=2.0)
    logger.info("   ✅ Auto-refresh started (2 second interval)")

    # Wait a bit to show auto-refresh working
    logger.info("\n   Waiting 5 seconds to demonstrate auto-refresh...")
    await asyncio.sleep(5)

    # 10. Stop auto-refresh
    logger.info("\n10. Stopping auto-refresh...")
    await service.stop_auto_refresh()
    logger.info("    ✅ Auto-refresh stopped")

    # 11. Batch operations example
    logger.info("\n11. Batch operations example...")
    logger.info("    (Would pause/resume all downloads)")

    # Example:
    """
    await service.pause_all()
    logger.info("    All downloads paused")

    await asyncio.sleep(2)

    await service.resume_all()
    logger.info("    All downloads resumed")
    """

    # 12. Server management
    logger.info("\n12. Server management...")
    servers = service.list_servers()
    logger.info(f"    Total servers: {len(servers)}")
    for server in servers:
        current_marker = "✓" if server['is_current'] else " "
        logger.info(f"    [{current_marker}] {server['name']}")
        logger.info(f"        URL: {server['url']}")
        logger.info(f"        Protocol: {server['protocol']}")
        logger.info(f"        State: {server['state']}")

    # 13. Test connection health
    logger.info("\n13. Testing connection health...")
    healthy = await service.test_connection()
    logger.info(f"    Connection healthy: {healthy}")

    # 14. Cleanup
    logger.info("\n14. Shutting down service...")
    await service.shutdown()
    logger.info("    ✅ Service shutdown complete")

    logger.info("\n=== Example Complete ===")

    # Summary
    logger.info("\n📊 Summary:")
    logger.info("✅ Service layer provides a clean, high-level API")
    logger.info("✅ Automatic state synchronization with aria2")
    logger.info("✅ Event-driven updates (when using WebSocket)")
    logger.info("✅ Unified error handling")
    logger.info("✅ Ready for UI layer integration")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
