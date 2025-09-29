from src.player.player import Player
from src.prompt.prompt import Prompt
from src.stats.stats import Stats
from src.ui import userInterface
from src.world.timeService import TimeService
from unittest.mock import MagicMock


def createUserInterface():
    currentPrompt = Prompt("What would you like to do?")
    player = Player()
    stats = Stats()
    timeService = TimeService(player, stats)
    userInterfaceInstance = userInterface.UserInterface(
        currentPrompt, timeService, player
    )
    return userInterfaceInstance


def test_initialization():
    # call
    userInterfaceInstance = createUserInterface()

    # check
    assert userInterfaceInstance.currentPrompt != None
    assert userInterfaceInstance.player != None
    assert userInterfaceInstance.timeService != None


def test_lotsOfSpace():
    # setup
    userInterfaceInstance = createUserInterface()
    userInterface.print = MagicMock()

    # call
    userInterfaceInstance.lotsOfSpace()

    # check
    userInterface.print.assert_called_with("\n" * 20)


def test_divider():
    # setup
    userInterfaceInstance = createUserInterface()
    userInterface.print = MagicMock()

    # call
    userInterfaceInstance.divider()

    # check
    assert userInterface.print.call_count == 3


def test_showOptions():
    # setup
    userInterfaceInstance = createUserInterface()
    userInterface.print = MagicMock()
    userInterface.input = MagicMock(return_value="1")
    userInterfaceInstance.lotsOfSpace = MagicMock()
    userInterfaceInstance.divider = MagicMock()

    # call
    userInterfaceInstance.showOptions("descriptor", ["option1", "option2"])

    # check
    assert userInterface.print.call_count == 9
    userInterfaceInstance.lotsOfSpace.assert_called()
    assert userInterfaceInstance.divider.call_count == 3
    userInterface.input.assert_called_with("\n> ")
