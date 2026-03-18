# Testing Guide for aria2rpc

This guide explains the unified testing system for the aria2rpc package, which provides a consistent and easy-to-use interface for running different types of tests.

## Overview

The testing infrastructure has been unified into a single Python-based system with the following features:

- **Unified test runner** (`scripts/run_tests.py`) - Replaces previous shell scripts
- **Pytest markers** for categorizing tests (unit, integration)
- **Mise tasks** for easy command execution (like npm scripts)
- **Automatic aria2c lifecycle management** for integration tests
- **Clear separation** between unit and integration tests

## Quick Start

### Running Tests with Mise (Recommended)

```bash
# Run all tests (unit + integration)
mise run test

# Run only unit tests (fast, no aria2c needed)
mise run test:unit

# Run only integration tests (requires aria2c)
mise run test:integration

# Run with coverage report
mise run test:coverage

# Setup aria2c configuration
mise run test:setup
```

### Running Tests with Python Script

```bash
# Run all tests
python scripts/run_tests.py

# Run only unit tests
python scripts/run_tests.py --unit

# Run only integration tests
python scripts/run_tests.py --integration

# Run with coverage
python scripts/run_tests.py --coverage

# Just setup aria2c without running tests
python scripts/run_tests.py --setup-only

# Run tests assuming aria2c is already running
python scripts/run_tests.py --no-daemon
```

### Running Tests with Pytest Directly

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/aria2rpc/unit/test_http_client.py

# Run only unit tests (using markers)
poetry run pytest -m "not integration"

# Run only integration tests
poetry run pytest -m integration

# Run with verbose output
poetry run pytest -v

# Run with coverage
poetry run pytest --cov=aria2rpc --cov-report=term-missing
```

## Test Categories

### Unit Tests

Unit tests are **fast, isolated tests** that don't require external dependencies like a running aria2c instance. They use mocking to simulate external interactions.

**Location**:
- `tests/aria2rpc/unit/test_http_client.py` - Unit tests for HTTP client (mocked RPC calls)
- `tests/ariatuc/unit/test_download_manager.py` - Tests for download manager

**Characteristics**:
- Run in < 1 second
- No aria2c installation required
- Use `unittest.mock.AsyncMock` for mocking
- Test business logic, parameter handling, error conditions

**Running**:
```bash
mise run test:unit
# or
python scripts/run_tests.py --unit
```

### Integration Tests

Integration tests require a **running aria2c instance** and test actual RPC communication over WebSocket.

**Location**:
- `tests/aria2rpc/integration/test_websocket_client.py` - WebSocket client integration tests
- `tests/aria2rpc/integration/test_websocket_complete.py` - Additional WebSocket tests

**Characteristics**:
- Require aria2c installation
- Test real network communication
- Marked with `@pytest.mark.integration`
- Automatically managed by test runner (starts/stops aria2c)

**Running**:
```bash
mise run test:integration
# or
python scripts/run_tests.py --integration
```

## Test Markers

Pytest markers are used to categorize tests:

```python
import pytest

# Mark entire module as integration tests
pytestmark = pytest.mark.integration

# Or mark individual tests
@pytest.mark.integration
async def test_websocket_connection():
    pass

@pytest.mark.unit
async def test_parameter_validation():
    pass
```

Available markers (defined in `pyproject.toml`):
- `integration` - Tests requiring aria2c
- `unit` - Fast isolated tests
- `asyncio` - Async tests (auto-detected)

## Unified Test Runner

The `scripts/run_tests.py` script provides comprehensive test management.

### Features

1. **Automatic aria2c Lifecycle**:
   - Checks if aria2c is installed
   - Creates test configuration
   - Starts aria2c daemon before integration tests
   - Stops daemon after tests complete
   - Handles cleanup on interruption (Ctrl+C)

2. **Smart Test Selection**:
   - `--unit`: Only unit tests
   - `--integration`: Only integration tests
   - Default: All tests

3. **Flexible Daemon Management**:
   - `--no-daemon`: Don't start/stop aria2c (assume already running)
   - `--setup-only`: Just create config and exit

4. **Clear Output**:
   - Color-coded messages (green=success, yellow=warning, red=error)
   - Section headers for different phases
   - Test summary at the end

### Usage Examples

```bash
# Standard workflow - run all tests
python scripts/run_tests.py

# Development workflow - unit tests only (fast feedback)
python scripts/run_tests.py --unit

# Full validation before commit
python scripts/run_tests.py --coverage

# Manual aria2c control
# Terminal 1:
aria2c --conf-path=.test_aria2/aria2.conf

# Terminal 2:
python scripts/run_tests.py --no-daemon

# Setup aria2c config once, then run tests multiple times
python scripts/run_tests.py --setup-only
aria2c --conf-path=.test_aria2/aria2.conf &
python scripts/run_tests.py --no-daemon
python scripts/run_tests.py --no-daemon --unit
```

## Mise Tasks

Mise tasks provide convenient shortcuts (similar to npm scripts in package.json).

### Available Tasks

| Task | Command | Description |
|------|---------|-------------|
| `test` | `mise run test` | Run all tests with aria2c management |
| `test:unit` | `mise run test:unit` | Run only unit tests (fast) |
| `test:integration` | `mise run test:integration` | Run only integration tests |
| `test:coverage` | `mise run test:coverage` | Run all tests with coverage |
| `test:unit:coverage` | `mise run test:unit:coverage` | Unit tests with coverage |
| `test:setup` | `mise run test:setup` | Setup aria2c configuration |
| `test:no-daemon` | `mise run test:no-daemon` | Run without managing aria2c |
| `test:pytest` | `mise run test:pytest` | Direct pytest access |

### Viewing Available Tasks

```bash
# List all available mise tasks
mise tasks

# Get help for a specific task
mise run test --help
```

## aria2c Setup

### Installation

The test runner will check for aria2c and provide installation instructions if missing:

```bash
# macOS
brew install aria2

# Ubuntu/Debian
sudo apt install aria2

# Arch Linux
sudo pacman -S aria2
```

### Test Configuration

The test runner creates a dedicated aria2c configuration at `.test_aria2/`:

```
.test_aria2/
├── aria2.conf          # aria2c configuration
├── aria2.log           # Log file
├── aria2.pid           # Process ID file
├── session.txt         # Session state
└── downloads/          # Download directory
```

**Configuration highlights**:
- RPC enabled on `localhost:6800`
- No authentication (test environment)
- Downloads go to `.test_aria2/downloads/`
- Session persistence enabled
- Logging to `.test_aria2/aria2.log`

**Note**: The `.test_aria2/` directory is created automatically and is typically added to `.gitignore`.

## Continuous Integration

For CI environments, use the following pattern:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Install aria2
        run: sudo apt install -y aria2

      - name: Install mise
        run: curl https://mise.run | sh

      - name: Install dependencies
        run: |
          mise install
          poetry install --with dev

      - name: Run unit tests
        run: mise run test:unit

      - name: Run integration tests
        run: mise run test:integration

      - name: Generate coverage
        run: mise run test:coverage
```

## Writing Tests

### Unit Test Example

```python
import pytest
from unittest.mock import AsyncMock, patch
from aria2rpc import HTTPRPCClient

@pytest.mark.asyncio
async def test_add_uri():
    """Test adding a URI download (mocked)."""
    client = HTTPRPCClient("http://localhost:6800/jsonrpc")

    with patch.object(client, "_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "abc123"

        gid = await client.add_uri(["http://example.com/file.zip"])

        # Verify the call was made correctly
        mock_call.assert_called_once()
        assert gid == "abc123"
```

### Integration Test Example

```python
import pytest
from aria2rpc import WebSocketRPCClient

# Mark as integration test
pytestmark = pytest.mark.integration

@pytest.fixture
async def client():
    """Create connected WebSocket client."""
    client = WebSocketRPCClient("ws://localhost:6800/jsonrpc")
    await client.connect()
    yield client
    await client.close()

@pytest.mark.asyncio
async def test_get_version(client):
    """Test getting aria2 version (real RPC call)."""
    version = await client.get_version()

    assert version.version is not None
    assert isinstance(version.version, str)
    assert len(version.version) > 0
```

## Migration from Old Scripts

### Before (Shell Scripts)

```bash
# Old approach
bash scripts/setup_test_aria2.sh
bash scripts/run_websocket_tests.sh

# or
aria2c --conf-path=.test_aria2/aria2.conf &
poetry run pytest tests/aria2rpc/integration/
```

### After (Unified Python System)

```bash
# New approach - single command
mise run test

# Or for specific test types
mise run test:unit
mise run test:integration

# Direct script usage
python scripts/run_tests.py
```

### Benefits of Migration

1. **Unified Interface**: One consistent way to run all tests
2. **Better Error Handling**: Clear error messages and automatic cleanup
3. **Cross-Platform**: Works on macOS, Linux, Windows (with WSL)
4. **Easier CI Integration**: Simple commands for CI pipelines
5. **No Shell Knowledge Required**: Pure Python implementation
6. **Better Documentation**: Built-in help and examples

## Troubleshooting

### aria2c not starting

```bash
# Check if aria2c is installed
which aria2c

# Check if port 6800 is already in use
lsof -i :6800

# View aria2c logs
cat .test_aria2/aria2.log

# Manually test aria2c
aria2c --conf-path=.test_aria2/aria2.conf
```

### Tests failing with connection errors

```bash
# Ensure aria2c is running
mise run test:setup
aria2c --conf-path=.test_aria2/aria2.conf

# Check RPC is accessible
curl http://localhost:6800/jsonrpc

# Run tests without daemon management
mise run test:no-daemon
```

### Port already in use

```bash
# Kill any existing aria2c processes
pkill -f aria2c

# Or find and kill specific process
lsof -i :6800
kill <PID>

# Then run tests again
mise run test
```

### Tests hang or timeout

```bash
# Reduce timeout for faster feedback
poetry run pytest tests/ --timeout=30

# Check for zombie processes
ps aux | grep aria2c

# Clean up test directory
rm -rf .test_aria2/
mise run test:setup
```

## Best Practices

### During Development

1. **Run unit tests frequently** - They're fast and catch most issues
   ```bash
   mise run test:unit
   ```

2. **Run integration tests before commits** - Validate against real aria2c
   ```bash
   mise run test
   ```

3. **Use coverage to find gaps** - Ensure new code is tested
   ```bash
   mise run test:coverage
   ```

### Before Pull Requests

1. **Run all tests with coverage**
   ```bash
   mise run test:coverage
   ```

2. **Check that new features have both unit and integration tests**

3. **Update documentation** if test commands changed

### In CI/CD

1. **Always install aria2c** in CI environment
2. **Run unit and integration tests separately** for better visibility
3. **Upload coverage reports** to services like Codecov
4. **Cache dependencies** (poetry, mise) for faster builds

## Performance Tips

### Parallel Test Execution

```bash
# Install pytest-xdist
poetry add --group dev pytest-xdist

# Run tests in parallel
poetry run pytest -n auto

# Or with mise task
mise run test:pytest -- -n auto
```

### Fast Feedback Loop

```bash
# Run only recently changed tests
poetry run pytest --lf  # Last failed
poetry run pytest --ff  # Failed first

# Run specific test
poetry run pytest tests/aria2rpc/unit/test_http_client.py::test_add_uri -v
```

### Watch Mode (Optional)

```bash
# Install pytest-watch
poetry add --group dev pytest-watch

# Run in watch mode
poetry run ptw -- tests/ -v

# Or create mise task
# [tasks]
# "test:watch" = "poetry run ptw -- tests/ -v"
```

## Summary

The unified testing system provides:

✅ **Single entry point** - `scripts/run_tests.py` or `mise run test`
✅ **Clear separation** - Unit vs integration tests with pytest markers
✅ **Automatic management** - aria2c lifecycle handled automatically
✅ **Flexible control** - Multiple options for different workflows
✅ **Easy CI integration** - Simple commands for automation
✅ **Cross-platform** - Pure Python, works everywhere
✅ **Better documentation** - This comprehensive guide

For most cases, just use:
```bash
mise run test:unit      # During development
mise run test           # Before commits
mise run test:coverage  # Before PRs
```