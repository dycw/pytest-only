from __future__ import annotations

from pytest_only import __version__


def test_main() -> None:
    assert isinstance(__version__, str)
