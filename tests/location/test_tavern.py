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


def test_changeBet_no_recursive_gamble():
    # prepare
    tavernInstance = createTavern()
    tavernInstance.userInterface.lotsOfSpace = MagicMock()
    tavernInstance.userInterface.divider = MagicMock()
    tavernInstance.player.money = 100
    
    # Mock gamble method to detect if it's called
    tavernInstance.gamble = MagicMock()
    
    # Mock input to simulate user entering valid bet amount
    with MagicMock() as mock_input:
        mock_input.return_value = '50'
        
        # Temporarily replace the built-in input function
        import builtins
        original_input = builtins.input
        builtins.input = mock_input
        
        try:
            # call
            tavernInstance.changeBet("How much money would you like to bet? Money: $100")
            
            # check
            # Verify that gamble was NOT called recursively
            tavernInstance.gamble.assert_not_called()
            # Verify that the bet was set correctly
            assert tavernInstance.currentBet == 50
            # Verify the prompt was updated correctly
            assert "What will the dice land on? Current Bet: $50" in tavernInstance.currentPrompt.text
        finally:
            # Restore original input function
            builtins.input = original_input
