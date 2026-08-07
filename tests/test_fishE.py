import json
import os
import tempfile
from unittest.mock import MagicMock, patch
from src import fishE
from src.player.player import Player
from src.stats.stats import Stats
from src.prompt.prompt import Prompt
from src.world.timeService import TimeService
from src.player.playerJsonReaderWriter import PlayerJsonReaderWriter
from src.stats.statsJsonReaderWriter import StatsJsonReaderWriter
from src.world.timeServiceJsonReaderWriter import TimeServiceJsonReaderWriter
from src.saveFileManager import SaveFileManager
from src.location.enum.locationType import LocationType
from src.housing import housing
from src.progression import progression

# Imported the same way fishE.py imports it (bare, not "src."-prefixed) so
# isinstance checks against fishE.FishE's real self.config compare the same
# module object - pytest.ini puts both "." and "src" on pythonpath, and
# these are two distinct module identities to Python.
from config.config import Config


def createFishE():
    # Player and Stats hand back real objects: __init__ runs the progression
    # catch-up over them (see src/progression), and its unlock conditions
    # compare real numbers. These are still mocks, so the call-count assertions
    # below hold either way.
    fishE.Player = MagicMock(return_value=Player())
    fishE.Stats = MagicMock(return_value=Stats())
    fishE.TimeService = MagicMock()
    fishE.Prompt = MagicMock()
    fishE.UserInterfaceFactory = MagicMock()
    fishE.bank.Bank = MagicMock()
    fishE.shop.Shop = MagicMock()
    fishE.home.Home = MagicMock()
    fishE.docks.Docks = MagicMock()
    fishE.tavern.Tavern = MagicMock()
    fishE.PlayerJsonReaderWriter = MagicMock()
    fishE.TimeServiceJsonReaderWriter = MagicMock()
    fishE.StatsJsonReaderWriter = MagicMock()
    fishE.SaveFileManager = MagicMock()
    # Same reason as Player/Stats above: whether __init__ takes the load path
    # depends on whether a save file happens to exist, and the progression
    # catch-up runs over whatever it ends up holding.
    fishE.PlayerJsonReaderWriter.return_value.readPlayerFromFile.return_value = Player()
    fishE.StatsJsonReaderWriter.return_value.readStatsFromFile.return_value = Stats()
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
    with patch.object(fishE.FishE, "_selectSaveFile", return_value=None):
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
    fishE.UserInterfaceFactory.create_user_interface.assert_called_once()
    fishE.bank.Bank.assert_called_once()
    fishE.shop.Shop.assert_called_once()
    fishE.home.Home.assert_called_once()
    fishE.docks.Docks.assert_called_once()
    fishE.tavern.Tavern.assert_called_once()
    fishE.PlayerJsonReaderWriter.assert_called_once()
    fishE.TimeServiceJsonReaderWriter.assert_called_once()
    fishE.StatsJsonReaderWriter.assert_called_once()
    fishE.SaveFileManager.assert_called_once()


def test_initialization_wires_config_into_saveFileManager_and_player():
    # call
    fishEInstance = createFishE()

    # check - a real Config seeds the mocked SaveFileManager's data directory
    # and is passed through to the (mocked) Player constructor
    assert isinstance(fishEInstance.config, Config)
    fishE.SaveFileManager.assert_called_once_with(
        data_directory=fishEInstance.config.dataDirectory
    )
    fishE.Player.assert_called_once_with(fishEInstance.config)


def createGameForPersistence(data_directory):
    # Build a FishE without running __init__ (which drives stdin); attach real
    # collaborators and a temp-dir-backed save manager so save()/load*() exercise
    # real serialization against a real (temporary) save slot.
    game = fishE.FishE.__new__(fishE.FishE)
    game.config = Config()
    game.playerJsonReaderWriter = PlayerJsonReaderWriter()
    game.statsJsonReaderWriter = StatsJsonReaderWriter()
    game.timeServiceJsonReaderWriter = TimeServiceJsonReaderWriter()
    saveFileManager = SaveFileManager(data_directory=data_directory)
    saveFileManager.select_save_slot(1)
    game.saveFileManager = saveFileManager
    # __init__ sets both up before the load block; save()/load*() report through
    # the front-end and record what would not load, so they are needed here too.
    game.failedLoads = []
    game.userInterface = MagicMock()
    return game


def createGameThroughInit(data_directory, saveFiles):
    # Run the real FishE.__init__ against a temp save slot holding exactly
    # saveFiles ({filename: json-serializable}), with only the save-slot menu
    # and the front-end stubbed out - everything else is the real wiring, so
    # the load block and the state it hands to TimeService are exercised.
    fishE.Player = Player
    fishE.Stats = Stats
    fishE.TimeService = TimeService
    fishE.Prompt = Prompt
    fishE.PlayerJsonReaderWriter = PlayerJsonReaderWriter
    fishE.StatsJsonReaderWriter = StatsJsonReaderWriter
    fishE.TimeServiceJsonReaderWriter = TimeServiceJsonReaderWriter
    fishE.SaveFileManager = SaveFileManager

    slot = os.path.join(data_directory, "slot_1")
    os.makedirs(slot, exist_ok=True)
    for filename, contents in saveFiles.items():
        with open(os.path.join(slot, filename), "w") as f:
            # A raw string is written verbatim so a test can plant a damaged
            # file; anything else is serialized as the JSON it stands for.
            if isinstance(contents, str):
                f.write(contents)
            else:
                json.dump(contents, f)

    config = Config()
    config.dataDirectory = data_directory

    def selectSlotOne(self):
        self.saveFileManager.select_save_slot(1)

    with patch.object(fishE, "Config", return_value=config), patch.object(
        fishE, "UserInterfaceFactory", MagicMock()
    ), patch.object(fishE.FishE, "_selectSaveFile", selectSlotOne):
        return fishE.FishE()


def test_init_rebinds_timeService_to_loaded_player_without_timeService_file():
    with tempfile.TemporaryDirectory() as data_directory:
        # prepare/call - a slot holding player.json and stats.json but no
        # timeService.json, which is the shape migrate_old_save_files() produces
        # from an old save that never had one
        game = createGameThroughInit(
            data_directory,
            {
                "player.json": PlayerJsonReaderWriter().createJsonFromPlayer(Player()),
                "stats.json": StatsJsonReaderWriter().createJsonFromStats(Stats()),
            },
        )

        # check - the TimeService drives the same objects the rest of the game
        # uses, so daily interest/income/rent land on the loaded player
        assert game.timeService.player is game.player
        assert game.timeService.stats is game.stats


def test_init_rebinds_timeService_when_only_player_file_present():
    with tempfile.TemporaryDirectory() as data_directory:
        # prepare/call - the shape left behind by a save interrupted after
        # player.json was written but before stats.json/timeService.json
        game = createGameThroughInit(
            data_directory,
            {"player.json": PlayerJsonReaderWriter().createJsonFromPlayer(Player())},
        )

        # check
        assert game.timeService.player is game.player
        assert game.timeService.stats is game.stats


def test_init_loads_timeService_when_present():
    with tempfile.TemporaryDirectory() as data_directory:
        # prepare - a slot with all three files, timeService.json holding
        # non-default state that only loadTimeService() would restore
        savedTimeService = TimeService(Player(), Stats())
        savedTimeService.day = 5
        savedTimeService.time = 14
        game = createGameThroughInit(
            data_directory,
            {
                "player.json": PlayerJsonReaderWriter().createJsonFromPlayer(Player()),
                "stats.json": StatsJsonReaderWriter().createJsonFromStats(Stats()),
                "timeService.json": TimeServiceJsonReaderWriter().createJsonFromTimeService(
                    savedTimeService
                ),
            },
        )

        # check - the loaded timeService's own state came from the file, not
        # the defaults built in __init__
        assert game.timeService.day == 5
        assert game.timeService.time == 14


def test_init_daily_tick_credits_the_loaded_player():
    with tempfile.TemporaryDirectory() as data_directory:
        # prepare - a saved player with money in the bank, in a slot with no
        # timeService.json
        savedPlayer = Player()
        savedPlayer.moneyInBank = 100
        game = createGameThroughInit(
            data_directory,
            {"player.json": PlayerJsonReaderWriter().createJsonFromPlayer(savedPlayer)},
        )
        moneyInBankBefore = game.player.moneyInBank

        # call
        game.timeService.increaseDay()

        # check - bank interest reaches the player the game actually reads
        assert game.player.moneyInBank > moneyInBankBefore
        assert game.stats.moneyMadeFromInterest > 0


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


def test_getTotalWealth_sums_cash_and_bank():
    # prepare
    game = fishE.FishE.__new__(fishE.FishE)
    game.player = Player()
    game.player.money = 30
    game.player.moneyInBank = 70

    # check
    assert game.getTotalWealth() == 100


def test_announceGoalIfReached_fires_once():
    # prepare - wealth at/above the goal
    game = fishE.FishE.__new__(fishE.FishE)
    game.player = Player()
    game.player.money = fishE.GOAL_AMOUNT
    game.player.moneyInBank = 0
    game.stats = Stats()
    game.prompt = Prompt("hi")

    # call - first time announces and records the flag
    assert game.announceGoalIfReached() is True
    assert fishE.GOAL_MILESTONE_NAME in game.stats.earnedMilestones
    assert "GOAL REACHED" in game.prompt.text

    # call again - already recorded, so it does not re-announce
    game.prompt.text = "fresh"
    assert game.announceGoalIfReached() is False
    assert "GOAL REACHED" not in game.prompt.text


def test_announceGoalIfReached_not_before_goal():
    # prepare - wealth below the goal
    game = fishE.FishE.__new__(fishE.FishE)
    game.player = Player()
    game.player.money = fishE.GOAL_AMOUNT - 1
    game.player.moneyInBank = 0
    game.stats = Stats()
    game.prompt = Prompt("hi")

    # call
    assert game.announceGoalIfReached() is False
    assert fishE.GOAL_MILESTONE_NAME not in game.stats.earnedMilestones


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


def test_loadPlayer_recovers_from_out_of_range_value():
    # restore the real Player so the except-path fallback builds a real player
    fishE.Player = Player

    with tempfile.TemporaryDirectory() as data_directory:
        # prepare - a syntactically valid save with an out-of-range value
        # (homeTier only goes up to 5 per schemas/player.json)
        game = createGameForPersistence(data_directory)
        path = game.saveFileManager.get_save_path("player.json")
        with open(path, "w") as f:
            json.dump(
                {
                    "fishCount": 0,
                    "money": 20,
                    "moneyInBank": 0.01,
                    "fishMultiplier": 1,
                    "priceForBait": 50,
                    "energy": 100,
                    "homeTier": 99,
                },
                f,
            )

        # call - must not raise; falls back to a fresh player instead of
        # loading a player whose homeTier housing.py can't resolve
        game.loadPlayer()

        # check
        assert isinstance(game.player, Player)
        assert game.player.homeTier == Player().homeTier


def test_loadStats_recovers_from_corrupt_file():
    # restore the real Stats so the except-path fallback builds real stats
    fishE.Stats = Stats

    with tempfile.TemporaryDirectory() as data_directory:
        # prepare - a stats save file containing invalid JSON
        game = createGameForPersistence(data_directory)
        path = game.saveFileManager.get_save_path("stats.json")
        with open(path, "w") as f:
            f.write("{ not valid json")

        # call - must not raise; falls back to fresh stats
        game.loadStats()

        # check
        assert isinstance(game.stats, Stats)
        assert game.stats.totalFishCaught == Stats().totalFishCaught


def test_loadTimeService_recovers_from_corrupt_file():
    # restore the real classes so the except-path fallback builds a real one
    fishE.Player = Player
    fishE.Stats = Stats
    fishE.TimeService = TimeService

    with tempfile.TemporaryDirectory() as data_directory:
        # prepare - a timeService save file containing invalid JSON
        game = createGameForPersistence(data_directory)
        game.player = Player()
        game.stats = Stats()
        path = game.saveFileManager.get_save_path("timeService.json")
        with open(path, "w") as f:
            f.write("{ not valid json")

        # call - must not raise; falls back to a fresh TimeService bound to
        # the game's current player/stats
        game.loadTimeService()

        # check
        assert game.timeService.day == TimeService(Player(), Stats()).day
        assert game.timeService.player is game.player
        assert game.timeService.stats is game.stats


def test_save_creates_missing_data_directory():
    with tempfile.TemporaryDirectory() as parent:
        # prepare - a data directory that does not exist yet
        data_directory = os.path.join(parent, "does-not-exist-yet")
        game = createGameForPersistence(data_directory)
        game.player = Player()
        game.stats = Stats()
        game.timeService = TimeService(game.player, game.stats)

        # call
        game.save()

        # check - save() created the directory tree itself
        assert os.path.exists(os.path.join(data_directory, "slot_1", "player.json"))


def test_save_handles_write_failure_without_raising():
    with tempfile.TemporaryDirectory() as data_directory:
        # prepare
        game = createGameForPersistence(data_directory)
        game.player = Player()
        game.stats = Stats()
        game.timeService = TimeService(game.player, game.stats)

        # call - must not raise even though writing to disk fails
        with patch("builtins.open", side_effect=IOError("disk full")):
            game.save()


def test_save_failure_is_reported_through_the_front_end():
    with tempfile.TemporaryDirectory() as data_directory:
        # prepare
        game = createGameForPersistence(data_directory)
        game.player = Player()
        game.stats = Stats()
        game.timeService = TimeService(game.player, game.stats)

        # call
        with patch("builtins.open", side_effect=IOError("disk full")):
            game.save()

        # check - the player is told through the UI contract every front-end
        # implements, rather than on a stdout none of them render
        game.userInterface.showDialogue.assert_called_once()
        said = game.userInterface.showDialogue.call_args[0][0]
        assert "could not be saved" in said
        assert "disk full" in said


def test_save_leaves_no_temporary_files_behind():
    with tempfile.TemporaryDirectory() as data_directory:
        # prepare
        game = createGameForPersistence(data_directory)
        game.player = Player()
        game.stats = Stats()
        game.timeService = TimeService(game.player, game.stats)

        # call
        game.save()

        # check - the temporary files the atomic write goes through are all
        # renamed into place, so nothing ending in .tmp survives the save
        slot = os.path.join(data_directory, "slot_1")
        assert [name for name in os.listdir(slot) if name.endswith(".tmp")] == []


def test_a_failed_save_does_not_truncate_the_previous_one():
    with tempfile.TemporaryDirectory() as data_directory:
        # prepare - a slot holding a good save
        game = createGameForPersistence(data_directory)
        game.player = Player()
        game.player.fishCount = 42
        game.stats = Stats()
        game.timeService = TimeService(game.player, game.stats)
        game.save()

        # call - the next save dies partway through writing player.json
        game.player.fishCount = 99
        with patch.object(
            game.playerJsonReaderWriter,
            "writePlayerToFile",
            side_effect=IOError("disk full"),
        ):
            game.save()

        # check - the save on disk is still the one that completed, not an
        # empty file left behind by a truncating open()
        reloaded = createGameForPersistence(data_directory)
        reloaded.loadPlayer()
        assert reloaded.player.fishCount == 42
        slot = os.path.join(data_directory, "slot_1")
        assert [name for name in os.listdir(slot) if name.endswith(".tmp")] == []


def corruptPlayerSlot():
    """A slot whose player.json is unreadable beside two intact files."""
    return {
        "player.json": "{ not valid json",
        "stats.json": StatsJsonReaderWriter().createJsonFromStats(Stats()),
        "timeService.json": TimeServiceJsonReaderWriter().createJsonFromTimeService(
            TimeService(Player(), Stats())
        ),
    }


def damagedBackupDirectories(data_directory):
    slot = os.path.join(data_directory, "slot_1")
    return sorted(name for name in os.listdir(slot) if name.startswith("damaged-"))


def test_load_failure_is_reported_through_the_front_end_not_stdout(capsys):
    with tempfile.TemporaryDirectory() as data_directory:
        # prepare/call - a slot whose player.json cannot be parsed
        game = createGameThroughInit(data_directory, corruptPlayerSlot())

        # check - said through the front-end, naming the file that failed
        said = "\n".join(
            call[0][0] for call in game.userInterface.showDialogue.call_args_list
        )
        assert "player.json" in said
        assert "new game has been started" in said
        # nothing on stdout, which no front-end renders
        assert "player.json" not in capsys.readouterr().out


def test_load_failure_names_every_file_that_failed_in_one_dialogue():
    with tempfile.TemporaryDirectory() as data_directory:
        # prepare/call - two of the three files are unreadable
        saveFiles = corruptPlayerSlot()
        saveFiles["stats.json"] = "{ not valid json either"
        game = createGameThroughInit(data_directory, saveFiles)

        # check - one dialogue, both files named
        game.userInterface.showDialogue.assert_called_once()
        said = game.userInterface.showDialogue.call_args[0][0]
        assert "player.json" in said
        assert "stats.json" in said


def test_a_schema_failure_is_described_in_one_short_line():
    with tempfile.TemporaryDirectory() as data_directory:
        # prepare/call - a syntactically valid save with an out-of-range value,
        # which jsonschema reports as a multi-paragraph dump of instance and
        # schema; a dialogue box can show no such thing
        savedPlayer = PlayerJsonReaderWriter().createJsonFromPlayer(Player())
        savedPlayer["homeTier"] = 99
        game = createGameThroughInit(data_directory, {"player.json": savedPlayer})

        # check - the reason is named, on one trimmed line
        said = game.userInterface.showDialogue.call_args[0][0]
        described = [line for line in said.splitlines() if "player.json" in line]
        assert len(described) == 1
        assert len(described[0]) < 160


def test_describeLoadFailure_trims_a_reason_too_long_for_a_dialogue():
    # prepare
    game = fishE.FishE.__new__(fishE.FishE)

    # call
    described = game._describeLoadFailure("player.json", IOError("x" * 500))

    # check - named, trimmed, and marked as trimmed
    assert described.startswith("player.json (")
    assert described.endswith("...)")
    assert len(described) < 160


def test_a_save_that_fails_to_load_is_copied_aside_before_it_is_overwritten():
    with tempfile.TemporaryDirectory() as data_directory:
        # prepare - a slot whose player.json cannot be parsed, loaded by a
        # game that therefore falls back to a brand-new character
        game = createGameThroughInit(data_directory, corruptPlayerSlot())
        slot = os.path.join(data_directory, "slot_1")

        # call - the first action of the fresh fallback game writes the slot
        game.save()

        # check - one backup directory holds every file as it was, so the run
        # that would not load is still recoverable by hand
        backups = damagedBackupDirectories(data_directory)
        assert len(backups) == 1
        backup = os.path.join(slot, backups[0])
        assert sorted(os.listdir(backup)) == [
            "player.json",
            "stats.json",
            "timeService.json",
        ]
        with open(os.path.join(backup, "player.json")) as f:
            assert f.read() == "{ not valid json"


def test_an_empty_player_file_is_reported_and_copied_aside():
    # prepare/call - a zero-byte player.json (what the old truncating write left
    # behind on a crash) beside a stats.json and timeService.json that load fine
    with tempfile.TemporaryDirectory() as data_directory:
        saveFiles = corruptPlayerSlot()
        saveFiles["player.json"] = ""
        game = createGameThroughInit(data_directory, saveFiles)

        # check - an empty file is a failed load, not an absent one: it is named
        # through the front-end and the slot is copied aside. Skipping the read
        # for it used to hand the player a starting character on the saved
        # calendar with nothing said and no copy kept.
        assert any("player.json" in described for described in game.failedLoads)
        said = game.userInterface.showDialogue.call_args[0][0]
        assert "player.json" in said
        assert len(damagedBackupDirectories(data_directory)) == 1


def test_an_empty_stats_or_time_file_is_reported_too():
    # prepare/call - player.json is intact; the other two are zero-byte
    with tempfile.TemporaryDirectory() as data_directory:
        game = createGameThroughInit(
            data_directory,
            {
                "player.json": PlayerJsonReaderWriter().createJsonFromPlayer(Player()),
                "stats.json": "",
                "timeService.json": "",
            },
        )

        # check - both are named in the one dialogue, same as any other damage
        described = "\n".join(game.failedLoads)
        assert "stats.json" in described
        assert "timeService.json" in described
        assert len(damagedBackupDirectories(data_directory)) == 1


def test_a_slot_that_loads_cleanly_is_not_copied_aside():
    with tempfile.TemporaryDirectory() as data_directory:
        # prepare/call - an intact save
        createGameThroughInit(
            data_directory,
            {
                "player.json": PlayerJsonReaderWriter().createJsonFromPlayer(Player()),
                "stats.json": StatsJsonReaderWriter().createJsonFromStats(Stats()),
                "timeService.json": TimeServiceJsonReaderWriter().createJsonFromTimeService(
                    TimeService(Player(), Stats())
                ),
            },
        )

        # check
        assert damagedBackupDirectories(data_directory) == []


def test_a_damaged_save_that_cannot_be_copied_aside_says_so():
    with tempfile.TemporaryDirectory() as data_directory:
        # prepare/call - the copy itself fails
        with patch("src.fishE.shutil.copy2", side_effect=OSError("read-only")):
            game = createGameThroughInit(data_directory, corruptPlayerSlot())

        # check - the player is warned the slot will be overwritten rather
        # than being told about a backup that does not exist
        said = game.userInterface.showDialogue.call_args[0][0]
        assert "could not be copied aside" in said
        assert damagedBackupDirectories(data_directory) == []


def test_selectSaveFile_new_game_selects_next_slot():
    # prepare - no existing saves; choosing the only non-quit option creates one
    game = fishE.FishE.__new__(fishE.FishE)
    game.saveFileManager = MagicMock()
    game.saveFileManager.list_save_files.return_value = []
    game.saveFileManager.get_next_available_slot.return_value = 1
    game.userInterface = MagicMock()
    game.userInterface.showOptions.return_value = "1"  # "Create New Save (Slot 1)"

    # call
    game._selectSaveFile()

    # check
    game.saveFileManager.select_save_slot.assert_called_once_with(1)


def test_selectSaveFile_loads_existing_slot():
    # prepare - one existing save; first option loads it
    game = fishE.FishE.__new__(fishE.FishE)
    game.saveFileManager = MagicMock()
    game.saveFileManager.list_save_files.return_value = [
        {"slot": 2, "metadata": {"day": 3, "money": 100, "fishCount": 5}}
    ]
    game.saveFileManager.get_next_available_slot.return_value = 1
    game.userInterface = MagicMock()
    game.userInterface.showOptions.return_value = "1"  # "Load Slot 2 (...)"

    # call
    game._selectSaveFile()

    # check
    game.saveFileManager.select_save_slot.assert_called_once_with(2)


def test_selectSaveFile_shows_a_damaged_slot_as_unpickable():
    # prepare - slot 1 will not parse, slot 2 is fine
    game = fishE.FishE.__new__(fishE.FishE)
    game.saveFileManager = MagicMock()
    game.saveFileManager.list_save_files.return_value = [
        {"slot": 1, "metadata": {"unreadable": True, "reason": "Expecting value"}},
        {"slot": 2, "metadata": {"day": 3, "money": 100, "fishCount": 5}},
    ]
    game.saveFileManager.get_next_available_slot.return_value = 3
    game.userInterface = MagicMock()
    game.userInterface.showOptions.return_value = "2"  # the intact slot

    # call
    game._selectSaveFile()

    # check - the damaged slot is on the menu (so the player knows it is there),
    # is not offered as something to load, and is marked unpickable with a reason
    # that points at the one menu entry that can clear it
    descriptor, options, unavailable = game.userInterface.showOptions.call_args[0]
    assert "damaged" in options[0]
    assert "Load Slot 1" not in options[0]
    assert 1 in unavailable
    assert "delete" in unavailable[1].lower()
    # the intact slot is untouched by any of that
    assert options[1] == "Load Slot 2 (Day 3, $100, 5 fish)"
    assert 2 not in unavailable
    game.saveFileManager.select_save_slot.assert_called_once_with(2)


def test_selectSaveFile_new_save_skips_a_damaged_slot():
    # prepare - the only slot is damaged, so a new game must land elsewhere
    game = fishE.FishE.__new__(fishE.FishE)
    game.saveFileManager = MagicMock()
    game.saveFileManager.list_save_files.return_value = [
        {"slot": 1, "metadata": {"unreadable": True, "reason": "Expecting value"}}
    ]
    game.saveFileManager.get_next_available_slot.return_value = 2
    game.userInterface = MagicMock()
    game.userInterface.showOptions.return_value = "2"  # "Create New Save (Slot 2)"

    # call
    game._selectSaveFile()

    # check - slot 2, not the occupied slot 1 whose intact stats.json and
    # timeService.json would have been overwritten by the first save
    options = game.userInterface.showOptions.call_args[0][1]
    assert options[1] == "Create New Save (Slot 2)"
    game.saveFileManager.select_save_slot.assert_called_once_with(2)


def test_selectSaveFile_explains_a_damaged_slot_a_front_end_let_through():
    # prepare - a front-end that hands back an unavailable option's number
    # anyway, which showOptions is contracted not to do. Without a branch for
    # it the menu would re-render forever and say nothing about why.
    game = fishE.FishE.__new__(fishE.FishE)
    game.saveFileManager = MagicMock()
    game.saveFileManager.list_save_files.return_value = [
        {"slot": 1, "metadata": {"unreadable": True, "reason": "Expecting value"}}
    ]
    game.saveFileManager.get_next_available_slot.return_value = 2
    game.userInterface = MagicMock()
    # the damaged slot, then "Create New Save (Slot 2)" to leave the menu
    game.userInterface.showOptions.side_effect = ["1", "2"]

    # call
    game._selectSaveFile()

    # check - the player is told why, and pointed at the way out, rather than
    # facing a menu that appears to ignore them
    said = game.userInterface.showDialogue.call_args[0][0]
    assert "could not be read" in said
    assert "Delete a Save File" in said
    game.saveFileManager.select_save_slot.assert_called_once_with(2)


def test_deleteSaveFile_tags_the_damaged_slot():
    # prepare - deleting is the only way to reclaim a damaged slot, so the row
    # has to be identifiable here
    game = fishE.FishE.__new__(fishE.FishE)
    game.saveFileManager = MagicMock()
    game.saveFileManager.delete_save_slot.return_value = True
    game.userInterface = MagicMock()
    game.userInterface.showOptions.side_effect = ["1", "1"]  # Delete Slot 1, then Yes

    # call
    game._deleteSaveFile(
        [
            {"slot": 1, "metadata": {"unreadable": True}},
            {"slot": 2, "metadata": {"day": 1, "money": 0, "fishCount": 0}},
        ]
    )

    # check
    options = game.userInterface.showOptions.call_args_list[0][0][1]
    assert options[0] == "Delete Slot 1 (damaged)"
    assert options[1] == "Delete Slot 2"
    game.saveFileManager.delete_save_slot.assert_called_once_with(1)


def test_deleteSaveFile_confirmed():
    # prepare - choose the slot, then confirm "Yes"
    game = fishE.FishE.__new__(fishE.FishE)
    game.saveFileManager = MagicMock()
    game.saveFileManager.delete_save_slot.return_value = True
    game.userInterface = MagicMock()
    game.userInterface.showOptions.side_effect = ["1", "1"]  # Delete Slot 1, then Yes

    # call
    result = game._deleteSaveFile([{"slot": 1, "metadata": {}}])

    # check
    assert result is True
    game.saveFileManager.delete_save_slot.assert_called_once_with(1)


def test_deleteSaveFile_cancelled():
    # prepare - choose "Cancel" (the last option)
    game = fishE.FishE.__new__(fishE.FishE)
    game.saveFileManager = MagicMock()
    game.userInterface = MagicMock()
    game.userInterface.showOptions.return_value = "2"  # Cancel (after one slot)

    # call
    result = game._deleteSaveFile([{"slot": 1, "metadata": {}}])

    # check
    assert result is False
    game.saveFileManager.delete_save_slot.assert_not_called()


def test_deleteSaveFile_declined_at_confirmation():
    # prepare - choose the slot, then decline at the "are you sure?" step
    game = fishE.FishE.__new__(fishE.FishE)
    game.saveFileManager = MagicMock()
    game.userInterface = MagicMock()
    game.userInterface.showOptions.side_effect = ["1", "2"]  # Delete Slot 1, then No

    # call
    result = game._deleteSaveFile([{"slot": 1, "metadata": {}}])

    # check
    assert result is False
    game.saveFileManager.delete_save_slot.assert_not_called()


def test_deleteSaveFile_reports_failure():
    # prepare - confirmed, but the underlying delete fails
    game = fishE.FishE.__new__(fishE.FishE)
    game.saveFileManager = MagicMock()
    game.saveFileManager.delete_save_slot.return_value = False
    game.userInterface = MagicMock()
    game.userInterface.showOptions.side_effect = ["1", "1"]  # Delete Slot 1, then Yes

    # call
    result = game._deleteSaveFile([{"slot": 1, "metadata": {}}])

    # check
    assert result is False
    game.userInterface.showDialogue.assert_called_once_with("Failed to delete Slot 1.")


def test_selectSaveFile_delete_then_quit():
    # prepare - one existing save; pick "Delete a Save File", cancel out of the
    # delete submenu, then pick "Quit" from the refreshed menu
    game = fishE.FishE.__new__(fishE.FishE)
    game.saveFileManager = MagicMock()
    game.saveFileManager.list_save_files.return_value = [
        {"slot": 1, "metadata": {"day": 1, "money": 0, "fishCount": 0}}
    ]
    game.saveFileManager.get_next_available_slot.return_value = 2
    game.userInterface = MagicMock()
    # Menu (with a save present): Load Slot 1 / Create New / Delete / Quit -> "3"
    # Delete submenu: Delete Slot 1 / Cancel -> "2" (Cancel)
    # Menu again: same options -> "4" (Quit)
    game.userInterface.showOptions.side_effect = ["3", "2", "4"]

    # call/check - Quit calls exit(0), which raises SystemExit
    try:
        game._selectSaveFile()
        assert False, "expected SystemExit"
    except SystemExit as e:
        assert e.code == 0
    game.saveFileManager.select_save_slot.assert_not_called()


def createGameForPlay():
    # A FishE built without running __init__, wired with mocks for everything
    # play() touches so a full iteration of the game loop can run in isolation.
    game = fishE.FishE.__new__(fishE.FishE)
    game.running = True
    game.currentLocation = LocationType.HOME
    game.player = Player()
    game.stats = Stats()
    game.prompt = Prompt("What would you like to do?")
    game.userInterface = MagicMock()
    game.timeService = MagicMock()
    game.timeService.increaseTime.return_value = {"evicted": False}
    game.locations = {
        LocationType.HOME: MagicMock(),
        LocationType.DOCKS: MagicMock(),
    }
    game.save = MagicMock()
    return game


def test_play_stops_when_location_returns_none():
    # prepare
    game = createGameForPlay()
    game.locations[LocationType.HOME].run.return_value = LocationType.NONE

    # call
    game.play()

    # check
    assert game.running is False
    game.save.assert_called_once()


def test_play_transitions_between_locations():
    # prepare - HOME sends the player to DOCKS, then DOCKS ends the run
    game = createGameForPlay()
    game.locations[LocationType.HOME].run.return_value = LocationType.DOCKS
    game.locations[LocationType.DOCKS].run.return_value = LocationType.NONE

    # call
    game.play()

    # check - both locations ran exactly once, in order, and each iteration saved
    game.locations[LocationType.HOME].run.assert_called_once()
    game.locations[LocationType.DOCKS].run.assert_called_once()
    assert game.save.call_count == 2


def test_play_appends_milestone_message():
    # prepare - crossing the "First Catch" threshold this iteration
    game = createGameForPlay()
    game.locations[LocationType.HOME].run.return_value = LocationType.NONE
    game.stats.totalFishCaught = 1

    # call
    game.play()

    # check
    assert "Milestone unlocked: First Catch!" in game.prompt.text


def test_play_appends_eviction_message():
    # prepare - the daily tick reports an eviction
    game = createGameForPlay()
    game.locations[LocationType.HOME].run.return_value = LocationType.NONE
    game.timeService.increaseTime.return_value = {"evicted": True}

    # call
    game.play()

    # check
    assert housing.EVICTION_MESSAGE in game.prompt.text


def test_play_announces_goal_once_reached():
    # prepare - wealth already at the goal amount
    game = createGameForPlay()
    game.locations[LocationType.HOME].run.return_value = LocationType.NONE
    game.player.money = fishE.GOAL_AMOUNT

    # call
    game.play()

    # check
    assert "GOAL REACHED" in game.prompt.text
    assert fishE.GOAL_MILESTONE_NAME in game.stats.earnedMilestones


def test_play_updates_ui_header_before_running_location():
    # prepare
    game = createGameForPlay()
    game.locations[LocationType.HOME].run.return_value = LocationType.NONE
    game.player.money = 10
    game.player.moneyInBank = 5

    # call
    game.play()

    # check - header fields are set from the location/wealth before run() is
    # called; the goal line stays hidden until the player has been shown it
    assert game.userInterface.currentLocationName == LocationType.HOME.capitalize()
    assert game.userInterface.goalProgress == ""


def test_play_shows_the_goal_line_once_it_is_unlocked():
    # prepare - a player who has already been shown the goal
    game = createGameForPlay()
    game.locations[LocationType.HOME].run.return_value = LocationType.NONE
    game.player.money = 10
    game.player.moneyInBank = 5
    progression.unlockAll(game.stats)

    # call
    game.play()

    # check
    assert game.userInterface.goalProgress == "$15 / $%d" % fishE.GOAL_AMOUNT


def test_play_announces_a_newly_unlocked_feature_with_its_reason():
    # prepare - the player lands their first catch this iteration
    game = createGameForPlay()
    game.locations[LocationType.HOME].run.return_value = LocationType.NONE
    game.stats.totalFishCaught = 1

    # call
    game.play()

    # check - the newly-appeared menu entry is explained on the same screen it
    # first shows up on
    shop = next(u for u in progression.UNLOCKS if u["id"] == progression.SHOP)
    assert shop["announcement"] in game.prompt.text
    assert progression.isUnlocked(game.stats, progression.SHOP)


def test_play_does_not_repeat_an_unlock_announcement():
    # prepare
    game = createGameForPlay()
    game.locations[LocationType.HOME].run.return_value = LocationType.NONE
    game.stats.totalFishCaught = 1
    progression.catchUp(game.player, game.stats)

    # call
    game.play()

    # check
    shop = next(u for u in progression.UNLOCKS if u["id"] == progression.SHOP)
    assert shop["announcement"] not in game.prompt.text


def test_init_starts_a_new_game_on_the_docks_with_nothing_unlocked():
    with tempfile.TemporaryDirectory() as data_directory:
        # prepare/call - an empty slot, i.e. a brand new game
        game = createGameThroughInit(data_directory, {})

        # check - the player opens on the docks, where fishing is the only
        # thing on the menu, and is greeted with something better than the
        # standing "What would you like to do?"
        assert game.currentLocation == LocationType.DOCKS
        assert game.stats.unlockedFeatures == []
        assert game.prompt.text == progression.OPENING_PROMPT


def test_init_catches_up_a_save_written_before_progression_existed():
    with tempfile.TemporaryDirectory() as data_directory:
        # prepare - an established player whose stats.json has no
        # unlockedFeatures at all
        player = Player()
        player.money = 8000
        player.fishMultiplier = 4
        stats = Stats()
        stats.totalFishCaught = 900
        stats.totalMoneyMade = 12000
        stats.hoursSpentFishing = 400
        statsJson = StatsJsonReaderWriter().createJsonFromStats(stats)
        del statsJson["unlockedFeatures"]

        # call
        game = createGameThroughInit(
            data_directory,
            {
                "player.json": PlayerJsonReaderWriter().createJsonFromPlayer(player),
                "stats.json": statsJson,
            },
        )

        # check - the village they already built is not re-locked around them,
        # and none of it is announced as news
        assert sorted(game.stats.unlockedFeatures) == sorted(
            progression.ALL_FEATURE_IDS
        )
        assert game.prompt.text != progression.OPENING_PROMPT


def test_play_announces_one_unlock_per_screen():
    # prepare - a first catch that also emptied the energy bar, so two unlocks
    # are earned on the same action
    game = createGameForPlay()
    game.locations[LocationType.HOME].run.return_value = LocationType.NONE
    game.stats.totalFishCaught = 1
    game.player.energy = 0

    # call - one iteration of the game loop
    game.play()

    # check - the player is handed one new button with its reason, not two;
    # the other is still earned and arrives on the next screen
    announcements = [
        unlock["announcement"]
        for unlock in progression.UNLOCKS
        if unlock["announcement"] in game.prompt.text
    ]
    assert len(announcements) == 1
    assert game.stats.unlockedFeatures == [progression.SHOP]


def test_play_appends_the_overnight_fleet_report():
    # The hourly tick is the one place guaranteed to run whatever the player
    # did, and it used to read only "evicted" - dropping the fleet's overnight
    # report on any action that happened to roll the day over.
    game = createGameForPlay()
    game.locations[LocationType.HOME].run.return_value = LocationType.NONE
    game.timeService.increaseTime.return_value = {
        "evicted": False,
        "report": ["The Marauder landed 12 fish."],
    }

    # call
    game.play()

    # check
    assert "The Marauder landed 12 fish." in game.prompt.text


def test_play_appends_the_fleet_report_and_the_eviction_together():
    # Both halves of the day's news survive the same tick, separated from the
    # action's own message by the game loop's wider gap.
    game = createGameForPlay()
    game.locations[LocationType.HOME].run.return_value = LocationType.NONE
    game.timeService.increaseTime.return_value = {
        "evicted": True,
        "report": ["The Marauder landed 12 fish."],
    }

    # call
    game.play()

    # check
    assert "The Marauder landed 12 fish." in game.prompt.text
    assert housing.EVICTION_MESSAGE in game.prompt.text
