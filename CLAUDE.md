# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ariatuc** is a Terminal User Interface (TUI) application for managing aria2c download manager, built with Python and Textual. The project aims to provide a feature-rich, keyboard-driven interface inspired by lazygit's UX principles, covering functionality equivalent to the AriaNg web frontend.

## ⚠️ MANDATORY DEVELOPMENT WORKFLOW ⚠️

**CRITICAL**: This project enforces a strict quality-first development workflow. **You MUST follow this exact order:**

```text
1. Write Code
2. Run Ruff (linting + formatting)  ← MANDATORY
3. Run Mypy (type checking)         ← MANDATORY
4. Fix ALL issues from steps 2-3    ← MANDATORY
5. Run Tests                        ← ONLY after steps 2-4 are clean
6. Verify with IDE diagnostics
```

**Quick command pipeline:**

```bash
poetry run ruff check --fix src/ tests/ && \
poetry run ruff format src/ tests/ && \
poetry run mypy src/ && \
poetry run pytest
```

**Zero-tolerance policy:**

- ❌ Running tests BEFORE Ruff/Mypy pass = Workflow violation
- ❌ Committing code with ANY Ruff/Mypy issues = Not allowed
- ❌ Skipping code quality checks = Task incomplete

See [Code Quality and Diagnostics](#code-quality-and-diagnostics) section for detailed requirements.

## Project Structure

```shell
ariatuc/
├── .git/                    # Git version control
├── .gitignore               # Git ignore configuration
├── mise.toml                # Mise environment config (Python version lock)
├── pyproject.toml           # Poetry config (metadata, dependencies, scripts)
├── README.md                # Project documentation
├── src/                     # Core source code root
│   ├── aria2rpc/            # Aria2 RPC client library (future standalone package)
│   │   ├── __init__.py      # Package exports
│   │   ├── client.py        # Unified client interface
│   │   ├── http.py          # HTTP JSON-RPC implementation
│   │   ├── websocket.py     # WebSocket JSON-RPC (TODO)
│   │   ├── models.py        # Data models (DownloadStatus, GlobalStat, etc.)
│   │   └── exceptions.py    # Exception definitions
│   └── ariatuc/             # TUI application package
│       ├── __init__.py      # Package initialization
│       ├── main.py          # TUI application entry point
│       ├── ui/              # UI components and widgets
│       │   ├── __init__.py
│       │   ├── app.py       # Main Textual App class
│       │   ├── screens/     # Different screen views
│       │   └── widgets/     # Reusable UI widgets
│       ├── core/            # Core business logic
│       │   ├── __init__.py
│       │   ├── service.py  # Service
│       │   ├── event_manager.py  # Event management
│       │   ├── download_manager.py  # Download state management
│       │   ├── rpc_manager.py       # Multiple RPC server management
│       │   └── config_manager.py            # Configuration management
│       └── utils/           # Utility functions
├── scripts/                 # Build and utility scripts
└── tests/                   # Test code directory
    ├── __init__.py
    ├── aria2rpc/            # Tests for aria2rpc package
    │   ├── unit/            # Unit tests (fast, no aria2c needed)
    │   │   └── test_http_client.py
    │   └── integration/     # Integration tests (requires aria2c)
    │       ├── test_websocket_client.py
    │       └── test_websocket_complete.py
    └── ariatuc/             # Tests for ariatuc application
        ├── unit/            # Unit tests
        │   └── test_download_manager.py
        └── ui/              # UI tests
```

**Note**:

- The `aria2rpc` package is designed as a standalone library that can eventually be extracted and published to PyPI
- The `src/ariatuc/` code structure is flexible and should evolve with architectural needs
- `ariatuc` imports from `aria2rpc` as if it's an external package

## Development Setup

This project uses **Poetry** for dependency management and **mise** for tool version management.

### Prerequisites

- Python 3.11+ (configured for Python 3.14 in mise.toml)
- Poetry (managed via mise)
- Virtual environment at `.venv/` (auto-created by mise)
- Running aria2c instance with RPC enabled

### Environment Setup

```bash
# Install dependencies
poetry install

# Install with development dependencies
poetry install --with dev

# Run the application
poetry run python -m ariatuc
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run specific test file (HTTP client unit tests)
poetry run pytest tests/aria2rpc/unit/test_http_client.py

# Run specific test file (WebSocket integration tests)
poetry run pytest tests/aria2rpc/integration/test_websocket_client.py

# Run with verbose output and coverage
poetry run pytest -v --cov=ariatuc

# Run only async tests
poetry run pytest -m asyncio
```

## Core Architecture

### 1. aria2rpc Package - RPC Client Library

The `aria2rpc` package is a standalone Python client library for aria2's RPC interface. It is designed to be eventually extracted as an independent PyPI package (similar to `transmission-rpc`).

**Package Location**: `src/aria2rpc/`

**Design Philosophy**:

- Standalone library that can be used by any aria2-based application
- Type-safe with modern Python features (async/await, type hints)
- Comprehensive error handling with custom exception classes
- Clean separation between protocol implementations (HTTP, WebSocket)

The foundation of this project is the aria2 RPC interface. The client must support:

#### RPC Protocol Support

- **JSON-RPC over HTTP** (primary): Standard JSON-RPC 2.0 protocol
- **JSON-RPC over WebSocket**: For real-time notifications and events
- **XML-RPC**: Legacy support if needed

#### Authentication

- **Token-based auth** using `--rpc-secret` (recommended)
- Support for deprecated `--rpc-user` and `--rpc-passwd` for compatibility

#### Essential RPC Methods

**Download Control:**

- `aria2.addUri(uris, [options], [position])` - Add HTTP/FTP downloads
- `aria2.addTorrent(torrent, [uris], [options], [position])` - Add torrent downloads
- `aria2.addMetalink(metalink, [options], [position])` - Add metalink downloads
- `aria2.remove(gid)` - Remove download
- `aria2.forceRemove(gid)` - Force remove download
- `aria2.pause(gid)` / `aria2.pauseAll()` - Pause downloads
- `aria2.unpause(gid)` / `aria2.unpauseAll()` - Resume downloads

**Status & Information:**

- `aria2.tellStatus(gid, [keys])` - Get download status
- `aria2.tellActive([keys])` - Get active downloads
- `aria2.tellWaiting(offset, num, [keys])` - Get waiting downloads
- `aria2.tellStopped(offset, num, [keys])` - Get stopped downloads
- `aria2.getUris(gid)` - Get URIs for download
- `aria2.getFiles(gid)` - Get file list in download
- `aria2.getPeers(gid)` - Get peer information (BitTorrent)
- `aria2.getServers(gid)` - Get server information
- `aria2.getGlobalStat()` - Get global statistics
- `aria2.getVersion()` - Get aria2 version
- `aria2.getSessionInfo()` - Get session info

**Configuration:**

- `aria2.getOption(gid)` - Get download options
- `aria2.changeOption(gid, options)` - Change download options
- `aria2.getGlobalOption()` - Get global options
- `aria2.changeGlobalOption(options)` - Change global options

**Utility:**

- `aria2.changePosition(gid, pos, how)` - Change download position in queue
- `aria2.changeUri(gid, fileIndex, delUris, addUris, [position])` - Change URIs
- `aria2.purgeDownloadResult()` - Purge completed/removed downloads
- `aria2.removeDownloadResult(gid)` - Remove download result
- `aria2.saveSession()` - Save session
- `aria2.shutdown()` / `aria2.forceShutdown()` - Shutdown aria2
- `system.multicall(methods)` - Batch multiple method calls
- `system.listMethods()` - List all available methods

#### WebSocket Notifications

Support real-time event notifications:

- `onDownloadStart` - Download started
- `onDownloadPause` - Download paused
- `onDownloadStop` - Download stopped
- `onDownloadComplete` - Download completed
- `onDownloadError` - Download error
- `onBtDownloadComplete` - BitTorrent download completed

### 2. Multiple RPC Server Management (`rpc_manager.py`)

The application should support managing multiple aria2 RPC servers:

- Add/remove/edit server configurations
- Switch between different servers
- Display server connection status
- Save server configurations persistently
- Handle authentication per server

### 3. Feature Parity with AriaNg

The TUI should aim to provide equivalent functionality to AriaNg web frontend:

**Download Management:**

- Add downloads from URLs, torrents, and metalink files
- Pause/resume/remove downloads (individual and batch operations)
- View detailed download information (status, speed, connections, files)
- Manage download queue and priorities
- BitTorrent-specific features (peer info, tracker management)

**Configuration:**

- Global settings configuration
- Per-download options
- Connection settings (max connections, timeout, etc.)
- BitTorrent settings (DHT, peer exchange, encryption)
- Directory and file allocation settings

**Monitoring & Statistics:**

- Real-time download speeds (download/upload)
- Global statistics (active/waiting/stopped downloads)
- Per-file progress in multi-file downloads
- Connection and server status

**Advanced Features:**

- Session management (save/restore)
- Download result history
- File selection in torrents
- URI management for downloads

### 4. TUI Design Inspired by lazygit

The UI should follow lazygit's successful interaction paradigms:

#### Panel-Based Layout

- **Main panels**: Downloads (active/waiting/stopped), Details, Servers
- **Context switching**: Use `1-5` number keys or `Tab` to switch between panels
- **Full-screen modes**: Expand panels to full screen with dedicated keys

#### Keyboard-Driven Navigation

- **Vim-style navigation**: `j`/`k` or arrow keys for list navigation
- **Panel switching**: `h`/`l` or `Tab`/`Shift+Tab` to move between panels
- **Quick actions**: Single-key commands for common operations
  - `a` - Add new download
  - `d` - Delete/remove download
  - `p` - Pause/unpause download
  - `e` - Edit download options
  - `r` - Refresh/reload
  - `s` - Switch server
  - `g` - Global settings
  - `?` - Show keybindings help
  - `q` - Quit application
  - `Enter` - View details/expand item

#### Context-Sensitive UI

- Different key bindings based on current context (panel and selection)
- Status bar showing available actions for current context
- Modal dialogs for complex operations (add download, settings)

#### Real-Time Updates

- Use WebSocket notifications for instant status updates
- Reactive UI that reflects download progress without manual refresh
- Visual indicators for download state (active, paused, error, completed)

#### Visual Design

- Use Textual's rich rendering for progress bars and stats
- Color coding for different download states
- Table/list views with sortable columns
- Compact information density while maintaining readability

## Development Notes

### Async Programming

This is an **async-first** application:

- All RPC calls are asynchronous
- Textual framework is built on asyncio
- WebSocket connections require async handling
- Use `async def` and `await` throughout

### Testing Strategy

```python
# Testing RPC client
@pytest.mark.asyncio
async def test_add_download():
    client = Aria2Client("http://localhost:6800/jsonrpc")
    gid = await client.add_uri(["http://example.com/file.zip"])
    assert gid is not None

# Testing Textual UI
@pytest.mark.asyncio
async def test_download_list_widget():
    app = AriatucApp()
    async with app.run_test() as pilot:
        # Simulate user interactions
        await pilot.press("a")  # Add download
        assert app.screen.query_one("#add-dialog").visible
```

### Code Quality and Diagnostics

**CRITICAL**: All files (Python, Markdown, etc.) must pass diagnostics before a task can be considered complete. This requirement applies to:

- **Main development work** - All coding and documentation tasks
- **Sub-agents** - doc-manager, notes-manager, prj-manager, and all other agents
- **All file types** - Python source code, test files, Markdown documentation, etc.

#### Task Completion Definition

A task is **NOT complete** until ALL of the following conditions are met:

1. ✅ **Functionality Implemented** - Feature works as expected
2. ✅ **Code Quality Checks Pass** - ALL Poetry tool checks clean (Ruff + Mypy) - **MUST run BEFORE testing**
3. ✅ **Tests Pass** - All test cases run successfully (for code changes)
4. ✅ **Diagnostics Clean** - ALL diagnostics resolved for ALL modified files
5. ✅ **Compilation/Validation Success** - All files are valid (Python compiles, Markdown validates, etc.)

**Important**: The workflow order is MANDATORY:

```text
Code Implementation → Poetry Tools (Ruff + Mypy) → Fix All Issues → Run Tests → IDE Diagnostics → Complete
```

**You MUST NOT run tests until all Poetry tool checks pass.** Implementing functionality is **necessary but not sufficient**.

#### Diagnostic Workflow by File Type

##### Python Files (.py)

After creating or modifying Python scripts in a task, follow this **MANDATORY** workflow. **DO NOT skip steps or change the order.**

###### Step 1: Run Ruff Linting and Formatting (MANDATORY - BEFORE testing)

**Critical**: This step MUST be completed before running any tests.

```bash
# 1.1 Run Ruff linter to check for code quality issues
poetry run ruff check src/ tests/

# 1.2 Auto-fix issues that Ruff can handle automatically
poetry run ruff check --fix src/ tests/

# 1.3 Run Ruff formatter to ensure consistent code style
poetry run ruff format src/ tests/
```

**What Ruff checks:**

- Code style (PEP 8)
- Import sorting and organization
- Unused imports, variables, arguments
- Code complexity and simplification opportunities
- Common bug patterns
- Modern Python idioms (pyupgrade)

###### Step 2: Run Mypy Type Checking (MANDATORY - BEFORE testing)

**Critical**: This step MUST be completed before running any tests.

```bash
# Run static type checking on source code
poetry run mypy src/ariatuc/ src/aria2rpc/

# For comprehensive check including tests
poetry run mypy src/ tests/
```

**What Mypy checks:**

- Type annotations correctness
- Type compatibility in assignments and function calls
- Return type consistency
- Optional/None handling
- Generic type usage

**Common Mypy issues to fix:**

- Missing return type annotations
- Incorrect type hints
- Using `Any` unnecessarily
- Missing `Optional[]` for nullable values

###### Step 3: Verify Compilation

```bash
# Compile check all modified Python files
poetry run python -m py_compile src/path/to/modified_file.py
poetry run python -m py_compile tests/path/to/test_file.py
```

###### Step 4: Run Tests (ONLY AFTER Steps 1-3 are clean)

**DO NOT run tests until all Ruff and Mypy issues are fixed.**

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/path/to/test_file.py

# Run with coverage
poetry run pytest --cov=ariatuc --cov=aria2rpc
```

###### Step 5: Run IDE Diagnostics

```bash
# Final check for any remaining diagnostics
# Use mcp__ide__getDiagnostics tool
```

###### Step 6: Re-verify All Tools

```bash
# Verify all issues are resolved
poetry run ruff check src/ tests/
poetry run mypy src/
# Re-check with mcp__ide__getDiagnostics tool
```

###### Common Python Diagnostic Issues and Fixes

**Unused Imports:**

```python
# ❌ Bad - unused import
import sys
from typing import Optional  # Not used anywhere
from pathlib import Path      # Not used anywhere

# ✅ Good - remove unused imports
import sys
```

**Unused Variables:**

```python
# ❌ Bad - variable assigned but never used
result = calculate_something()
print("Done")

# ✅ Good - use the variable or remove it
result = calculate_something()
print(f"Result: {result}")

# ✅ Good - if intentionally unused, use underscore
_ = calculate_something()  # Side effect only
print("Done")
```

**Unused Loop Variables:**

```python
# ❌ Bad - loop variable not used
for i in range(10):
    print("hello")

# ✅ Good - use underscore for intentionally unused variables
for _ in range(10):
    print("hello")
```

**Unused Function Parameters:**

```python
# ❌ Bad - parameter defined but not used
def handler(event, context):
    return {"status": "ok"}

# ✅ Good - use underscore prefix for unused parameters
def handler(_event, _context):
    return {"status": "ok"}

# ✅ Better - remove if truly not needed
def handler():
    return {"status": "ok"}
```

**Type Errors in Tests:**

```python
# ❌ Bad - assigning to unknown attribute
service._test_mock_client = mock_client

# ✅ Good - use proper mocking
with patch.object(service, 'rpc_mgr') as mock_rpc:
    mock_rpc.get_client.return_value = mock_client
```

###### Python Diagnostic Tools Summary

**MANDATORY Tools (MUST run in this order BEFORE testing):**

```bash
# 1. Ruff linting and formatting (MANDATORY)
poetry run ruff check src/ tests/           # Check for issues
poetry run ruff check --fix src/ tests/     # Auto-fix issues
poetry run ruff format src/ tests/          # Format code

# 2. Mypy type checking (MANDATORY)
poetry run mypy src/ariatuc/ src/aria2rpc/  # Check types

# 3. Python compilation check (MANDATORY)
poetry run python -m py_compile src/path/to/file.py

# 4. Run tests (ONLY AFTER 1-3 are clean)
poetry run pytest

# 5. IDE diagnostics (Final verification)
# Use mcp__ide__getDiagnostics tool in Claude Code
```

**Quick Command for Full Check:**

```bash
# Run all quality checks in sequence (use this for verification)
poetry run ruff check --fix src/ tests/ && \
poetry run ruff format src/ tests/ && \
poetry run mypy src/ && \
poetry run pytest
```

**Important Notes:**

- Ruff and Mypy are **NOT optional** - they are required for all code changes
- Tests MUST NOT be run until Ruff and Mypy pass completely
- All auto-fixable issues MUST be fixed before manual review
- Zero tolerance for linting/type errors in committed code

##### Markdown Files (.md)

After creating or modifying Markdown files in a task, follow this mandatory workflow:

###### Step 1: Run IDE Diagnostics (Markdown)

```bash
# Check for all diagnostics in modified Markdown files
# Use mcp__ide__getDiagnostics tool
```

###### Step 2: Fix ALL Issues in Priority Order (Markdown)

Must fix in order of severity:

1. **Errors (Severity: Error)** - MUST fix all (blocking)
   - Invalid syntax
   - Broken links
   - Malformed tables
   - Invalid HTML/code blocks

2. **Warnings (Severity: Warning)** - MUST fix all (required)
   - Inconsistent heading levels
   - Missing blank lines around elements
   - Inconsistent list markers
   - Line length issues

3. **Hints (Severity: Hint)** - MUST fix all (required)
   - Trailing whitespace
   - Multiple consecutive blank lines
   - Inconsistent emphasis markers
   - Other style inconsistencies

###### Step 3: Re-run Diagnostics

```bash
# Verify all issues are resolved
# Re-check with mcp__ide__getDiagnostics tool
```

###### Common Markdown Diagnostic Issues and Fixes

**MD032 - Lists should be surrounded by blank lines:**

```markdown
❌ Bad - no blank line before list
Some text:
- List item 1
- List item 2

✅ Good - blank line before list
Some text:

- List item 1
- List item 2
```

**MD031 - Fenced code blocks should be surrounded by blank lines:**

Incorrect: Code block immediately after text without blank line

Correct: Always add a blank line before and after code blocks

**MD036 - Emphasis used instead of a heading:**

```markdown
❌ Bad - using bold for heading
**Section Title**

Some content here.

✅ Good - use proper heading
#### Section Title

Some content here.
```

**MD001 - Heading levels should increment by one:**

```markdown
❌ Bad - skipping heading levels
## Level 2
#### Level 4 (skipped 3)

✅ Good - proper heading sequence
## Level 2
### Level 3
#### Level 4
```

###### Markdown Diagnostic Tools

```bash
# IDE diagnostics (comprehensive - use this!)
# mcp__ide__getDiagnostics tool in Claude Code

# Standalone markdownlint (if installed)
markdownlint **/*.md
```

#### Task Completion Checklist

Before marking ANY task as complete, verify **in this exact order**:

**Phase 1: Implementation**

- [ ] All functionality implemented

**Phase 2: Poetry Tool Checks (MANDATORY - BEFORE testing)**

- [ ] **Ruff linting passed** - `poetry run ruff check src/ tests/` shows 0 issues
- [ ] **Ruff auto-fix applied** - `poetry run ruff check --fix src/ tests/` completed
- [ ] **Ruff formatting applied** - `poetry run ruff format src/ tests/` completed
- [ ] **Mypy type checking passed** - `poetry run mypy src/` shows 0 errors
- [ ] **Python files compile** - `poetry run python -m py_compile` succeeds for all modified files

**Phase 3: Testing (ONLY after Phase 2 is complete)**

- [ ] **All test cases pass** - `poetry run pytest` completes successfully
- [ ] **Test coverage acceptable** (if required)

**Phase 4: Final Verification**

- [ ] **IDE diagnostics run** on ALL modified files (Python, Markdown, etc.)
- [ ] **ALL Error diagnostics fixed** (0 errors) in ALL file types
- [ ] **ALL Warning diagnostics fixed** (0 warnings) in ALL file types
- [ ] **ALL Hint diagnostics fixed** (0 hints) in ALL file types
- [ ] **Markdown files pass validation** (if modified)
- [ ] **Re-ran all checks** to confirm clean state

**Critical Rule**: If ANY check in Phase 2 fails, you MUST fix it before proceeding to Phase 3.

#### Enforcement Policy

**Task Status Rules:**

- ❌ **INCOMPLETE**: Ruff linting shows ANY issues
- ❌ **INCOMPLETE**: Ruff formatting not applied
- ❌ **INCOMPLETE**: Mypy type checking shows ANY errors
- ❌ **INCOMPLETE**: Any Python files don't compile
- ❌ **INCOMPLETE**: Tests run BEFORE Poetry tools pass (workflow violation)
- ❌ **INCOMPLETE**: Tests fail (for code changes)
- ❌ **INCOMPLETE**: Any IDE diagnostics remain (Error/Warning/Hint) in ANY file
- ❌ **INCOMPLETE**: Any Markdown files have validation errors
- ✅ **COMPLETE**: All above conditions satisfied in the correct order

**Scope of Application:**

This enforcement policy applies to:

- **Main agent**: All development and documentation work
- **doc-manager**: All documentation updates and organization tasks
- **notes-manager**: All note creation and organization tasks
- **prj-manager**: All backlog and task management updates
- **All other sub-agents**: Any file modifications they perform

**Note**: If you (or any sub-agent) report a task as "complete" but diagnostics show issues, the task will be considered incomplete and must be continued until all diagnostics are resolved.

### Error Handling

- Handle RPC connection failures gracefully
- Display user-friendly error messages in TUI
- Implement reconnection logic for WebSocket
- Validate user input in forms and dialogs

### Configuration Management

Support persistent configuration:

- Server list with credentials
- UI preferences (keybindings, theme)
- Default download options
- Store in `~/.config/ariatuc/` or similar

## Poetry Commands

### Development Workflow Commands

**MANDATORY: Run these commands in order before running tests**

```bash
# Code Quality Checks (MANDATORY before testing)
poetry run ruff check src/ tests/           # Lint code
poetry run ruff check --fix src/ tests/     # Auto-fix issues
poetry run ruff format src/ tests/          # Format code
poetry run mypy src/                        # Type check

# Testing (ONLY after quality checks pass)
poetry run pytest                           # Run all tests
poetry run pytest tests/path/to/test.py     # Run specific test
poetry run pytest --cov=ariatuc             # Run with coverage

# Full quality check pipeline
poetry run ruff check --fix src/ tests/ && \
poetry run ruff format src/ tests/ && \
poetry run mypy src/ && \
poetry run pytest
```

### Package Management Commands

```bash
# Add dependency
poetry add httpx websockets

# Add dev dependency
poetry add --group dev pytest-mock

# Update dependencies
poetry update

# Show dependency tree
poetry show --tree

# Build package
poetry build
```

### Application Commands

```bash
# Run application
poetry run python -m ariatuc

# Run with debug logging
poetry run python -m ariatuc --debug
```

## Key Dependencies

### Main Dependencies

- `textual` (>=6.10.0): TUI framework
- `httpx`: Async HTTP client for JSON-RPC
- `websockets`: WebSocket support for notifications
- `pydantic`: Data validation and settings management

### Dev Dependencies

**Code Quality Tools (MANDATORY):**

- `ruff` (>=0.14.11): Modern Python linter and formatter (REQUIRED)
- `mypy` (>=1.19.1): Static type checker (REQUIRED)

**Testing Tools:**

- `pytest` (>=9.0.2): Testing framework
- `pytest-asyncio` (>=1.3.0): Async test support
- `pytest-mock` (>=3.12.0): Mocking support for tests
- `pytest-cov` (>=4.1.0): Test coverage reporting

## Architecture Evolution

The codebase structure is designed to be flexible. As the project develops:

- Refactor shared functionality into appropriate modules
- Split large files when they exceed ~500 lines
- Extract reusable widgets into `ui/widgets/`
- Create separate screens for distinct views in `ui/screens/`
- Consider plugins/extensions system for advanced features

## Task Management with Backlog.md

This project uses **Backlog.md** for task and project management. Backlog.md is a markdown-native task management system that stores all project data as plain `.md` files in the repository.

### Overview

- **Task Storage**: Tasks are stored in `backlog/tasks/` as markdown files
- **File Naming**: `task-<id> - <title>.md` (e.g., `task-1 - P0-MVP-Testing-Polish.md`)
- **Completed Tasks**: Moved to `backlog/completed/` directory
- **Configuration**: `backlog/config.yml` contains project settings

### Task Structure

Each task file contains YAML frontmatter with metadata:

```markdown
---
status: "To Do"  # "To Do", "In Progress", "Blocked", "Done"
priority: high   # high, medium, low
labels:
  - ui
  - test
  - p0
assignee:
dependencies:
parent:
---

# Task Title

## Description
Detailed description of the task

## Acceptance Criteria
- [ ] First criterion
- [ ] Second criterion
- [ ] Third criterion
```

### Key Backlog CLI Commands

**Viewing Tasks:**

- `backlog board` - Display Kanban board with all tasks
- `backlog task list` - List tasks grouped by status
- `backlog task view <taskId>` - Show detailed task information
- `backlog overview` - Show project statistics

**Managing Tasks:**

- `backlog task create "Title" --status "To Do" --priority high --labels ui,test --ac "Criterion"` - Create new task
- `backlog task edit <taskId> --status "In Progress"` - Update task status
- `backlog task edit <taskId> --priority medium` - Change priority
- `backlog search <query>` - Search across all tasks
- `backlog cleanup` - Archive completed tasks to `backlog/completed/`

### Task Granularity Guidelines

**IMPORTANT**: Avoid creating excessive task files. Use appropriate granularity:

✅ **DO:**

- Create consolidated tasks that represent meaningful work units
- Use acceptance criteria to break down tasks internally
- Group related subtasks under a single task
- Aim for tasks completable in a few hours to a few days

❌ **DON'T:**

- Create separate task files for every small subtask
- Over-fragment work into dozens of tiny tasks
- Duplicate information across multiple related tasks

**Example**: Instead of creating 6 separate tasks for testing (test UI, test download, test pause, etc.), create one "P0 MVP Testing & Polish" task with 6 acceptance criteria.

### Labels System

Consistent labels for filtering and organization:

**Component Labels:**

- `aria2rpc` - RPC client library
- `ariatuc` - TUI application
- `ui` - User interface
- `service` - Service layer
- `manager` - Manager classes
- `test` - Testing tasks
- `docs` - Documentation
- `infra` - Infrastructure/CI/CD

**Priority Labels:**

- `p0` - MVP features (Phase 0)
- `p1` - Core features (Phase 1)
- `p2` - Advanced features (Phase 2)
- `p3` - Extended features (Phase 3)

### Integration with prj-manager Agent

The `prj-manager` agent (`.claude/agents/prj-manager.md`) is specialized for managing project tasks using Backlog.md:

- Automatically invoked for task management requests
- Creates and updates tasks using backlog CLI
- Provides daily planning and progress tracking
- Maintains appropriate task granularity
- Ensures consistent labeling and prioritization

Use the prj-manager agent when you need to:

- Add new requirements or track issues
- Update progress on completed work
- Plan daily work sessions
- Review project status

### Migration from TODO.md

This project previously used `TODO.md` (todo.txt format). Tasks have been migrated to Backlog.md:

- High-priority and in-progress tasks → Active backlog tasks
- Completed tasks → Available as reference in old TODO.md
- New development → Use Backlog.md exclusively

**Note**: `TODO.md` is retained for historical reference but is no longer actively maintained.

## Notes and Documentation Workflow

### When to Create Notes

Create development notes in `notes/` directory **only** when:

1. **Major architectural changes**: Significant refactoring or new architectural patterns
2. **Milestone completions**: P0/P1/P2 phase completions, major feature releases
3. **Key feature implementations**: Core functionality that requires detailed documentation
4. **Important design decisions**: Choices that affect future development
5. **Explicitly requested**: User specifically asks for note generation

**Do NOT create notes for**:

- Simple bug fixes (unless explicitly requested)
- Minor code changes or routine maintenance
- Every commit or small feature addition

### Note Structure Requirements

All notes must include YAML front matter metadata at the top:

```markdown
---
date: YYYY-MM-DD
feature: "Brief description of the feature/component"
files:
  - path/to/file1.py
  - path/to/file2.py
  - path/to/file3.py
---

# Title

## Content

[Rest of the documentation]
```

### File Organization

**`notes/` Directory** (Temporary development notes):

- Working notes and decisions
- Active development context
- Design explorations
- Should be cleaned up periodically
- Keep only long-term reference documents (e.g., feature checklists)

**`docs/` Directory** (Official documentation):

This project has TWO independent modules:

- `aria2rpc` - Standalone RPC client library (can be published to PyPI)
- `ariatuc` - TUI application that uses aria2rpc

Each module maintains its own documentation:

- `docs/aria2rpc/` - aria2rpc library documentation and architecture
- `docs/ariatuc/` - ariatuc application documentation and architecture
  - `docs/ariatuc/architecture/` - Technical architecture documents
  - `docs/ariatuc/milestones/` - Milestone completion reports
- `docs/` (root) - Project-wide guides (quick-start, installation, etc.)

### Reference Policy

**IMPORTANT**: Do NOT reference `notes/` files from other project locations:

- ❌ Don't reference notes in backlog tasks
- ❌ Don't reference notes in `README.md`
- ❌ Don't reference notes in `docs/`
- ❌ Don't reference notes in source code comments

### Organizing Notes into Documentation

Periodically review `notes/` and:

1. **Identify the module**: Determine if the note relates to `aria2rpc` or `ariatuc`
   - `aria2rpc`: RPC client library, HTTP/WebSocket implementation, protocol handling
   - `ariatuc`: TUI application, UI components, service layer, managers

2. **Extract key information** into proper technical documentation in the appropriate module's `docs/` directory:
   - aria2rpc architecture → `docs/aria2rpc/architecture/`
   - ariatuc architecture → `docs/ariatuc/architecture/`
   - ariatuc milestones → `docs/ariatuc/milestones/`
   - Project-wide guides → `docs/` (root level)

3. **Delete temporary notes** after they're incorporated or no longer relevant

4. **Keep long-term references** (like feature parity checklists)

5. **Update backlog tasks** to reflect completed milestones (without referencing notes)

### Notes Manager Subagent

A specialized subagent is available for managing notes workflow:

- Located at `.claude/agents/notes-manager.md`
- Use when organizing notes or creating milestone documentation
- Handles metadata, organization, and cleanup

## Resources

- Aria2 RPC Documentation: <https://aria2.github.io/manual/en/html/aria2c.html#rpc-interface>
- Textual Documentation: <https://textual.textualize.io/>
- AriaNg (feature reference): Web-based aria2 frontend
- lazygit (UX reference): Terminal UI for git
