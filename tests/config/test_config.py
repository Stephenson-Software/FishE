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
