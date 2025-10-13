from src.config.config import Config


def createConfig():
    return Config()


def test_initialization():
    # call
    config = createConfig()

    # check save file paths
    assert config.dataDirectory == "data"
    assert config.playerSaveFile == "data/player.json"
    assert config.statsSaveFile == "data/stats.json"
    assert config.timeServiceSaveFile == "data/timeService.json"
    
    # check initial player values
    assert config.initialMoney == 20
    assert config.initialEnergy == 100
    assert config.initialFishCount == 0
    assert config.initialMoneyInBank == 0.01
    assert config.initialFishMultiplier == 1
    assert config.initialPriceForBait == 50
