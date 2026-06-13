import sys
import os

# Bare `ui.*`/`player.*` imports (like the factory test) so pygame is exercised
# directly; run headless under SDL_VIDEODRIVER=dummy (set by CI / the test cmd).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from ui.pygameUserInterface import PygameUserInterface
from player.player import Player
from prompt.prompt import Prompt
from stats.stats import Stats
from world.timeService import TimeService


def makeUI():
    player = Player()
    stats = Stats()
    timeService = TimeService(player, stats)
    prompt = Prompt("What would you like to do?")
    return PygameUserInterface(prompt, timeService, player)


def test_handle_resize_clamps_below_minimum():
    # a resize smaller than the minimum window is clamped up to the minimum
    ui = makeUI()
    try:
        ui._handle_resize(100, 100)
        assert ui.width == ui.min_width
        assert ui.height == ui.min_height
    finally:
        ui.cleanup()


def test_handle_resize_accepts_larger_window():
    # a resize above the minimum is honored exactly
    ui = makeUI()
    try:
        ui._handle_resize(1024, 768)
        assert ui.width == 1024
        assert ui.height == 768
    finally:
        ui.cleanup()


def test_update_fonts_keeps_fonts_usable_when_tiny():
    # even at a tiny window the min-size guard keeps the fonts renderable
    ui = makeUI()
    try:
        ui.width, ui.height = 200, 150
        ui._update_fonts()
        for font in (ui.font_large, ui.font_medium, ui.font_small):
            assert font is not None
            surface = font.render("Hi", True, ui.WHITE)
            assert surface.get_width() > 0 and surface.get_height() > 0
    finally:
        ui.cleanup()


# --- interactive input primitives (events injected via patched pygame.event.get) ---
import contextlib  # noqa: E402
from types import SimpleNamespace  # noqa: E402
from unittest.mock import patch  # noqa: E402

import pygame  # noqa: E402


def keydown(key=0, unicode=""):
    return SimpleNamespace(type=pygame.KEYDOWN, key=key, unicode=unicode)


@contextlib.contextmanager
def injected_events(events):
    # Feed the given events to the UI's event loop and stub out the per-frame
    # display flip / clock so the loop runs without a real frame delay.
    with patch("ui.pygameUserInterface.pygame.event.get", return_value=events), patch(
        "ui.pygameUserInterface.pygame.display.flip"
    ), patch("ui.pygameUserInterface.pygame.time.Clock"):
        yield


def test_showDialogue_returns_on_keypress():
    ui = makeUI()
    try:
        ui.currentPrompt.text = "before"
        with injected_events([keydown()]):
            ui.showDialogue("some text")
        assert ui.currentPrompt.text == "What would you like to do?"
    finally:
        ui.cleanup()


def test_timedKeyPress_returns_nonnegative_seconds():
    ui = makeUI()
    try:
        with injected_events([keydown()]):
            reaction = ui.timedKeyPress("React!")
        assert isinstance(reaction, float)
        assert reaction >= 0.0
    finally:
        ui.cleanup()


def test_promptForText_collects_typed_characters():
    ui = makeUI()
    try:
        events = [
            keydown(unicode="h"),
            keydown(unicode="i"),
            keydown(key=pygame.K_RETURN),
        ]
        with injected_events(events):
            result = ui.promptForText("Name?")
        assert result == "hi"
    finally:
        ui.cleanup()


def test_promptForText_handles_backspace():
    ui = makeUI()
    try:
        events = [
            keydown(unicode="a"),
            keydown(unicode="b"),
            keydown(key=pygame.K_BACKSPACE),
            keydown(key=pygame.K_RETURN),
        ]
        with injected_events(events):
            result = ui.promptForText("Name?")
        assert result == "a"
    finally:
        ui.cleanup()


def test_showOptions_number_key_selects_directly():
    ui = makeUI()
    try:
        with injected_events([keydown(key=pygame.K_2)]):
            choice = ui.showOptions("Pick", ["A", "B", "C"])
        assert choice == "2"
    finally:
        ui.cleanup()


def test_showOptions_arrow_then_enter_selects():
    ui = makeUI()
    try:
        # down moves the highlight from option 1 to option 2, Enter confirms it
        with injected_events([keydown(key=pygame.K_DOWN), keydown(key=pygame.K_RETURN)]):
            choice = ui.showOptions("Pick", ["A", "B", "C"])
        assert choice == "2"
    finally:
        ui.cleanup()


def test_showOptions_ignores_out_of_range_number():
    ui = makeUI()
    try:
        # "9" exceeds the 2 options and is ignored; "1" then selects
        with injected_events([keydown(key=pygame.K_9), keydown(key=pygame.K_1)]):
            choice = ui.showOptions("Pick", ["A", "B"])
        assert choice == "1"
    finally:
        ui.cleanup()
