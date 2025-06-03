from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from pytest import Testdir

pytest_plugins = "pytester"

if TYPE_CHECKING:
    from _pytest.pytester import Pytester, RunResult


@pytest.fixture(autouse=True)
def setup_syspath(testdir: Testdir) -> None:
    repo_dir = Path(__file__).resolve().parent.parent
    testdir.syspathinsert(str(repo_dir))
    _ = testdir.makeconftest('pytest_plugins = ["pytest_only.plugin"]')
    _ = testdir.makeini("[pytest]\naddopts = -p no:only")


def assert_test_did_run(res: RunResult, name: str) -> None:
    res.stdout.fnmatch_lines(f"*{name}*")


def assert_test_did_not_run(res: RunResult, name: str) -> None:
    with pytest.raises(pytest.fail.Exception):
        res.stdout.fnmatch_lines(f"*{name}*")


def test_function(testdir: Pytester) -> None:
    file = testdir.makepyfile(
        """
        import pytest

        def test_should_not_run():
            pass

        @pytest.mark.only
        def test_should_run():
            pass

        def test_should_also_not_run():
            pass
        """
    )
    res = testdir.runpytest(file, "--verbose")
    outcomes = res.parseoutcomes()
    assert outcomes.get("passed") == 1
    assert_test_did_run(res, "test_should_run")
    assert_test_did_not_run(res, "test_should_not_run")
    assert_test_did_not_run(res, "test_should_also_not_run")


def test_class(testdir: Pytester) -> None:
    file = testdir.makepyfile(
        """
        import pytest

        def test_should_not_run():
            pass

        @pytest.mark.only
        class TestShouldRun:
            def test_should_run(self):
                pass

            def test_should_also_run(self):
                pass

        class TestShouldNotRun:
            def test_should_also_not_run(self):
                pass
        """
    )
    res = testdir.runpytest(file, "--verbose")
    outcomes = res.parseoutcomes()
    assert outcomes.get("passed") == 2
    assert_test_did_run(res, "test_should_run")
    assert_test_did_run(res, "test_should_also_run")
    assert_test_did_not_run(res, "test_should_not_run")
    assert_test_did_not_run(res, "test_should_also_not_run")


def test_file(testdir: Pytester) -> None:
    should_run = testdir.makepyfile(
        should_run="""
        import pytest

        pytestmark = pytest.mark.only

        def test_should_run():
            pass

        def test_should_also_run():
            pass
        """
    )

    should_not_run = testdir.makepyfile(
        should_not_run="""
        def test_should_not_run():
            pass
        """
    )

    res = testdir.runpytest("--verbose", should_run, should_not_run)
    outcomes = res.parseoutcomes()
    assert outcomes.get("passed") == 2
    assert_test_did_run(res, "test_should_run")
    assert_test_did_run(res, "test_should_also_run")
    assert_test_did_not_run(res, "test_should_not_run")


def test_no_only_cmdline_option(testdir: Pytester) -> None:
    file = testdir.makepyfile(
        """
        import pytest

        def test_should_run_as_well():
            pass

        @pytest.mark.only
        def test_should_run():
            pass

        def test_should_also_run():
            pass
        """
    )
    res = testdir.runpytest(file, "--verbose", "--no-only")
    outcomes = res.parseoutcomes()
    assert "passed" in outcomes
    assert_test_did_run(res, "test_should_run")
    assert_test_did_run(res, "test_should_run_as_well")
    assert_test_did_run(res, "test_should_also_run")


def test_negating_cmdline_options(testdir: Pytester) -> None:
    file = testdir.makepyfile(
        """
        import pytest

        def test_should_not_run():
            pass

        @pytest.mark.only
        def test_should_run():
            pass

        def test_should_also_not_run():
            pass
        """
    )
    res = testdir.runpytest(file, "--verbose", "--no-only", "--only")
    outcomes = res.parseoutcomes()
    assert outcomes.get("passed") == 1
    assert_test_did_run(res, "test_should_run")
    assert_test_did_not_run(res, "test_should_also_not_run")
    assert_test_did_not_run(res, "test_should_not_run")
