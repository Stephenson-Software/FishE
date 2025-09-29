from src.location.enum.locationType import LocationType
from src.location import home
from src.player.player import Player
from src.prompt.prompt import Prompt
from src.stats.stats import Stats
from src.ui.userInterface import UserInterface
from src.world.timeService import TimeService
from unittest.mock import MagicMock


def createHome():
    currentPrompt = Prompt("What would you like to do?")
    player = Player()
    stats = Stats()
    timeService = TimeService(player, stats)
    userInterface = UserInterface(currentPrompt, timeService, player)
    return home.Home(userInterface, currentPrompt, player, stats, timeService)


def test_initialization():
    # call
    home = createHome()

    # check
    assert home.userInterface != None
    assert home.currentPrompt != None
    assert home.player != None
    assert home.stats != None
    assert home.timeService != None


def test_run_sleep_action():
    # prepare
    homeInstance = createHome()
    homeInstance.userInterface.showOptions = MagicMock(return_value="1")
    homeInstance.sleep = MagicMock()

    # call
    nextLocation = homeInstance.run()

    # check
    homeInstance.sleep.assert_called_once()
    assert nextLocation == LocationType.HOME


def test_run_see_stats_action():
    # prepare
    homeInstance = createHome()
    homeInstance.userInterface.showOptions = MagicMock(return_value="2")
    homeInstance.displayStats = MagicMock()

    # call
    nextLocation = homeInstance.run()

    # check
    homeInstance.displayStats.assert_called_once()
    assert nextLocation == LocationType.HOME


def test_run_go_to_docks_action():
    # prepare
    homeInstance = createHome()
    homeInstance.userInterface.showOptions = MagicMock(return_value="3")

    # call
    nextLocation = homeInstance.run()

    # check
    assert nextLocation == LocationType.DOCKS


def test_run_quit_action():
    # prepare
    homeInstance = createHome()
    homeInstance.userInterface.showOptions = MagicMock(return_value="4")

    # call
    nextLocation = homeInstance.run()

    # check
    assert nextLocation == LocationType.NONE


def test_sleep():
    # prepare
    homeInstance = createHome()
    homeInstance.timeService.increaseDay = MagicMock()
    homeInstance.player.energy = 50  # Set energy to something less than 100

    # call
    homeInstance.sleep()

    # check
    homeInstance.timeService.increaseDay.assert_called_once()
    assert homeInstance.currentPrompt.text == "You sleep until the next morning. You feel refreshed!"
    assert homeInstance.player.energy == 100  # Energy should be restored to full


def test_sleep_restores_energy():
    # prepare
    homeInstance = createHome()
    homeInstance.timeService.increaseDay = MagicMock()
    homeInstance.player.energy = 10  # Low energy

    # call
    homeInstance.sleep()

    # check
    assert homeInstance.player.energy == 100


def test_displayStats():
    # prepare
    homeInstance = createHome()
    homeInstance.userInterface.lotsOfSpace = MagicMock()
    home.print = MagicMock()
    home.input = MagicMock()

    # call
    homeInstance.displayStats()

    # check
    assert homeInstance.userInterface.lotsOfSpace.call_count == 1
    assert home.print.call_count == 7
    assert home.input.call_count == 1
