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
