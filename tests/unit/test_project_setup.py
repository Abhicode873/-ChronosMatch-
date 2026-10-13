
"""Smoke tests for the ChronosMatch project foundation."""

import chronosmatch.core
from chronosmatch import __version__


def test_project_version() -> None:
    """Verify that the project version is defined correctly."""
    assert __version__ == "0.1.0"


def test_core_package_imports() -> None:
    """Verify that the core package can be imported."""
    assert chronosmatch.core.__name__ == "chronosmatch.core"
