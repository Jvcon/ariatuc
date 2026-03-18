# Notes Manager Agent

## Agent Purpose

This agent is responsible for managing development notes and organizing them into proper technical documentation. It should be invoked when:

1. Completing major architectural changes or milestones
2. Implementing key features that require documentation
3. Making significant refactoring decisions
4. User explicitly requests note generation

## When to Use

### Invoke this agent when:
- ✅ Completing a major milestone (e.g., P0 MVP, Service Layer, Manager Refactoring)
- ✅ Implementing critical technical architecture changes
- ✅ Making important design decisions that need to be documented
- ✅ User specifically requests: "generate notes", "document this", "create technical doc"

### Do NOT invoke for:
- ❌ Simple bug fixes (unless explicitly requested)
- ❌ Minor code changes or tweaks
- ❌ Routine maintenance tasks
- ❌ Every commit or small feature

## Note Structure Requirements

All notes created in `notes/` directory must include YAML front matter metadata:

```markdown
---
date: YYYY-MM-DD
feature: "Brief description of the feature/component"
files:
  - path/to/file1.py
  - path/to/file2.py
---

# Title

## Content

[Rest of the documentation]
```

## Workflow

### 1. Creating Notes

When a significant milestone or feature is completed:

1. Create a new markdown file in `notes/` with descriptive name
2. Include YAML front matter metadata with date, feature, and files
3. Document key technical decisions, architecture, and rationale
4. Keep notes focused on "why" not "what" (code shows "what")

### 2. Organizing Notes into Docs

After accumulating related notes or completing a phase:

1. **Identify the module**: Determine if the note relates to `aria2rpc` or `ariatuc`
   - `aria2rpc`: RPC client library, HTTP/WebSocket implementation, protocol handling
   - `ariatuc`: TUI application, UI components, service layer, managers

2. **Create proper technical documentation** in the appropriate module's `docs/` directory:
   - **aria2rpc architecture** → `docs/aria2rpc/architecture/`
   - **ariatuc architecture** → `docs/ariatuc/architecture/`
   - **ariatuc milestones** → `docs/ariatuc/milestones/`
   - **Project-wide guides** → `docs/` (root level)

3. **Delete temporary/completed notes** from `notes/`

4. **Keep long-term reference notes** (e.g., feature parity checklists)

### 3. Updating TODO.md

When completing milestones or key features:

1. Update TODO.md to mark completed items
2. Do NOT reference notes files directly in TODO.md
3. Update project status and next steps

## File Organization

### `notes/` Directory (Temporary)

Purpose: Working development notes, decisions, and progress tracking

Characteristics:
- Temporary by nature
- Can be messy and detailed
- Personal development context
- Should be cleaned up periodically

Keep in `notes/`:
- Long-term reference documents (feature checklists, API specs)
- Active development notes for ongoing work
- Design explorations and experiments

Remove from `notes/`:
- Bug fix notes (after bug is fixed)
- Session summaries (after session ends)
- Notes that have been organized into docs/
- Outdated or superseded information

### `docs/` Directory (Official)

Purpose: Official project documentation

**Important**: This project has TWO independent modules:
- `aria2rpc` - Standalone RPC client library (can be published to PyPI)
- `ariatuc` - TUI application that uses aria2rpc

Each module maintains its own documentation hierarchy.

Structure:
```
docs/
├── aria2rpc/                    # aria2rpc library documentation
│   ├── README.md                # Library overview and usage
│   ├── architecture/            # aria2rpc architecture docs
│   │   └── (aria2rpc arch docs)
│   ├── getting-started.md       # Library quick start
│   ├── architecture.md          # Architecture overview
│   ├── websocket.md             # WebSocket client guide
│   ├── bittorrent-metalink.md   # BitTorrent/Metalink support
│   └── testing.md               # Testing guide
├── ariatuc/                     # ariatuc application documentation
│   ├── README.md                # Application overview
│   ├── architecture/            # ariatuc architecture docs
│   │   ├── service-layer.md     # Service layer design
│   │   └── manager-refactoring.md  # Manager layer refactoring
│   ├── milestones/              # ariatuc milestone reports
│   │   └── p0-mvp-completion.md # P0 MVP completion
│   ├── development.md           # Development guide
│   └── user-guide.md            # User guide
├── quick-start.md               # Project-wide quick start
├── installation.md              # Installation instructions
├── README.md                    # Documentation index
└── STRUCTURE.md                 # Project structure overview
```

### Reference Policy

**Important**: Do NOT reference `notes/` files from other project files:
- ❌ Don't reference notes in TODO.md
- ❌ Don't reference notes in README.md
- ❌ Don't reference notes in docs/
- ❌ Don't reference notes in source code

## Examples

### Good Note (With Metadata)

```markdown
---
date: 2025-12-19
feature: "WebSocket RPC Client - Real-time event notifications"
files:
  - src/aria2rpc/websocket.py
  - src/aria2rpc/client.py
  - tests/aria2rpc/integration/test_websocket_client.py
---

# WebSocket Implementation

## Overview

Implemented complete WebSocket JSON-RPC client with event subscription...
```

### Bad Note (Missing Metadata)

```markdown
# Some Changes

Made some changes to the code today. Added WebSocket support.
```

## Agent Responsibilities

1. **Create notes** with proper metadata when significant work is completed
2. **Organize notes** into docs/ when appropriate
3. **Clean up** temporary notes after they're no longer needed
4. **Update TODO.md** to reflect completed milestones (without referencing notes)
5. **Maintain** clear separation between notes/ (temporary) and docs/ (official)

## Decision Guidelines

### Should I create a note?

Ask:
1. Is this a significant technical decision or architecture change?
2. Will future developers need to understand the rationale?
3. Is this a milestone worth documenting?

If yes to any → Create a note

### Should I move a note to docs/?

Ask:
1. Is this information valuable long-term?
2. Should this be part of official documentation?
3. Is the note polished and complete?

If yes to all → Move to docs/

### Should I delete a note?

Ask:
1. Has this been superseded by newer information?
2. Is this a temporary fix note for a resolved issue?
3. Has this been incorporated into official docs?

If yes to any → Delete

## Summary

The notes-manager agent maintains a healthy balance between capturing important development context and keeping official documentation clean and organized. Notes are temporary working documents that should eventually either become official docs or be discarded.

Key principles:
- Create notes for significant work only
- Include metadata in all notes
- Organize into docs/ periodically
- Clean up regularly
- Never reference notes/ from official docs