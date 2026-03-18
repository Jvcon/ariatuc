# Development Guide

This document describes the development environment setup and toolchain for ariatuc project.

## Overview

The project uses a minimal, modern Python toolchain:

- **Ruff** - Ultra-fast linter and formatter (replaces flake8, black, isort, etc.)
- **Mypy** - Static type checker
- **Pytest** - Testing framework with async support

## Quick Start

```bash
# Install dependencies (including dev tools)
poetry install

# Run all quality checks
poetry run ruff check src tests          # Linting
poetry run ruff format src tests         # Formatting
poetry run mypy src                      # Type checking
poetry run pytest                        # Testing
```

## Ruff - Linting & Formatting

**Ruff** is an extremely fast Python linter and formatter written in Rust. It replaces multiple tools:
- ✅ Flake8 (linting)
- ✅ Black (formatting)
- ✅ isort (import sorting)
- ✅ pyupgrade (Python syntax modernization)
- ✅ And 50+ more linters

### Usage

```bash
# Check for issues
poetry run ruff check src tests

# Auto-fix issues
poetry run ruff check src tests --fix

# Check formatting
poetry run ruff format --check src tests

# Apply formatting
poetry run ruff format src tests
```

### Configuration

Configured in `pyproject.toml` under `[tool.ruff]`:

- **Target**: Python 3.11+
- **Line length**: 100 characters
- **Enabled rules**:
  - E, W (pycodestyle errors/warnings)
  - F (pyflakes)
  - I (import sorting)
  - N (naming conventions)
  - UP (pyupgrade - modern syntax)
  - B (bugbear - common bugs)
  - C4 (comprehensions)
  - SIM (simplify)
  - RET (return statements)
  - ARG (unused arguments)
  - PTH (pathlib)
  - ASYNC (async patterns)

See `pyproject.toml` for detailed configuration and ignored rules.

## Mypy - Type Checking

**Mypy** performs static type analysis to catch type errors before runtime.

### Usage

```bash
# Type check source code
poetry run mypy src

# Type check with error codes
poetry run mypy src --show-error-codes

# Type check specific file
poetry run mypy src/ariatuc/core/service.py
```

### Configuration

Configured in `pyproject.toml` under `[tool.mypy]`:

- **Mode**: Balanced strictness (allows gradual typing)
- **Target**: Python 3.11
- **Packages**: aria2rpc, ariatuc
- **Incremental**: Enabled (faster subsequent runs)

The configuration is intentionally relaxed to allow:
- Incremental typing (not all functions need type hints)
- Practical dictionary/list usage
- Textual framework decorators

## Pytest - Testing

**Pytest** is the testing framework with async support via pytest-asyncio.

### Usage

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/aria2rpc/unit/test_http_client.py

# Run with coverage
poetry run pytest --cov=ariatuc --cov-report=html

# Run only unit tests (fast)
poetry run pytest -m unit

# Run only integration tests (requires aria2c)
poetry run pytest -m integration

# Verbose output
poetry run pytest -v
```

### Test Categories

Tests are marked with categories:
- `@pytest.mark.unit` - Fast unit tests, no external dependencies
- `@pytest.mark.integration` - Integration tests, require running aria2c
- `@pytest.mark.asyncio` - Async tests (auto-detected with pytest-asyncio)

### Configuration

Configured in `pyproject.toml` under `[tool.pytest.ini_options]`:

- **Test paths**: `tests/`
- **Python path**: `src/` (for imports)
- **Async mode**: Auto (pytest-asyncio)

## Pre-Commit Workflow

Recommended workflow before committing:

```bash
# 1. Format code
poetry run ruff format src tests

# 2. Fix linting issues
poetry run ruff check src tests --fix

# 3. Check remaining issues
poetry run ruff check src tests

# 4. Type check
poetry run mypy src

# 5. Run tests
poetry run pytest

# 6. Commit if all checks pass
git add .
git commit -m "Your commit message"
```

## IDE Integration

### VS Code

Install these extensions:
- **Ruff** (charliermarsh.ruff) - Auto-linting and formatting
- **Pylance** (ms-python.vscode-pylance) - Type checking
- **Python** (ms-python.python) - Base Python support

Add to `.vscode/settings.json`:

```json
{
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": "explicit",
      "source.organizeImports": "explicit"
    },
    "editor.defaultFormatter": "charliermarsh.ruff"
  },
  "ruff.lint.enable": true,
  "ruff.format.enable": true,
  "python.languageServer": "Pylance",
  "python.analysis.typeCheckingMode": "basic"
}
```

### PyCharm

1. **Ruff Plugin**: Install from marketplace
2. **Mypy Plugin**: Install from marketplace
3. Configure file watchers for auto-formatting

## Dependency Management

All development dependencies are in `pyproject.toml`:

```toml
[dependency-groups]
dev = [
    "pytest>=9.0.2,<10.0.0",           # Test framework
    "pytest-asyncio>=1.3.0,<2.0.0",    # Async test support
    "pytest-mock>=3.12.0",              # Mocking
    "pytest-cov>=4.1.0",                # Coverage reporting
    "ruff>=0.14.11,<0.15.0",            # Linter + formatter
    "mypy>=1.19.1,<2.0.0",              # Type checker
]
```

### Adding/Updating Dependencies

```bash
# Add development dependency
poetry add --group dev <package>

# Update all dependencies
poetry update

# Update specific dependency
poetry update ruff

# Show outdated packages
poetry show --outdated
```

## Troubleshooting

### Ruff Issues

**Q: Ruff is too strict on certain rules**

A: Add the rule to `ignore` list in `pyproject.toml`:

```toml
[tool.ruff.lint]
ignore = [
    "E501",  # Line too long
    # Add your rule here
]
```

**Q: Need to ignore a rule in specific files**

A: Use per-file-ignores:

```toml
[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["ARG", "F401"]
```

### Mypy Issues

**Q: Mypy complains about missing type stubs**

A: Add the module to overrides:

```toml
[[tool.mypy.overrides]]
module = ["some_module.*"]
ignore_missing_imports = true
```

**Q: Too many type errors in legacy code**

A: Mypy configuration is already relaxed for gradual adoption. For specific files, add:

```python
# type: ignore  # At end of line
# mypy: ignore-errors  # At top of file
```

### Test Issues

**Q: Tests are slow**

A: Run only unit tests:

```bash
poetry run pytest -m unit
```

**Q: Integration tests fail**

A: Ensure aria2c is running:

```bash
aria2c --enable-rpc --rpc-listen-all=false --rpc-listen-port=6800
```

## Performance

Tool performance (on medium-sized codebase):

- **Ruff check**: ~50ms ⚡
- **Ruff format**: ~100ms ⚡
- **Mypy**: ~2-5s (incremental) 🚀
- **Pytest (unit)**: ~1-3s 🚀
- **Pytest (all)**: ~10-30s (depends on integration tests)

## Best Practices

1. **Run ruff format regularly** - Keep consistent formatting
2. **Fix ruff check issues** - Don't accumulate technical debt
3. **Add type hints incrementally** - Focus on public APIs first
4. **Write tests for new features** - Aim for good coverage
5. **Use markers for tests** - Separate unit from integration tests
6. **Keep dependencies updated** - Run `poetry update` monthly

## References

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Mypy Documentation](https://mypy.readthedocs.io/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Poetry Documentation](https://python-poetry.org/docs/)
