from unittest.mock import MagicMock, patch
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
    fishE.SaveFileManager = MagicMock()
    fishE.loadPlayer = MagicMock()
    fishE.loadStats = MagicMock()
    fishE.loadTimeService = MagicMock()
    
    # Mock the save file manager instance methods
    mock_save_manager = MagicMock()
    mock_save_manager.get_save_path.return_value = "data/player.json"
    mock_save_manager.list_save_files.return_value = []
    mock_save_manager.get_next_available_slot.return_value = 1
    fishE.SaveFileManager.return_value = mock_save_manager
    
    # Mock the _selectSaveFile method to avoid stdin interaction
    with patch.object(fishE.FishE, '_selectSaveFile', return_value=None):
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
    fishE.SaveFileManager.assert_called_once()
