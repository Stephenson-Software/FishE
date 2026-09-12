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
