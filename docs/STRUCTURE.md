# Documentation Structure

This document explains the organization of the ariatuc documentation.

## Overview

The documentation is organized to clearly separate two main components:

1. **aria2rpc** - Standalone RPC client library (95% complete)
2. **ariatuc** - TUI application built on aria2rpc (25% complete)

## Directory Structure

```
docs/
├── README.md                      # Documentation index
├── quick-start.md                 # ariatuc quick start (users)
├── installation.md                # ariatuc installation (users)
│
├── aria2rpc/                      # aria2rpc library docs
│   ├── README.md                  # Library overview
│   ├── getting-started.md         # Basic usage guide
│   ├── websocket.md               # WebSocket client guide
│   ├── bittorrent-metalink.md     # Advanced features
│   ├── testing.md                 # Testing guide
│   └── architecture.md            # Design & implementation
│
└── ariatuc/                       # ariatuc TUI docs
    ├── README.md                  # TUI overview
    ├── user-guide.md              # User guide (coming soon)
    └── development.md             # Development guide
```

## Document Categories

### User Documentation

For end users of ariatuc TUI:

- `quick-start.md` - Get started in 5 minutes
- `installation.md` - Detailed installation for all platforms
- `ariatuc/user-guide.md` - Using the TUI (coming soon)

### Library Documentation (aria2rpc)

For developers using aria2rpc as a library:

- `aria2rpc/getting-started.md` - Library usage basics
- `aria2rpc/websocket.md` - Real-time event notifications
- `aria2rpc/bittorrent-metalink.md` - Advanced download features

### Developer Documentation

For contributors to the project:

- `aria2rpc/testing.md` - Testing infrastructure
- `aria2rpc/architecture.md` - Library design
- `ariatuc/development.md` - TUI development guide

## Navigation Paths

### For Users

```
README.md
  ↓
Quick Start → Installation → User Guide
```

### For Library Users

```
README.md → aria2rpc/
  ↓
Getting Started → WebSocket Guide → Advanced Features
```

### For Contributors

```
README.md → aria2rpc/ or ariatuc/
  ↓
Testing Guide → Architecture → Development Guide
```

## Component Status

### aria2rpc (95% Complete)

Fully documented:
- ✅ Getting started guide
- ✅ WebSocket development
- ✅ BitTorrent & Metalink features
- ✅ Testing infrastructure
- ✅ Architecture overview

### ariatuc (25% Complete)

Limited documentation (TUI is early stage):
- ✅ Development guide
- 🔄 User guide (placeholder)
- 🔄 Detailed usage (waiting for TUI completion)

## Documentation Principles

1. **Separation of Concerns**
   - aria2rpc = library documentation
   - ariatuc = application documentation

2. **Progressive Disclosure**
   - Quick start for new users
   - Detailed guides for power users
   - Architecture for contributors

3. **Clear Entry Points**
   - README.md → main index
   - aria2rpc/README.md → library index
   - ariatuc/README.md → application index

4. **Cross-linking**
   - Documents link to related content
   - Library docs link to application
   - Application docs link to library

## Development Notes Location

**Important**: Development process notes are kept separate from official documentation.

- **Official Docs**: `docs/` (tracked in git)
- **Process Notes**: `notes/` (git-ignored, local only)

The `notes/` directory contains:
- Architecture analysis and decisions
- Implementation summaries
- Refactoring details
- Development progress logs

These are valuable for understanding the development process but are not part of the official documentation.

## Future Additions

As the project grows, consider adding:

- `docs/api/` - Auto-generated API reference
- `docs/tutorials/` - Step-by-step tutorials
- `docs/faq.md` - Frequently asked questions
- `docs/troubleshooting.md` - Common issues and solutions

## Maintenance

When adding new documentation:

1. Determine if it belongs to aria2rpc or ariatuc
2. Place in appropriate directory
3. Update the relevant README.md
4. Add cross-links where helpful
5. Update this STRUCTURE.md if organization changes
