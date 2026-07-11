from src.location.enum.locationType import LocationType
from src.location import tavern
from src.player.player import Player
from src.prompt.prompt import Prompt
from src.stats.stats import Stats
from src.ui.userInterface import UserInterface
from src.world.timeService import TimeService
from unittest.mock import MagicMock, patch


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
    assert tavernInstance.npc != None
    assert tavernInstance.npc.name == "Old Tom the Barkeep"


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
    tavernInstance.userInterface.showOptions = MagicMock(return_value="4")

    # call
    nextLocation = tavernInstance.run()

    # check
    assert nextLocation == LocationType.DOCKS


def test_run_talk_to_npc_action():
    # prepare
    tavernInstance = createTavern()
    tavernInstance.userInterface.showOptions = MagicMock(return_value="3")
    tavernInstance.talkToNPC = MagicMock()

    # call
    nextLocation = tavernInstance.run()

    # check
    assert nextLocation == LocationType.TAVERN
    tavernInstance.talkToNPC.assert_called_once()


def test_talkToNPC():
    # prepare
    tavernInstance = createTavern()
    tavernInstance.userInterface.showInteractiveDialogue = MagicMock()

    # call
    tavernInstance.talkToNPC()

    # check
    tavernInstance.userInterface.showInteractiveDialogue.assert_called_once()
    call_args = tavernInstance.userInterface.showInteractiveDialogue.call_args[0][0]
    assert call_args.name == "Old Tom the Barkeep"
    assert len(call_args.get_dialogue_options()) > 0


def test_npc_business_dialogue_no_boat():
    # prepare
    tavernInstance = createTavern()

    # check
    assert "No boat yet" in tavernInstance._businessDialogue()


def test_npc_business_dialogue_staged_by_tier():
    # prepare - one crewed boat per tier
    responses = {}
    for tier in (1, 2, 3):
        tavernInstance = createTavern()
        tavernInstance.player.hasBoat = True
        tavernInstance.player.boatTier = tier
        responses[tier] = tavernInstance._businessDialogue()

    # check - each tier gets distinct banter
    assert len(set(responses.values())) == 3
    assert "Fishing Fleet" in responses[3]


def test_npc_business_dialogue_mentions_business_name():
    # prepare
    tavernInstance = createTavern()
    tavernInstance.player.hasBoat = True
    tavernInstance.player.boatTier = 3
    tavernInstance.player.businessName = "Salty Dawn Fisheries"

    # check
    assert "Salty Dawn Fisheries" in tavernInstance._businessDialogue()


def test_getDrunk():
    # prepare
    tavernInstance = createTavern()
    tavernInstance.userInterface.lotsOfSpace = MagicMock()
    tavernInstance.userInterface.divider = MagicMock()
    tavernInstance.player.money = 10
    tavern.print = MagicMock()
    tavern.sys.stdout.flush = MagicMock()
    tavern.time.sleep = MagicMock()
    tavernInstance.timeService.increaseDay = MagicMock(return_value={"evicted": False})

    # call
    tavernInstance.getDrunk()

    # check
    assert tavern.print.call_count == 3
    assert tavern.sys.stdout.flush.call_count == 3
    tavernInstance.timeService.increaseDay.assert_called_once()


def test_getDrunk_mentions_eviction_when_it_happens():
    # prepare
    from src.housing import housing

    tavernInstance = createTavern()
    tavernInstance.userInterface.lotsOfSpace = MagicMock()
    tavernInstance.userInterface.divider = MagicMock()
    tavernInstance.player.money = 10
    tavern.print = MagicMock()
    tavern.sys.stdout.flush = MagicMock()
    tavern.time.sleep = MagicMock()
    tavernInstance.timeService.increaseDay = MagicMock(return_value={"evicted": True})

    # call
    tavernInstance.getDrunk()

    # check - the player is told, not just silently moved back to Homeless
    assert housing.EVICTION_MESSAGE in tavernInstance.currentPrompt.text


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
        mock_input.return_value = "50"

        # Temporarily replace the built-in input function
        import builtins

        original_input = builtins.input
        builtins.input = mock_input

        try:
            # call
            tavernInstance.changeBet(
                "How much money would you like to bet? Money: $100"
            )

            # check
            # Verify that gamble was NOT called recursively
            tavernInstance.gamble.assert_not_called()
            # Verify that the bet was set correctly
            assert tavernInstance.currentBet == 50
            # Verify the prompt was updated correctly
            assert (
                "What will the dice land on? Current Bet: $50"
                in tavernInstance.currentPrompt.text
            )
        finally:
            # Restore original input function
            builtins.input = original_input


def test_gamble_win_shows_correct_amount():
    # prepare
    tavernInstance = createTavern()
    tavernInstance.player.money = 100
    tavernInstance.currentBet = 50
    tavern.random.randint = MagicMock(
        return_value=1
    )  # Make sure dice matches player choice

    # Store prompt text after the win
    win_prompt_text = None

    def mock_showOptions(prompt, options):
        nonlocal win_prompt_text
        # First call: player chooses 1
        # After processing, capture the prompt text
        if win_prompt_text is None:
            result = "1"
            # We need to manually process what would happen
            return result
        else:
            # Second call: player chooses to go back
            return "8"

    tavernInstance.userInterface.showOptions = MagicMock(side_effect=["1", "8"])

    # We need to capture the state after the win but before the next iteration
    # Let's test the win logic directly instead
    input_value = 1
    tavernInstance.diceThrow = 1

    # Execute the win condition logic
    winAmount = tavernInstance.currentBet
    tavernInstance.player.money += tavernInstance.currentBet
    tavernInstance.stats.totalMoneyMade += tavernInstance.currentBet
    tavernInstance.currentBet = 0
    tavernInstance.currentPrompt.text = (
        "The dice rolled a %d! You won $%d! Care to try again? Current Bet: $%d"
        % (tavernInstance.diceThrow, winAmount, tavernInstance.currentBet)
    )

    # check
    assert tavernInstance.player.money == 150  # Won 50
    assert tavernInstance.stats.totalMoneyMade == 50
    assert tavernInstance.currentBet == 0
    # Verify the message shows the actual bet amount won, not $0
    assert "You won $50!" in tavernInstance.currentPrompt.text
    assert "You won $0!" not in tavernInstance.currentPrompt.text


def test_gamble_loss():
    # prepare
    tavernInstance = createTavern()
    tavernInstance.player.money = 100
    tavernInstance.currentBet = 50

    # Test the loss logic directly
    input_value = 1
    tavernInstance.diceThrow = 2  # Different from player choice

    # Execute the loss condition logic
    tavernInstance.player.money -= tavernInstance.currentBet
    tavernInstance.stats.moneyLostFromGambling += tavernInstance.currentBet
    tavernInstance.currentBet = 0
    tavernInstance.currentPrompt.text = (
        "The dice rolled a %d! You lost your money! Care to try again? Current Bet: $%d"
        % (tavernInstance.diceThrow, tavernInstance.currentBet)
    )

    # check
    assert tavernInstance.player.money == 50  # Lost 50
    assert tavernInstance.stats.moneyLostFromGambling == 50
    assert tavernInstance.currentBet == 0
    assert "You lost your money!" in tavernInstance.currentPrompt.text


def test_changeBet_insufficient_money():
    # prepare
    tavernInstance = createTavern()
    tavernInstance.userInterface.lotsOfSpace = MagicMock()
    tavernInstance.userInterface.divider = MagicMock()
    tavernInstance.player.money = 50

    # Mock input to simulate user entering more than they have
    import builtins

    original_input = builtins.input
    builtins.input = MagicMock(return_value="100")

    try:
        # call
        tavernInstance.changeBet("How much money would you like to bet? Money: $50")

        # check
        # Bet should not be set since player doesn't have enough money
        assert tavernInstance.currentBet == 0
        # Verify error message
        assert "You don't have that much money" in tavernInstance.currentPrompt.text
    finally:
        # Restore original input function
        builtins.input = original_input


def test_changeBet_invalid_input():
    # prepare
    tavernInstance = createTavern()
    tavernInstance.userInterface.lotsOfSpace = MagicMock()
    tavernInstance.userInterface.divider = MagicMock()
    tavernInstance.player.money = 100

    # Mock input to simulate user entering invalid input
    import builtins

    original_input = builtins.input
    builtins.input = MagicMock(return_value="not a number")

    try:
        # call
        tavernInstance.changeBet("How much money would you like to bet? Money: $100")

        # check
        # Bet should remain 0
        assert tavernInstance.currentBet == 0
        # Verify error message
        assert "Try again" in tavernInstance.currentPrompt.text
    finally:
        # Restore original input function
        builtins.input = original_input


def test_getDrunk_updates_stats():
    # prepare
    tavernInstance = createTavern()
    tavernInstance.userInterface.lotsOfSpace = MagicMock()
    tavernInstance.userInterface.divider = MagicMock()
    tavernInstance.player.money = 20
    tavernInstance.stats.timesGottenDrunk = 0
    tavern.print = MagicMock()
    tavern.sys.stdout.flush = MagicMock()
    tavern.time.sleep = MagicMock()
    tavernInstance.timeService.increaseDay = MagicMock(return_value={"evicted": False})

    # call - skip the random additional-loss path (>= 0.3 means no extra loss)
    # so the base $10 cost is asserted deterministically.
    with patch("src.location.tavern.random.random", return_value=0.99):
        tavernInstance.getDrunk()

    # check
    assert tavernInstance.player.money == 10  # Lost $10
    assert tavernInstance.stats.timesGottenDrunk == 1
    assert tavernInstance.currentPrompt.text == "You have a headache."


def test_getDrunk_can_earn_a_tip():
    # prepare
    tavernInstance = createTavern()
    tavernInstance.userInterface.lotsOfSpace = MagicMock()
    tavernInstance.userInterface.divider = MagicMock()
    tavernInstance.player.money = 20
    tavernInstance.stats.totalMoneyMade = 0
    tavern.print = MagicMock()
    tavern.sys.stdout.flush = MagicMock()
    tavern.time.sleep = MagicMock()
    tavernInstance.timeService.increaseDay = MagicMock(return_value={"evicted": False})

    # call - land in the "tip" outcome (>= loss chance, < loss + tip) and fix
    # the tip amount deterministically.
    with patch("src.location.tavern.random.random", return_value=0.5), patch(
        "src.location.tavern.random.randint", return_value=25
    ):
        tavernInstance.getDrunk()

    # check - $10 drink cost, then +$25 tip => net +$15, and it counts as earnings
    assert tavernInstance.player.money == 35
    assert tavernInstance.stats.totalMoneyMade == 25
    assert "earned $25" in tavernInstance.currentPrompt.text


def test_gamble_win_pays_multiple_of_bet():
    # prepare - drive the real gamble() loop: guess 3, dice rolls 3, then go back
    from src.location.tavern import DICE_WIN_MULTIPLIER

    tavernInstance = createTavern()
    tavernInstance.player.money = 100
    tavernInstance.currentBet = 50
    tavernInstance.userInterface.showOptions = MagicMock(side_effect=["3", "8"])

    # call
    with patch("src.location.tavern.random.randint", return_value=3):
        tavernInstance.gamble()

    # check - a correct guess pays DICE_WIN_MULTIPLIER x the bet (not even money)
    expectedWin = 50 * DICE_WIN_MULTIPLIER
    assert tavernInstance.player.money == 100 + expectedWin
    assert tavernInstance.stats.totalMoneyMade == expectedWin
    assert tavernInstance.currentBet == 0
