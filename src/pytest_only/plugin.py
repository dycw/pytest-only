from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.config.argparsing import Parser
    from _pytest.nodes import Item


def pytest_addoption(parser: Parser) -> None:
    parser.addoption(
        "--only",
        dest="enable_only",
        default=True,
        action="store_true",
        help='Only run tests with the "only" marker',
    )
    parser.addoption(
        "--no-only",
        dest="enable_only",
        action="store_false",
        help="Disable --only filtering",
    )


def pytest_configure(config: Config) -> None:
    config.addinivalue_line(
        "markers", "only: normal runs will execute only marked tests"
    )


def pytest_collection_modifyitems(config: Config, items: list[Item]) -> None:
    if not config.getoption("--only"):
        return

    only: list[Item] = []
    other: list[Item] = []
    for item in items:
        (only if item.get_closest_marker("only") else other).append(item)

    if only:
        items[:] = only
        if other:
            config.hook.pytest_deselected(items=other)
