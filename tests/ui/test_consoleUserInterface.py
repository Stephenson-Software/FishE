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


def createConsoleUserInterface():
    currentPrompt = Prompt("What would you like to do?")
    player = Player()
    stats = Stats()
    timeService = TimeService(player, stats)
    return ConsoleUserInterface(currentPrompt, timeService, player)


def test_console_ui_initialization():
    # call
    ui = createConsoleUserInterface()

    # check
    assert ui.currentPrompt != None
    assert ui.player != None
    assert ui.timeService != None
    assert ui.times != None


def test_console_ui_lots_of_space():
    # setup
    ui = createConsoleUserInterface()
    
    # call with patch
    with patch('builtins.print') as mock_print:
        ui.lotsOfSpace()
        
        # check
        mock_print.assert_called_with("\n" * 20)


def test_console_ui_divider():
    # setup
    ui = createConsoleUserInterface()
    
    # call with patch
    with patch('builtins.print') as mock_print:
        ui.divider()
        
        # check
        assert mock_print.call_count == 3


def test_console_ui_cleanup():
    # setup
    ui = createConsoleUserInterface()
    
    # call - should not raise any errors
    ui.cleanup()
    
    # No assertions needed as cleanup doesn't do anything for console UI