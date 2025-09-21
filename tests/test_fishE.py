from unittest.mock import MagicMock
from src import fishE


def createFishE():
    fishE.Player = MagicMock()
    fishE.Stats = MagicMock()
    fishE.TimeService = MagicMock()
    fishE.Prompt = MagicMock()
    fishE.UserInterface = MagicMock()
    fishE.bank.Bank = MagicMock()
    fishE.shop.Shop = MagicMock()
    fishE.home.Home = MagicMock()
    fishE.docks.Docks = MagicMock()
    fishE.tavern.Tavern = MagicMock()
    fishE.PlayerJsonReaderWriter = MagicMock()
    fishE.TimeServiceJsonReaderWriter = MagicMock()
    fishE.StatsJsonReaderWriter = MagicMock()
    fishE.ShopJsonReaderWriter = MagicMock()
    fishE.loadPlayer = MagicMock()
    fishE.loadStats = MagicMock()
    fishE.loadTimeService = MagicMock()
    fishE.loadShop = MagicMock()
    return fishE.FishE()


def test_initialization():
    # call
    fishEInstance = createFishE()

    # check
    assert fishEInstance.running == True
    assert (
        fishE.Player.call_count == 1
        or fishEInstance.playerJsonReaderWriter.readPlayerFromFile.call_count == 1
    )
    assert (
        fishE.TimeService.call_count == 1
        or fishEInstance.timeServiceJsonReaderWriter.readTimeServiceFromFile.call_count
        == 1
    )
    assert (
        fishE.Stats.call_count == 1
        or fishEInstance.statsJsonReaderWriter.readStatsFromFile.call_count == 1
    )
    fishE.Prompt.assert_called_once()
    fishE.UserInterface.assert_called_once()
    fishE.bank.Bank.assert_called_once()
    fishE.shop.Shop.assert_called_once()
    fishE.home.Home.assert_called_once()
    fishE.docks.Docks.assert_called_once()
    fishE.tavern.Tavern.assert_called_once()
    fishE.PlayerJsonReaderWriter.assert_called_once()
    fishE.TimeServiceJsonReaderWriter.assert_called_once()
    fishE.StatsJsonReaderWriter.assert_called_once()
    fishE.ShopJsonReaderWriter.assert_called_once()
