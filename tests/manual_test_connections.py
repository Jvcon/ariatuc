#!/usr/bin/env python3
"""Manual test script for testing HTTP and WebSocket connections.

This script can be used to manually verify that both HTTP and WebSocket
connections work correctly with aria2 RPC.

Usage:
    # Test HTTP connection (default)
    python tests/manual_test_connections.py

    # Test WebSocket connection
    python tests/manual_test_connections.py --websocket

    # Custom URL and secret
    python tests/manual_test_connections.py --url ws://localhost:6800/jsonrpc --secret mytoken
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from aria2rpc import Aria2Client
from aria2rpc.http import HTTPRPCClient
from aria2rpc.websocket import WebSocketRPCClient


async def test_http_connection(
    url: str = "http://localhost:6800/jsonrpc", secret: str | None = None
):
    """Test HTTP RPC connection.

    Args:
        url: HTTP RPC URL
        secret: Optional RPC secret
    """
    print(f"\n{'=' * 60}")
    print("Testing HTTP Connection")
    print(f"URL: {url}")
    print(f"Secret: {'***' if secret else 'None'}")
    print(f"{'=' * 60}\n")

    try:
        # Create HTTP client
        client = Aria2Client(url, secret=secret)

        if not isinstance(client, HTTPRPCClient):
            print(f"❌ ERROR: Expected HTTPRPCClient, got {type(client).__name__}")
            return False

        print("✓ HTTP client created")

        # Test get_version
        print("→ Testing get_version()...")
        version = await asyncio.wait_for(client.get_version(), timeout=10)
        print(f"✓ Connected! aria2 version: {version.version}")
        print(f"  Enabled features: {', '.join(version.enabled_features)}")

        # Test get_global_stat
        print("\n→ Testing get_global_stat()...")
        stats = await asyncio.wait_for(client.get_global_stat(), timeout=10)
        print("✓ Global stats retrieved:")
        print(f"  Download speed: {stats.download_speed} B/s")
        print(f"  Upload speed: {stats.upload_speed} B/s")
        print(f"  Active downloads: {stats.num_active}")

        print(f"\n{'=' * 60}")
        print("✅ HTTP Connection Test PASSED")
        print(f"{'=' * 60}\n")
        return True

    except TimeoutError:
        print("\n❌ Connection timeout!")
        print("Make sure aria2c is running with:")
        print("  aria2c --enable-rpc")
        return False

    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        return False


async def test_websocket_connection(
    url: str = "ws://localhost:6800/jsonrpc", secret: str | None = None
):
    """Test WebSocket RPC connection.

    Args:
        url: WebSocket RPC URL
        secret: Optional RPC secret
    """
    print(f"\n{'=' * 60}")
    print("Testing WebSocket Connection")
    print(f"URL: {url}")
    print(f"Secret: {'***' if secret else 'None'}")
    print(f"{'=' * 60}\n")

    try:
        # Create WebSocket client
        client = Aria2Client(url, secret=secret)

        if not isinstance(client, WebSocketRPCClient):
            print(f"❌ ERROR: Expected WebSocketRPCClient, got {type(client).__name__}")
            return False

        print("✓ WebSocket client created")

        # Explicitly connect
        print("→ Connecting to WebSocket...")
        await asyncio.wait_for(client.connect(), timeout=10)
        print("✓ WebSocket connected")

        # Test get_version
        print("\n→ Testing get_version()...")
        version = await asyncio.wait_for(client.get_version(), timeout=10)
        print(f"✓ RPC call successful! aria2 version: {version.version}")
        print(f"  Enabled features: {', '.join(version.enabled_features)}")

        # Test get_global_stat
        print("\n→ Testing get_global_stat()...")
        stats = await asyncio.wait_for(client.get_global_stat(), timeout=10)
        print("✓ Global stats retrieved:")
        print(f"  Download speed: {stats.download_speed} B/s")
        print(f"  Upload speed: {stats.upload_speed} B/s")
        print(f"  Active downloads: {stats.num_active}")

        # Disconnect
        print("\n→ Disconnecting...")
        await client.close()
        print("✓ Disconnected cleanly")

        print(f"\n{'=' * 60}")
        print("✅ WebSocket Connection Test PASSED")
        print(f"{'=' * 60}\n")
        return True

    except TimeoutError:
        print("\n❌ Connection timeout!")
        print("Make sure aria2c is running with WebSocket enabled:")
        print("  aria2c --enable-rpc")
        return False

    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run connection tests."""
    import argparse

    parser = argparse.ArgumentParser(description="Test aria2 RPC connections")
    parser.add_argument(
        "--websocket", action="store_true", help="Test WebSocket connection instead of HTTP"
    )
    parser.add_argument(
        "--url",
        type=str,
        help="Custom RPC URL (e.g., http://localhost:6800/jsonrpc or ws://localhost:6800/jsonrpc)",
    )
    parser.add_argument("--secret", type=str, help="RPC secret token")

    args = parser.parse_args()

    # Determine test type and URL
    if args.websocket:
        url = args.url or "ws://localhost:6800/jsonrpc"
        result = await test_websocket_connection(url, args.secret)
    else:
        url = args.url or "http://localhost:6800/jsonrpc"
        result = await test_http_connection(url, args.secret)

    # Exit with appropriate code
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    asyncio.run(main())
