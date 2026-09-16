import pytest


@pytest.fixture(autouse=True)
def usageReportingOff(monkeypatch):
    """Keep every test away from the production trace service.

    Reporting is on by default, and several tests build a real FishE with a
    real Config - which would otherwise queue a genuine startup event to
    trace.danielstephenson.dev from every test run, and write the first-run
    notice marker into the repository's data directory. Tests that exercise
    reporting itself switch it back on and point the endpoint at a loopback
    stub server (see tests/test_usageReporting.py)."""
    monkeypatch.setenv("FISHE_USAGE_REPORTING_ENABLED", "false")
    # The machine running the tests may itself have opted out through the
    # client-wide variables; a test that turns reporting back on must start
    # from a clean slate, so both are cleared here.
    monkeypatch.delenv("TRACE_USAGE_REPORTING", raising=False)
    monkeypatch.delenv("DO_NOT_TRACK", raising=False)
