"""
Test to enforce that device model name strings are only referenced in models.py.

Any time a model name (e.g. "DR-HTF007S") is hardcoded in a source file other
than models.py it becomes a maintenance hazard — the canonical definition in
SUPPORTED_DEVICES can drift out of sync with scattered copies.  This test
catches that before it reaches the main branch.
"""

import ast
from pathlib import Path

import pytest

# Repository root, derived from this file's location (tests/pydreo/test_no_hardcoded_models.py)
REPO_ROOT = Path(__file__).parents[2]

# Root of the pydreo source package
PYDREO_SRC_DIR = REPO_ROOT / "custom_components" / "dreo" / "pydreo"
MODELS_FILE = PYDREO_SRC_DIR / "models.py"


def _load_model_names_from_models_py() -> set[str]:
    """Return every key in SUPPORTED_DEVICES by parsing models.py with AST.

    Only exact model strings (e.g. "DR-HTF007S") are returned; family-prefix
    entries such as "DR-HTF" that serve as catch-all fallbacks are included too
    because they also must not be duplicated outside models.py.
    """
    tree = ast.parse(MODELS_FILE.read_text(encoding="utf-8"), filename=str(MODELS_FILE))
    model_names: set[str] = set()

    for node in ast.walk(tree):
        # SUPPORTED_DEVICES = { "DR-...": ..., ... }
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "SUPPORTED_DEVICES":
                    if isinstance(node.value, ast.Dict):
                        for key in node.value.keys:
                            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                                model_names.add(key.value)

    return model_names


def _collect_string_literals(source_path: Path) -> list[tuple[int, str]]:
    """Return (line_number, string_value) for every string constant in *source_path*."""
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    results: list[tuple[int, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            results.append((node.lineno, node.value))

    return results


def _source_files_to_scan() -> list[Path]:
    """Return all .py files under the pydreo package, excluding models.py itself."""
    return [p for p in PYDREO_SRC_DIR.rglob("*.py") if p.resolve() != MODELS_FILE.resolve()]


class TestNoHardcodedModels:
    """Ensure device model names are only referenced as string literals in models.py."""

    def test_model_names_found_in_supported_devices(self):
        """Sanity check: SUPPORTED_DEVICES must contain at least one DR- prefixed model name."""
        model_names = _load_model_names_from_models_py()
        assert len(model_names) > 0, "Could not parse any model names from SUPPORTED_DEVICES in models.py"
        dr_models = [m for m in model_names if m.startswith("DR-")]
        assert len(dr_models) > 0, "Expected at least one 'DR-' prefixed model in SUPPORTED_DEVICES"

    def test_no_model_names_in_source_files(self):
        """Fail if any source file outside models.py contains a model name string literal."""
        model_names = _load_model_names_from_models_py()
        source_files = _source_files_to_scan()

        violations: list[str] = []

        for source_file in sorted(source_files):
            for line_no, string_value in _collect_string_literals(source_file):
                if string_value in model_names:
                    rel_path = source_file.relative_to(REPO_ROOT)
                    violations.append(f"  {rel_path}:{line_no}  →  {string_value!r}")

        if violations:
            joined = "\n".join(violations)
            pytest.fail(
                "Model names must only appear as string literals in models.py.\n"
                "The following violations were found:\n"
                f"{joined}\n\n"
                "Move any model-specific logic to SUPPORTED_DEVICES in models.py instead."
            )
