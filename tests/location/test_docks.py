from src.location.enum.locationType import LocationType
from src.location import docks
from src.player.player import Player
from src.prompt.prompt import Prompt
from src.stats.stats import Stats
from src.ui.userInterface import UserInterface
from src.world.timeService import TimeService
from unittest.mock import MagicMock


def createDocks():
    currentPrompt = Prompt("What would you like to do?")
    player = Player()
    stats = Stats()
    timeService = TimeService(player, stats)
    userInterface = UserInterface(currentPrompt, timeService, player)
    return docks.Docks(userInterface, currentPrompt, player, stats, timeService)


def test_initialization():
    # call
    docksInstance = createDocks()

    # check
    assert docksInstance.userInterface != None
    assert docksInstance.currentPrompt != None
    assert docksInstance.player != None
    assert docksInstance.stats != None
    assert docksInstance.timeService != None


def test_run_fish_action():
    # prepare
    docksInstance = createDocks()
    docksInstance.userInterface.showOptions = MagicMock(return_value="1")
    docksInstance.fish = MagicMock()

    # call
    nextLocation = docksInstance.run()

    # check
    docksInstance.fish.assert_called_once()
    assert nextLocation == LocationType.DOCKS


def test_run_go_home_action():
    # prepare
    docksInstance = createDocks()
    docksInstance.userInterface.showOptions = MagicMock(return_value="2")

    # call
    nextLocation = docksInstance.run()

    # check
    assert nextLocation == LocationType.HOME


def test_run_go_to_shop_action():
    # prepare
    docksInstance = createDocks()
    docksInstance.userInterface.showOptions = MagicMock(return_value="3")

    # call
    nextLocation = docksInstance.run()

    # check
    assert nextLocation == LocationType.SHOP


def test_run_go_to_tavern_action():
    # prepare
    docksInstance = createDocks()
    docksInstance.userInterface.showOptions = MagicMock(return_value="4")

    # call
    nextLocation = docksInstance.run()

    # check
    assert nextLocation == LocationType.TAVERN


def test_run_go_to_bank_action():
    # prepare
    docksInstance = createDocks()
    docksInstance.userInterface.showOptions = MagicMock(return_value="5")

    # call
    nextLocation = docksInstance.run()

    # check
    assert nextLocation == LocationType.BANK


def test_fish():
    # prepare
    docksInstance = createDocks()
    docksInstance.userInterface.lotsOfSpace = MagicMock()
    docksInstance.userInterface.divider = MagicMock()
    docks.print = MagicMock()
    docks.sys.stdout.flush = MagicMock()
    docks.time.sleep = MagicMock()
    docks.random.randint = MagicMock(return_value=3)
    docksInstance.timeService.increaseTime = MagicMock()

    # call
    docksInstance.fish()

    # check
    docksInstance.userInterface.lotsOfSpace.assert_called_once()
    docksInstance.userInterface.divider.assert_called_once()
    assert docks.print.call_count == 4
    assert docks.sys.stdout.flush.call_count == 4
    assert docks.time.sleep.call_count == 4
    assert docksInstance.player.fishCount == 3
    assert docksInstance.stats.totalFishCaught == 3


def test_run_fish_action_low_energy():
    # prepare
    docksInstance = createDocks()
    docksInstance.player.energy = 5  # Too low to fish
    docksInstance.userInterface.showOptions = MagicMock(return_value="1")

    # call
    nextLocation = docksInstance.run()

    # check
    assert nextLocation == LocationType.DOCKS
    assert docksInstance.currentPrompt.text == "You're too tired to fish! Go home and sleep."


def test_fish_consumes_energy():
    # prepare
    docksInstance = createDocks()
    docksInstance.player.energy = 100
    docksInstance.userInterface.lotsOfSpace = MagicMock()
    docksInstance.userInterface.divider = MagicMock()
    docks.print = MagicMock()
    docks.sys.stdout.flush = MagicMock()
    docks.time.sleep = MagicMock()
    docks.random.randint = MagicMock(return_value=3)  # Fish for 3 hours, catch 3 fish
    docksInstance.timeService.increaseTime = MagicMock()

    # call
    docksInstance.fish()

    # check
    assert docksInstance.player.energy == 100 - (3 * 10)  # Should lose 30 energy (3 hours * 10 per hour)


def test_fish_with_limited_energy():
    # prepare  
    docksInstance = createDocks()
    docksInstance.player.energy = 25  # Only enough for 2 hours
    docksInstance.userInterface.lotsOfSpace = MagicMock()
    docksInstance.userInterface.divider = MagicMock()
    docks.print = MagicMock()
    docks.sys.stdout.flush = MagicMock()
    docks.time.sleep = MagicMock()
    docks.random.randint = MagicMock(return_value=5)  # Would normally fish for 5 hours, but energy limits to 2
    docksInstance.timeService.increaseTime = MagicMock()

    # call
    docksInstance.fish()

    # check
    assert docksInstance.player.energy == 5  # Should be 25 - (2 * 10)
    assert docksInstance.timeService.increaseTime.call_count == 2  # Only fished for 2 hours due to energy limit
