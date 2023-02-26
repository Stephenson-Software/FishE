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
    return fishE.FishE()


def test_initialization():
    # call
    fishEInstance = createFishE()

    # check
    assert fishEInstance.running == True
    assert fishE.Player.call_count == 1 or fishEInstance.playerJsonReaderWriter.readPlayerFromFile.call_count == 1
    fishE.Stats.assert_called_once()
    assert fishE.TimeService.call_count == 1 or fishEInstance.timeServiceJsonReaderWriter.createTimeServiceFromJson.call_count == 1
    fishE.Prompt.assert_called_once()
    fishE.UserInterface.assert_called_once()
    fishE.bank.Bank.assert_called_once()
    fishE.shop.Shop.assert_called_once()
    fishE.home.Home.assert_called_once()
    fishE.docks.Docks.assert_called_once()
    fishE.tavern.Tavern.assert_called_once()
