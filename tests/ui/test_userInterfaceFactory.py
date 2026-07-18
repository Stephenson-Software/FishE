import pytest
import sys
import os

# Add src to the path so imports work correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from ui.enum.uiType import UIType
from ui.userInterfaceFactory import UserInterfaceFactory
from ui.consoleUserInterface import ConsoleUserInterface
from ui.pygameUserInterface import PygameUserInterface
from ui.webUserInterface import WebUserInterface
from player.player import Player
from prompt.prompt import Prompt
from stats.stats import Stats
from world.timeService import TimeService


def test_ui_type_enum():
    """Test UI type enum values"""
    assert UIType.CONSOLE.value == "console"
    assert UIType.PYGAME.value == "pygame"
    assert UIType.WEB.value == "web"


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


def test_factory_create_web_ui_default_bind(monkeypatch):
    """Test factory creates a web UI bound to 127.0.0.1:8000 by default,
    matching WebUserInterface's own defaults, when no FISHE_WEB_HOST/
    FISHE_WEB_PORT override is set."""
    monkeypatch.delenv("FISHE_WEB_HOST", raising=False)
    # Use an ephemeral port (0) so this test never fights a real listener on
    # 8000, but assert the *host* the factory chose defaults correctly.
    monkeypatch.setenv("FISHE_WEB_PORT", "0")
    currentPrompt = Prompt("What would you like to do?")
    player = Player()
    stats = Stats()
    timeService = TimeService(player, stats)

    ui = UserInterfaceFactory.create_user_interface(
        UIType.WEB, currentPrompt, timeService, player
    )
    try:
        assert isinstance(ui, WebUserInterface)
        assert ui.address[0] == "127.0.0.1"
        assert ui.currentPrompt == currentPrompt
        assert ui.timeService == timeService
        assert ui.player == player
    finally:
        ui.cleanup()


def test_factory_create_web_ui_honors_env_overrides(monkeypatch):
    """Test FISHE_WEB_HOST/FISHE_WEB_PORT override the web UI's bind address —
    the mechanism a container needs to make the server reachable from outside
    its own network namespace (e.g. FISHE_WEB_HOST=0.0.0.0)."""
    monkeypatch.setenv("FISHE_WEB_HOST", "0.0.0.0")
    monkeypatch.setenv("FISHE_WEB_PORT", "0")
    currentPrompt = Prompt("What would you like to do?")
    player = Player()
    stats = Stats()
    timeService = TimeService(player, stats)

    ui = UserInterfaceFactory.create_user_interface(
        UIType.WEB, currentPrompt, timeService, player
    )
    try:
        assert ui.address[0] == "0.0.0.0"
    finally:
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
