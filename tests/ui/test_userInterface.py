import sys
import os

# Add src to the path so imports work correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from player.player import Player
from prompt.prompt import Prompt
from stats.stats import Stats
from ui.consoleUserInterface import ConsoleUserInterface
from world.timeService import TimeService
from unittest.mock import patch


def createUserInterface():
    currentPrompt = Prompt("What would you like to do?")
    player = Player()
    stats = Stats()
    timeService = TimeService(player, stats)
    userInterfaceInstance = ConsoleUserInterface(
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
    
    # call with patch
    with patch('builtins.print') as mock_print:
        userInterfaceInstance.lotsOfSpace()
        
        # check
        mock_print.assert_called_with("\n" * 20)


def test_divider():
    # setup
    userInterfaceInstance = createUserInterface()
    
    # call with patch
    with patch('builtins.print') as mock_print:
        userInterfaceInstance.divider()
        
        # check
        assert mock_print.call_count == 3


def test_showOptions():
    # setup
    userInterfaceInstance = createUserInterface()
    
    # call with patches
    with patch('builtins.print') as mock_print, \
         patch('builtins.input', return_value="1") as mock_input, \
         patch.object(userInterfaceInstance, 'lotsOfSpace') as mock_lots_of_space, \
         patch.object(userInterfaceInstance, 'divider') as mock_divider:
        
        result = userInterfaceInstance.showOptions("descriptor", ["option1", "option2"])
        
        # check
        assert result == "1"
        mock_lots_of_space.assert_called()
        assert mock_divider.call_count == 3
        mock_input.assert_called_with("\n> ")
