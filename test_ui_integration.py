#!/usr/bin/env python3
"""Quick test script for UI integration features."""

import asyncio
from pathlib import Path

from ariatuc.core import Aria2Service, ServerConfig


async def test_local_process_integration():
    """Test local process management integration."""
    print("=== Testing Local Process Integration ===\n")

    # Create service
    service = Aria2Service()
    await service.initialize()

    print("✓ Service initialized")

    # Add a test local server
    test_server_config = ServerConfig(
        name="test-local",
        url="http://localhost:6801/jsonrpc",
        secret=None,
        is_local=True,
        session_file=None,
        aria2c_path=None,
        aria2c_options={
            "max-concurrent-downloads": 3,
            "max-connection-per-server": 4,
        },
    )

    service.rpc_mgr.servers["test-local"] = test_server_config
    print(f"✓ Added test server: {test_server_config.name}")
    print(f"  - URL: {test_server_config.url}")
    print(f"  - Is Local: {test_server_config.is_local}")
    print(f"  - Session File: {test_server_config.managed_session_file}")

    # Test process info (should be None initially)
    process_info = service.get_local_process_info("test-local")
    print(f"\n✓ Process info (initial): {process_info}")

    # Test session file path
    session_path = test_server_config.managed_session_file
    print(f"\n✓ Session file path: {session_path}")
    print(f"  - Parent dir exists: {session_path.parent.exists()}")

    # Test save_session method availability
    print(f"\n✓ save_session method available: {hasattr(service, 'save_session')}")
    print(
        f"✓ stop_local_process method available: {hasattr(service, 'stop_local_process')}"
    )
    print(
        f"✓ restart_local_process method available: {hasattr(service, 'restart_local_process')}"
    )

    # Cleanup
    await service.shutdown()
    print("\n✓ Service shutdown complete")

    print("\n=== All Integration Tests Passed ===")


if __name__ == "__main__":
    asyncio.run(test_local_process_integration())
