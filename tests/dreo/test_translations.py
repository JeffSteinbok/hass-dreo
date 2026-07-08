"""
Tests validating translation file consistency.

These guard against the classes of bugs that otherwise only surface in CI
(hassfest) or at runtime:

* Every ``translations/<lang>.json`` file must have the exact same set of keys
  as ``strings.json`` (the source of truth), so no language drifts ahead of or
  behind the others.
* Every entity ``state`` translation key must be a valid Home Assistant slug
  (``[a-z0-9_-]`` and not starting/ending with ``-``/``_``). hassfest only
  validates ``strings.json`` and ``en.json``, so this check extends that rule to
  all languages and lets us catch capitalized state keys locally.
"""

import json
import re
from pathlib import Path

import pytest


DREO_DIR = Path(__file__).parent.parent.parent / "custom_components" / "dreo"
STRINGS_FILE = DREO_DIR / "strings.json"
TRANSLATIONS_DIR = DREO_DIR / "translations"

# Home Assistant translation key slug rule (mirrors hassfest).
SLUG_RE = re.compile(r"^[a-z0-9]([a-z0-9_-]*[a-z0-9])?$")


def _translation_files() -> list[Path]:
    return sorted(TRANSLATIONS_DIR.glob("*.json"))


def _load(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def _flatten_keys(obj, prefix: str = "") -> set[str]:
    """Return the set of leaf key paths in a nested dict."""
    keys: set[str] = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            keys |= _flatten_keys(value, f"{prefix}/{key}")
    else:
        keys.add(prefix)
    return keys


def _state_key_paths(obj, prefix: str = "", under_state: bool = False) -> list[str]:
    """Return the paths of all keys that live inside a ``state`` dictionary."""
    paths: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if under_state:
                paths.append(f"{prefix}/{key}")
            paths.extend(_state_key_paths(value, f"{prefix}/{key}", key == "state"))
    return paths


def test_strings_file_exists():
    """The source-of-truth strings.json must exist."""
    assert STRINGS_FILE.is_file(), "custom_components/dreo/strings.json is missing"


def test_translation_files_exist():
    """There must be at least the English translation file."""
    files = {path.name for path in _translation_files()}
    assert "en.json" in files, "translations/en.json is missing"


@pytest.mark.parametrize("path", _translation_files(), ids=lambda p: p.name)
def test_translation_is_valid_json(path: Path):
    """Every translation file must be valid JSON."""
    _load(path)


@pytest.mark.parametrize("path", _translation_files(), ids=lambda p: p.name)
def test_translation_matches_strings_keys(path: Path):
    """Every translation file must have the exact same keys as strings.json."""
    reference = _flatten_keys(_load(STRINGS_FILE))
    actual = _flatten_keys(_load(path))

    missing = reference - actual
    extra = actual - reference
    assert not missing, f"{path.name} is missing keys present in strings.json: {sorted(missing)}"
    assert not extra, f"{path.name} has keys not present in strings.json: {sorted(extra)}"


@pytest.mark.parametrize(
    "path",
    [STRINGS_FILE, *_translation_files()],
    ids=lambda p: p.name,
)
def test_state_keys_are_valid_slugs(path: Path):
    """Entity state translation keys must be valid HA slugs (lowercase)."""
    invalid = [
        key_path
        for key_path in _state_key_paths(_load(path))
        if not SLUG_RE.match(key_path.rsplit("/", 1)[-1])
    ]
    assert not invalid, (
        f"{path.name} has invalid state translation keys "
        f"(must be lowercase slug [a-z0-9_-]): {invalid}"
    )
