"""Tests for aria2 option value parsing and formatting.

Covers the conversion between aria2's wire format (everything is a string) and
Python native values (``int``, ``bool``). These helpers are used by
``get_option`` / ``get_global_option`` (parse) and ``change_option`` /
``change_global_option`` (format).
"""

import pytest

from aria2rpc.option_types import (
    BOOLEAN_OPTIONS,
    INTEGER_OPTIONS,
    format_option_value,
    format_options_dict,
    parse_option_value,
    parse_options_dict,
)

# -----------------------------------------------------------------------------
# parse_option_value
# -----------------------------------------------------------------------------


def test_parse_option_value_none_returns_none() -> None:
    """None and empty string map to None."""
    assert parse_option_value("dir", None) is None
    assert parse_option_value("dir", "") is None


def test_parse_option_value_boolean_known_keys() -> None:
    """Boolean-typed options are converted to bool regardless of input shape."""
    # String inputs
    assert parse_option_value("continue", "true") is True
    assert parse_option_value("continue", "false") is False
    # Already bool passthrough
    assert parse_option_value("continue", True) is True
    assert parse_option_value("continue", False) is False
    # Case-insensitive on string input
    assert parse_option_value("dry-run", "TRUE") is True
    # Non-string, non-bool falls back to bool(value)
    assert parse_option_value("enable-dht", 1) is True
    assert parse_option_value("enable-dht", 0) is False


def test_parse_option_value_integer_known_keys() -> None:
    """Integer-typed options are converted to int."""
    assert parse_option_value("split", "5") == 5
    assert isinstance(parse_option_value("split", "5"), int)
    assert parse_option_value("max-concurrent-downloads", "16") == 16
    # Non-numeric strings fall back to the raw value
    assert parse_option_value("split", "abc") == "abc"


def test_parse_option_value_passthrough_for_other_keys() -> None:
    """Strings, paths, and unknown keys pass through unchanged."""
    assert parse_option_value("dir", "/downloads") == "/downloads"
    assert parse_option_value("user-agent", "Mozilla/5.0") == "Mozilla/5.0"
    assert parse_option_value("referer", "") is None  # empty stays None
    assert parse_option_value("header", ["Cookie: a=1"]) == ["Cookie: a=1"]


def test_parse_option_value_sets_are_non_empty() -> None:
    """Regression guard: BOOLEAN_OPTIONS and INTEGER_OPTIONS must be populated.

    An accidentally emptied set would silently turn off conversion. Catch it here
    rather than via an obscure production failure.
    """
    assert "continue" in BOOLEAN_OPTIONS
    assert "dry-run" in BOOLEAN_OPTIONS
    assert "enable-dht" in BOOLEAN_OPTIONS
    assert "split" in INTEGER_OPTIONS
    assert "max-connection-per-server" in INTEGER_OPTIONS
    assert "max-concurrent-downloads" in INTEGER_OPTIONS
    assert "dry-run" in BOOLEAN_OPTIONS
    assert "enable-dht" in BOOLEAN_OPTIONS
    assert "split" in INTEGER_OPTIONS
    assert "max-connection-per-server" in INTEGER_OPTIONS
    assert "max-concurrent-downloads" in INTEGER_OPTIONS


# -----------------------------------------------------------------------------
# format_option_value
# -----------------------------------------------------------------------------


def test_format_option_value_none_returns_empty() -> None:
    """None and empty string format as the empty string (aria2 wire format)."""
    assert format_option_value("dir", None) == ""
    assert format_option_value("dir", "") == ""


def test_format_option_value_boolean_keys_render_as_strings() -> None:
    """Booleans are rendered as the literal 'true' / 'false'."""
    assert format_option_value("continue", True) == "true"
    assert format_option_value("continue", False) == "false"
    assert format_option_value("dry-run", False) == "false"


def test_format_option_value_other_keys_use_str() -> None:
    """Non-boolean values are stringified."""
    assert format_option_value("split", 5) == "5"
    assert format_option_value("dir", "/downloads") == "/downloads"
    assert format_option_value("max-download-limit", "1M") == "1M"


# -----------------------------------------------------------------------------
# parse_options_dict
# -----------------------------------------------------------------------------


def test_parse_options_dict_converts_mixed_types() -> None:
    """A realistic wire dict returns parsed Python native types."""
    wire = {
        "dir": "/downloads",
        "split": "16",
        "max-connection-per-server": "4",
        "continue": "true",
        "user-agent": "Mozilla/5.0",
    }
    parsed = parse_options_dict(wire)

    assert parsed == {
        "dir": "/downloads",
        "split": 16,
        "max-connection-per-server": 4,
        "continue": True,
        "user-agent": "Mozilla/5.0",
    }


def test_parse_options_dict_preserves_unknown_keys() -> None:
    """Unknown keys are passed through untouched."""
    parsed = parse_options_dict({"my-custom-option": "value", "split": "5"})
    assert parsed == {"my-custom-option": "value", "split": 5}


def test_parse_options_dict_handles_empty_input() -> None:
    """Empty input returns an empty dict."""
    assert parse_options_dict({}) == {}


# -----------------------------------------------------------------------------
# format_options_dict
# -----------------------------------------------------------------------------


def test_format_options_dict_converts_mixed_types() -> None:
    """Python native values render to aria2 wire format."""
    python_native = {
        "split": 16,
        "continue": True,
        "dir": "/downloads",
        "dry-run": False,
        "user-agent": "Mozilla/5.0",
    }
    formatted = format_options_dict(python_native)

    assert formatted == {
        "split": "16",
        "continue": "true",
        "dir": "/downloads",
        "dry-run": "false",
        "user-agent": "Mozilla/5.0",
    }


def test_format_options_dict_handles_empty_input() -> None:
    """Empty input returns an empty dict."""
    assert format_options_dict({}) == {}


# -----------------------------------------------------------------------------
# Round-trip
# -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("key", "wire_value"),
    [
        ("split", "16"),
        ("max-connection-per-server", "4"),
        ("max-concurrent-downloads", "5"),
        ("dir", "/downloads"),
        ("continue", "true"),
        ("dry-run", "false"),
    ],
)
def test_round_trip_parse_then_format_stabilises(key: str, wire_value: str) -> None:
    """parse → format returns the original wire string.

    This guards against drift: a future change to the parse set must still
    leave the formatter producing the same wire string.
    """
    parsed = parse_options_dict({key: wire_value})
    formatted = format_options_dict(parsed)
    assert formatted[key] == wire_value
