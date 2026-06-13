import json
import os
import tempfile
from unittest.mock import MagicMock, patch
from src import fishE
from src.player.player import Player
from src.stats.stats import Stats
from src.world.timeService import TimeService
from src.player.playerJsonReaderWriter import PlayerJsonReaderWriter
from src.stats.statsJsonReaderWriter import StatsJsonReaderWriter
from src.world.timeServiceJsonReaderWriter import TimeServiceJsonReaderWriter
from src.saveFileManager import SaveFileManager


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


def createGameForPersistence(data_directory):
    # Build a FishE without running __init__ (which drives stdin); attach real
    # collaborators and a temp-dir-backed save manager so save()/load*() exercise
    # real serialization against a real (temporary) save slot.
    game = fishE.FishE.__new__(fishE.FishE)
    game.playerJsonReaderWriter = PlayerJsonReaderWriter()
    game.statsJsonReaderWriter = StatsJsonReaderWriter()
    game.timeServiceJsonReaderWriter = TimeServiceJsonReaderWriter()
    saveFileManager = SaveFileManager(data_directory=data_directory)
    saveFileManager.select_save_slot(1)
    game.saveFileManager = saveFileManager
    return game


def test_save_then_load_roundtrip():
    # restore real classes in case an earlier test mocked the module globals
    fishE.Player = Player
    fishE.Stats = Stats
    fishE.TimeService = TimeService

    with tempfile.TemporaryDirectory() as data_directory:
        # prepare - a game holding non-default state
        game = createGameForPersistence(data_directory)
        game.player = Player()
        game.player.fishCount = 42
        game.player.money = 123
        game.stats = Stats()
        game.stats.totalFishCaught = 7
        game.timeService = TimeService(game.player, game.stats)
        game.timeService.day = 9
        game.timeService.time = 15

        # call - persist, then load into a fresh game on the same slot
        game.save()
        loaded = createGameForPersistence(data_directory)
        loaded.loadPlayer()
        loaded.loadStats()
        loaded.loadTimeService()

        # check - state round-trips through disk
        assert loaded.player.fishCount == 42
        assert loaded.player.money == 123
        assert loaded.stats.totalFishCaught == 7
        assert loaded.timeService.day == 9
        assert loaded.timeService.time == 15


def test_save_writes_all_three_files():
    with tempfile.TemporaryDirectory() as data_directory:
        # prepare
        game = createGameForPersistence(data_directory)
        game.player = Player()
        game.stats = Stats()
        game.timeService = TimeService(game.player, game.stats)

        # call
        game.save()

        # check - all three save files are written into the selected slot
        slot = os.path.join(data_directory, "slot_1")
        assert os.path.exists(os.path.join(slot, "player.json"))
        assert os.path.exists(os.path.join(slot, "stats.json"))
        assert os.path.exists(os.path.join(slot, "timeService.json"))


def test_loadPlayer_recovers_from_corrupt_file():
    # restore the real Player so the except-path fallback builds a real player
    fishE.Player = Player

    with tempfile.TemporaryDirectory() as data_directory:
        # prepare - a player save file containing invalid JSON
        game = createGameForPersistence(data_directory)
        path = game.saveFileManager.get_save_path("player.json")
        with open(path, "w") as f:
            f.write("{ not valid json")

        # call - must not raise; falls back to a fresh player
        game.loadPlayer()

        # check
        assert isinstance(game.player, Player)
        assert game.player.fishCount == Player().fishCount
