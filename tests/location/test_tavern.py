from src.location.enum.locationType import LocationType
from src.location import tavern
from src.player.player import Player
from src.prompt.prompt import Prompt
from src.stats.stats import Stats
from src.ui.userInterface import UserInterface
from src.world.timeService import TimeService
from unittest.mock import MagicMock


def createTavern():
    currentPrompt = Prompt("What would you like to do?")
    player = Player()
    stats = Stats()
    timeService = TimeService(player, stats)
    userInterface = UserInterface(currentPrompt, timeService, player)
    return tavern.Tavern(userInterface, currentPrompt, player, stats, timeService)


def test_initialization():
    # call
    tavernInstance = createTavern()

    # check
    assert tavernInstance.userInterface != None
    assert tavernInstance.currentPrompt != None
    assert tavernInstance.player != None
    assert tavernInstance.stats != None
    assert tavernInstance.timeService != None


def test_run_get_drunk_action_success():
    # prepare
    tavernInstance = createTavern()
    tavernInstance.userInterface.showOptions = MagicMock(return_value="1")
    tavernInstance.getDrunk = MagicMock()
    tavernInstance.player.money = 10

    # call
    nextLocation = tavernInstance.run()

    # check
    assert nextLocation == LocationType.HOME
    tavernInstance.getDrunk.assert_called_once()


def test_run_get_drunk_action_failure_not_enough_money():
    # prepare
    tavernInstance = createTavern()
    tavernInstance.userInterface.showOptions = MagicMock(return_value="1")
    tavernInstance.getDrunk = MagicMock()
    tavernInstance.player.money = 5

    # call
    nextLocation = tavernInstance.run()

    # check
    assert nextLocation == LocationType.TAVERN
    tavernInstance.getDrunk.assert_not_called()


def test_run_gamble_action_success():
    # prepare
    tavernInstance = createTavern()
    tavernInstance.userInterface.showOptions = MagicMock(return_value="2")
    tavernInstance.gamble = MagicMock(return_value=LocationType.TAVERN)
    tavernInstance.player.money = 10

    # call
    nextLocation = tavernInstance.run()

    # check
    assert nextLocation == LocationType.TAVERN
    tavernInstance.gamble.assert_called_once()


def test_run_go_to_docks_action():
    # prepare
    tavernInstance = createTavern()
    tavernInstance.userInterface.showOptions = MagicMock(return_value="3")

    # call
    nextLocation = tavernInstance.run()

    # check
    assert nextLocation == LocationType.DOCKS


def test_getDrunk():
    # prepare
    tavernInstance = createTavern()
    tavernInstance.userInterface.lotsOfSpace = MagicMock()
    tavernInstance.userInterface.divider = MagicMock()
    tavernInstance.player.money = 10
    tavern.print = MagicMock()
    tavern.sys.stdout.flush = MagicMock()
    tavern.time.sleep = MagicMock()
    tavernInstance.timeService.increaseDay = MagicMock()

    # call
    tavernInstance.getDrunk()

    # check
    assert tavern.print.call_count == 3
    assert tavern.sys.stdout.flush.call_count == 3
    tavernInstance.timeService.increaseDay.assert_called_once()


def test_getDrunk_no_money_loss():
    # prepare
    tavernInstance = createTavern()
    tavernInstance.userInterface.lotsOfSpace = MagicMock()
    tavernInstance.userInterface.divider = MagicMock()
    tavernInstance.player.money = 100
    initial_money = tavernInstance.player.money
    tavern.print = MagicMock()
    tavern.sys.stdout.flush = MagicMock()
    tavern.time.sleep = MagicMock()
    tavern.random.random = MagicMock(return_value=0.5)  # No money loss (> 0.3)
    tavernInstance.timeService.increaseDay = MagicMock()

    # call
    tavernInstance.getDrunk()

    # check
    assert tavernInstance.player.money == initial_money - 10  # Only lost the $10 cost
    assert tavernInstance.stats.moneyLostWhileDrunk == 0  # No additional money lost tracked
    assert tavernInstance.currentPrompt.text == "You have a headache."
    tavernInstance.timeService.increaseDay.assert_called_once()


def test_getDrunk_with_money_loss():
    # prepare
    tavernInstance = createTavern()
    tavernInstance.userInterface.lotsOfSpace = MagicMock()
    tavernInstance.userInterface.divider = MagicMock()
    tavernInstance.player.money = 100
    initial_money = tavernInstance.player.money
    tavern.print = MagicMock()
    tavern.sys.stdout.flush = MagicMock()
    tavern.time.sleep = MagicMock()
    tavern.random.random = MagicMock(return_value=0.2)  # Money loss (< 0.3)
    tavern.random.uniform = MagicMock(return_value=0.3)  # 30% loss
    tavernInstance.timeService.increaseDay = MagicMock()

    # call
    tavernInstance.getDrunk()

    # check
    expected_loss = int((initial_money - 10) * 0.3)  # 30% of remaining money after $10 cost
    expected_money = initial_money - 10 - expected_loss
    assert tavernInstance.player.money == expected_money
    assert tavernInstance.stats.moneyLostWhileDrunk == expected_loss
    assert f"You have a headache. In your drunken stupor, you lost ${expected_loss}!" in tavernInstance.currentPrompt.text
    tavernInstance.timeService.increaseDay.assert_called_once()


def test_getDrunk_with_money_loss_no_money_remaining():
    # prepare
    tavernInstance = createTavern()
    tavernInstance.userInterface.lotsOfSpace = MagicMock()
    tavernInstance.userInterface.divider = MagicMock()
    tavernInstance.player.money = 10  # Only enough for the drink cost
    tavern.print = MagicMock()
    tavern.sys.stdout.flush = MagicMock()
    tavern.time.sleep = MagicMock()
    tavern.random.random = MagicMock(return_value=0.2)  # Money loss scenario
    tavernInstance.timeService.increaseDay = MagicMock()

    # call
    tavernInstance.getDrunk()

    # check
    assert tavernInstance.player.money == 0  # Only lost the $10 cost, no additional money to lose
    assert tavernInstance.currentPrompt.text == "You have a headache."
    tavernInstance.timeService.increaseDay.assert_called_once()
