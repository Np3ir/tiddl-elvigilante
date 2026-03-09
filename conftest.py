"""
conftest.py — Pytest configuration for tiddl worktree.

This file redirects 'tiddl' imports to the worktree directory so that
tests always test the local code (not the installed tiddl package).
"""
from __future__ import annotations
import sys
from pathlib import Path
import importlib.util
import types

_WORKTREE = Path(__file__).parent
_TIDDL = _WORKTREE / "tiddl"


def _install_worktree_as_tiddl() -> None:
    """Replace 'tiddl' in sys.modules with the worktree package."""
    # Remove any cached tiddl modules (installed package)
    stale = [k for k in list(sys.modules) if k == "tiddl" or k.startswith("tiddl.")]
    for key in stale:
        del sys.modules[key]

    # Create 'tiddl' namespace package pointing to tiddl/ subdir
    spec = importlib.util.spec_from_file_location(
        "tiddl",
        str(_TIDDL / "__init__.py"),
        submodule_search_locations=[str(_TIDDL)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["tiddl"] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]


_install_worktree_as_tiddl()
