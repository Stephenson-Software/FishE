from src.housing import housing
from src.player.player import Player
from src.prompt.prompt import Prompt
from src.stats.stats import Stats
from src.ui import userInterface
from src.world.timeService import TimeService
from unittest.mock import MagicMock, patch


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

    # check - the energy line shows the current tier's cap, not just the
    # raw value, so the housing energy-cap benefit is always visible
    expectedEnergyLine = " | Energy: %d/%d" % (
        userInterfaceInstance.player.energy,
        housing.maxEnergy(userInterfaceInstance.player),
    )
    printedLines = [call.args[0] for call in userInterface.print.call_args_list]
    assert expectedEnergyLine in printedLines


def test_showOptions_includes_location_when_set():
    # setup
    userInterfaceInstance = createUserInterface()
    userInterfaceInstance.currentLocationName = "Docks"
    userInterface.print = MagicMock()
    userInterface.input = MagicMock(return_value="1")
    userInterfaceInstance.lotsOfSpace = MagicMock()
    userInterfaceInstance.divider = MagicMock()

    # call
    userInterfaceInstance.showOptions("descriptor", ["option1"])

    # check - the header shows the current location
    printedLines = [call.args[0] for call in userInterface.print.call_args_list]
    assert " | Location: Docks" in printedLines


def test_showOptions_includes_goal_progress_when_set():
    # setup
    userInterfaceInstance = createUserInterface()
    userInterfaceInstance.goalProgress = "$1200 / $10000"
    userInterface.print = MagicMock()
    userInterface.input = MagicMock(return_value="1")
    userInterfaceInstance.lotsOfSpace = MagicMock()
    userInterfaceInstance.divider = MagicMock()

    # call
    userInterfaceInstance.showOptions("descriptor", ["option1"])

    # check
    printedLines = [call.args[0] for call in userInterface.print.call_args_list]
    assert " | Goal: $1200 / $10000" in printedLines


def test_showOptions_omits_location_when_unset():
    # setup
    userInterfaceInstance = createUserInterface()  # currentLocationName defaults to ""
    userInterface.print = MagicMock()
    userInterface.input = MagicMock(return_value="1")
    userInterfaceInstance.lotsOfSpace = MagicMock()
    userInterfaceInstance.divider = MagicMock()

    # call
    userInterfaceInstance.showOptions("descriptor", ["option1"])

    # check - no Location line is printed when none is set
    printedLines = [call.args[0] for call in userInterface.print.call_args_list]
    assert not any(line.startswith(" | Location:") for line in printedLines)


def test_showDialogue():
    # setup
    userInterfaceInstance = createUserInterface()
    userInterface.print = MagicMock()
    userInterface.input = MagicMock(return_value="")
    userInterfaceInstance.lotsOfSpace = MagicMock()
    userInterfaceInstance.divider = MagicMock()

    # call
    userInterfaceInstance.showDialogue("Test dialogue text")

    # check
    userInterfaceInstance.lotsOfSpace.assert_called_once()
    assert userInterfaceInstance.divider.call_count == 2
    userInterface.print.assert_called_with("Test dialogue text")
    userInterface.input.assert_called_with(" [ CONTINUE ]")
    assert userInterfaceInstance.currentPrompt.text == "What would you like to do?"


def test_showInteractiveDialogue_with_no_options():
    # setup
    from src.npc.npc import NPC

    userInterfaceInstance = createUserInterface()
    userInterface.print = MagicMock()
    userInterface.input = MagicMock(return_value="")
    userInterfaceInstance.lotsOfSpace = MagicMock()
    userInterfaceInstance.divider = MagicMock()
    npc = NPC("Test NPC", "A test character")

    # call
    userInterfaceInstance.showInteractiveDialogue(npc)

    # check - should fallback to simple introduction
    userInterfaceInstance.lotsOfSpace.assert_called_once()
    assert userInterfaceInstance.divider.call_count == 3
    userInterface.input.assert_called_with(" [ CONTINUE ]")
    assert userInterfaceInstance.currentPrompt.text == "What would you like to do?"


def test_showInteractiveDialogue_select_option():
    # setup
    from src.npc.npc import NPC

    userInterfaceInstance = createUserInterface()
    userInterface.print = MagicMock()
    # First input selects option 1, second input continues, third input selects Back
    userInterface.input = MagicMock(side_effect=["1", "", "2"])
    userInterfaceInstance.lotsOfSpace = MagicMock()
    userInterfaceInstance.divider = MagicMock()

    dialogue_options = [{"question": "Test question?", "response": "Test response"}]
    npc = NPC("Test NPC", "A test character", dialogue_options)

    # call
    userInterfaceInstance.showInteractiveDialogue(npc)

    # check - should have shown menu, response, and back option
    assert userInterface.input.call_count == 3
    assert userInterfaceInstance.currentPrompt.text == "What would you like to do?"


def test_showInteractiveDialogue_invalid_choice():
    # setup
    from src.npc.npc import NPC

    userInterfaceInstance = createUserInterface()
    userInterface.print = MagicMock()
    # First input is invalid, second continues error message, third selects Back
    userInterface.input = MagicMock(side_effect=["99", "", "2"])
    userInterfaceInstance.lotsOfSpace = MagicMock()
    userInterfaceInstance.divider = MagicMock()

    dialogue_options = [{"question": "Test question?", "response": "Test response"}]
    npc = NPC("Test NPC", "A test character", dialogue_options)

    # call
    userInterfaceInstance.showInteractiveDialogue(npc)

    # check - should have handled invalid input
    assert userInterface.input.call_count == 3
    # Should have printed "Invalid choice" message
    print_calls = [str(call) for call in userInterface.print.call_args_list]
    assert any("Invalid choice" in str(call) for call in print_calls)


def test_promptForText_returns_entered_line():
    # setup
    userInterfaceInstance = createUserInterface()
    userInterfaceInstance.lotsOfSpace = MagicMock()
    userInterfaceInstance.divider = MagicMock()
    userInterface.print = MagicMock()
    userInterface.input = MagicMock(return_value="42")

    # call
    result = userInterfaceInstance.promptForText("How much?")

    # check - the prompt is shown and the typed line is returned
    assert result == "42"
    userInterface.input.assert_called_with("> ")
    printed = [str(call) for call in userInterface.print.call_args_list]
    assert any("How much?" in call for call in printed)


def test_promptForNumber_parses_console_input():
    # setup
    userInterfaceInstance = createUserInterface()
    userInterfaceInstance.lotsOfSpace = MagicMock()
    userInterfaceInstance.divider = MagicMock()
    userInterface.print = MagicMock()

    # check - numeric input parses; non-numeric returns None
    userInterface.input = MagicMock(return_value="10.5")
    assert userInterfaceInstance.promptForNumber("Amount?") == 10.5
    userInterface.input = MagicMock(return_value="oops")
    assert userInterfaceInstance.promptForNumber("Amount?") is None


def test_timedKeyPress_returns_reaction_seconds():
    # setup
    userInterfaceInstance = createUserInterface()
    userInterface.print = MagicMock()
    userInterface.input = MagicMock(return_value="")

    # call - start at t=0, key pressed at t=1.5
    with patch("src.ui.userInterface.time.time", side_effect=[0.0, 1.5]):
        reaction = userInterfaceInstance.timedKeyPress("React!")

    # check
    assert reaction == 1.5
