import pytest
import sys
import os

# Add src to the path so imports work correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from ui.enum.uiType import UIType
from ui.userInterfaceFactory import UserInterfaceFactory
from ui.consoleUserInterface import ConsoleUserInterface
from ui.pygameUserInterface import PygameUserInterface
from player.player import Player
from prompt.prompt import Prompt
from stats.stats import Stats
from world.timeService import TimeService


def test_ui_type_enum():
    """Test UI type enum values"""
    assert UIType.CONSOLE.value == "console"
    assert UIType.PYGAME.value == "pygame"


def test_factory_create_console_ui():
    """Test factory creates console UI correctly"""
    # setup
    currentPrompt = Prompt("What would you like to do?")
    player = Player()
    stats = Stats()
    timeService = TimeService(player, stats)
    
    # call
    ui = UserInterfaceFactory.create_user_interface(
        UIType.CONSOLE, currentPrompt, timeService, player
    )
    
    # check
    assert isinstance(ui, ConsoleUserInterface)
    assert ui.currentPrompt == currentPrompt
    assert ui.timeService == timeService
    assert ui.player == player


def test_factory_create_pygame_ui():
    """Test factory creates pygame UI correctly"""
    # setup
    currentPrompt = Prompt("What would you like to do?")
    player = Player()
    stats = Stats()
    timeService = TimeService(player, stats)
    
    # call
    ui = UserInterfaceFactory.create_user_interface(
        UIType.PYGAME, currentPrompt, timeService, player
    )
    
    # check
    assert isinstance(ui, PygameUserInterface)
    assert ui.currentPrompt == currentPrompt
    assert ui.timeService == timeService
    assert ui.player == player
    
    # cleanup
    ui.cleanup()


def test_factory_invalid_ui_type():
    """Test factory raises error for invalid UI type"""
    currentPrompt = Prompt("What would you like to do?")
    player = Player()
    stats = Stats()
    timeService = TimeService(player, stats)
    
    with pytest.raises(ValueError):
        UserInterfaceFactory.create_user_interface(
            "invalid", currentPrompt, timeService, player
        )