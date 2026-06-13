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
    
    dialogue_options = [
        {"question": "Test question?", "response": "Test response"}
    ]
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
    
    dialogue_options = [
        {"question": "Test question?", "response": "Test response"}
    ]
    npc = NPC("Test NPC", "A test character", dialogue_options)

    # call
    userInterfaceInstance.showInteractiveDialogue(npc)

    # check - should have handled invalid input
    assert userInterface.input.call_count == 3
    # Should have printed "Invalid choice" message
    print_calls = [str(call) for call in userInterface.print.call_args_list]
    assert any("Invalid choice" in str(call) for call in print_calls)
