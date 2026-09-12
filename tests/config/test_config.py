import pytest

from src.config.config import Config


def createConfig():
    return Config()


@pytest.fixture(autouse=True)
def withoutSaveDirectoryOverride(monkeypatch):
    # FISHE_SAVE_DIR relocates the save directory, so a value left in the
    # environment would otherwise change what every test below sees.
    monkeypatch.delenv("FISHE_SAVE_DIR", raising=False)


def test_initialization():
    # call
    config = createConfig()

    # check
    assert config.dataDirectory == "data"

    # check initial player values
    assert config.initialMoney == 20
    assert config.initialFishCount == 0
    assert config.initialMoneyInBank == 0.01
    assert config.initialFishMultiplier == 1
    assert config.initialPriceForBait == 50


def test_save_directory_can_be_relocated(monkeypatch):
    # Deployments use this: a mounted volume for a server install, or the
    # browser-backed directory the Pyodide front-end mirrors to IndexedDB.
    monkeypatch.setenv("FISHE_SAVE_DIR", "/saves")

    config = createConfig()

    assert config.dataDirectory == "/saves"


def test_an_empty_save_directory_override_falls_back_to_the_default(monkeypatch):
    # An unset-but-present env var (a compose file with FISHE_SAVE_DIR=) must
    # not resolve save paths against the filesystem root.
    monkeypatch.setenv("FISHE_SAVE_DIR", "")

    assert createConfig().dataDirectory == "data"


def test_usage_reporting_is_on_by_default_and_aimed_at_the_trace_service(
    monkeypatch,
):
    for name in (
        "FISHE_USAGE_REPORTING_ENABLED",
        "FISHE_USAGE_REPORTING_ENDPOINT",
        "FISHE_USAGE_REPORTING_KEY",
    ):
        monkeypatch.delenv(name, raising=False)

    config = createConfig()

    assert config.usageReportingEnabled is True
    assert config.usageReportingEndpoint == "https://trace.danielstephenson.dev"
    # The bundled program key, so an install that sets nothing still reports.
    assert config.usageReportingKey
    assert config.usageReportingKey == config.usageReportingKey.strip()


@pytest.mark.parametrize("value", ["false", "FALSE", "0", "no", "off", " False "])
def test_usage_reporting_can_be_switched_off(monkeypatch, value):
    monkeypatch.setenv("FISHE_USAGE_REPORTING_ENABLED", value)

    assert createConfig().usageReportingEnabled is False


@pytest.mark.parametrize("value", ["", "  ", "true", "1", "yes", "anything"])
def test_only_a_clear_no_switches_usage_reporting_off(monkeypatch, value):
    # An unset-but-present variable (a compose file with
    # FISHE_USAGE_REPORTING_ENABLED=) leaves the default on, like FISHE_SAVE_DIR.
    monkeypatch.setenv("FISHE_USAGE_REPORTING_ENABLED", value)

    assert createConfig().usageReportingEnabled is True


def test_usage_reporting_endpoint_and_key_can_be_overridden(monkeypatch):
    # A self-hosted trace, or a test aiming the client at a loopback stub.
    monkeypatch.setenv("FISHE_USAGE_REPORTING_ENDPOINT", "http://127.0.0.1:1 ")
    monkeypatch.setenv("FISHE_USAGE_REPORTING_KEY", " k-override ")

    config = createConfig()

    assert config.usageReportingEndpoint == "http://127.0.0.1:1"
    assert config.usageReportingKey == "k-override"


def test_empty_usage_reporting_overrides_fall_back_to_the_defaults(monkeypatch):
    monkeypatch.setenv("FISHE_USAGE_REPORTING_ENDPOINT", "")
    monkeypatch.setenv("FISHE_USAGE_REPORTING_KEY", "")

    config = createConfig()

    assert config.usageReportingEndpoint == "https://trace.danielstephenson.dev"
    assert config.usageReportingKey
