import sys
import os

# Bare `ui.*`/`player.*` imports (like the factory test) so pygame is exercised
# directly; run headless under SDL_VIDEODRIVER=dummy (set by CI / the test cmd).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from housing import housing
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


def statusText(ui):
    # the status block groups several stats per row, so assertions look for an
    # entry anywhere in the block rather than as a row of its own
    return " | ".join(ui._statusLines())


def test_statusLines_shows_energy_cap():
    # check - the status block shows "current/cap", not just the raw value
    ui = makeUI()
    try:
        expected = "Energy: %d/%d" % (ui.player.energy, housing.maxEnergy(ui.player))
        assert expected in statusText(ui)
    finally:
        ui.cleanup()


def test_statusLines_shows_location_and_goal_when_set():
    # parity with the console/web front-ends: both header fields the game loop
    # sets appear in the status block
    ui = makeUI()
    try:
        ui.currentLocationName = "Docks"
        ui.goalProgress = "$20 / $10000"
        assert "Location: Docks" in statusText(ui)
        assert "Goal: $20 / $10000" in statusText(ui)
    finally:
        ui.cleanup()


def test_statusLines_hides_location_and_goal_when_unset():
    # empty header fields hide their entry, same as the other two front-ends
    ui = makeUI()
    try:
        assert "Location:" not in statusText(ui)
        assert "Goal:" not in statusText(ui)
    finally:
        ui.cleanup()


def test_statusLines_stays_compact_when_everything_is_shown():
    # the whole header fits in a few rows, leaving the option list room
    ui = makeUI()
    try:
        ui.currentLocationName = "Docks"
        ui.goalProgress = "$20 / $10000"
        ui.player.operatorMode = True
        lines = ui._statusLines()
        assert len(lines) == 3
        assert "[OPERATOR MODE]" in statusText(ui)
        for line in lines:
            assert ui.font_medium.size(line)[0] <= ui._textWidth()
    finally:
        ui.cleanup()


def test_statusLines_formats_money_to_two_decimals():
    # a fractional balance (a small bank withdrawal, say) is rounded for display
    # rather than shown as a raw float
    ui = makeUI()
    try:
        ui.player.money = 20 + 0.01 + 0.02
        assert "Money: $20.03" in statusText(ui)
    finally:
        ui.cleanup()


def test_gameScreenLayout_keeps_a_full_menu_on_screen():
    # the docks menu (7 options) with every header row and a wrapped prompt is
    # the busiest screen the game builds - all of it has to fit the window
    ui = makeUI()
    try:
        layout = ui._gameScreenLayout(3, 2, 7)
        assert layout["optionsY"] + 7 * layout["optionHeight"] <= ui.height
        # both instruction lines sit below the options and inside the window
        assert layout["instructionsY"] >= layout["optionsY"]
        assert layout["instructionsY"] + ui.height * 0.04 <= ui.height
    finally:
        ui.cleanup()


def test_gameScreenLayout_keeps_roomy_option_rows_when_there_is_space():
    # a short menu is unaffected: rows keep the full 6%-of-height size
    ui = makeUI()
    try:
        layout = ui._gameScreenLayout(3, 1, 3)
        assert layout["optionHeight"] == max(25, ui.height * 0.06)
    finally:
        ui.cleanup()


def test_gameScreenLayout_never_shrinks_options_below_the_font():
    # rows shrink to make room, but not so far that they overlap each other
    ui = makeUI()
    try:
        layout = ui._gameScreenLayout(3, 6, 20)
        assert layout["optionHeight"] >= ui.font_medium.get_linesize()
    finally:
        ui.cleanup()


def test_gameScreenLayout_shifts_blocks_down_as_the_prompt_wraps():
    # every block below the prompt moves down by exactly the added lines
    ui = makeUI()
    try:
        oneLine = ui._gameScreenLayout(3, 1, 5)
        threeLines = ui._gameScreenLayout(3, 3, 5)
        assert threeLines["promptY"] == oneLine["promptY"]
        assert threeLines["optionsY"] - oneLine["optionsY"] == 2 * oneLine["lineHeight"]
    finally:
        ui.cleanup()


def test_wrapText_keeps_every_line_within_the_width():
    # a line too wide for the window is broken into lines that each fit
    ui = makeUI()
    try:
        maxWidth = ui._textWidth()
        text = "You reel in a fish and the whole village hears about it. " * 5
        lines = ui._wrapText(text, ui.font_medium, maxWidth)
        assert len(lines) > 1
        for line in lines:
            assert ui.font_medium.size(line)[0] <= maxWidth
    finally:
        ui.cleanup()


def test_wrapText_preserves_newlines_and_blank_lines():
    # pygame's render ignores "\n", so the wrap has to turn them into real lines
    ui = makeUI()
    try:
        lines = ui._wrapText("Total Fish Caught: 3\n\nMilestones:", ui.font_medium, 700)
        assert lines == ["Total Fish Caught: 3", "", "Milestones:"]
    finally:
        ui.cleanup()


def test_wrapText_breaks_a_word_wider_than_the_window():
    # word wrapping can't help a single over-wide word, so it is split by
    # character instead of being clipped at the window edge
    ui = makeUI()
    try:
        lines = ui._wrapText("x" * 200, ui.font_medium, 200)
        assert len(lines) > 1
        assert "".join(lines) == "x" * 200
        for line in lines:
            assert ui.font_medium.size(line)[0] <= 200
    finally:
        ui.cleanup()


def test_wrapText_leaves_short_text_alone():
    ui = makeUI()
    try:
        assert ui._wrapText("Slot 1 deleted.", ui.font_medium, ui._textWidth()) == [
            "Slot 1 deleted."
        ]
    finally:
        ui.cleanup()


def test_dialogueScrollBounds_reports_scrollable_overflow():
    # more lines than fit leaves room to scroll; a short block does not
    ui = makeUI()
    try:
        visible, maxScroll = ui._dialogueScrollBounds(500)
        assert visible >= 1
        assert maxScroll == 500 - visible
        assert ui._dialogueScrollBounds(1)[1] == 0
    finally:
        ui.cleanup()


def test_dialogueHint_mentions_scrolling_only_when_needed():
    ui = makeUI()
    try:
        assert ui._dialogueHint(3, 0, 20) == "Press any key to continue"
        hint = ui._dialogueHint(60, 5, 20)
        assert "UP/DOWN" in hint
        assert "(6-25 of 60)" in hint
    finally:
        ui.cleanup()


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


@contextlib.contextmanager
def injected_event_frames(frames):
    # Like injected_events, but each frame of the loop gets its own event list -
    # needed for keys that don't end the loop (scrolling a dialogue).
    with patch("ui.pygameUserInterface.pygame.event.get", side_effect=frames), patch(
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


def test_showDialogue_scrolls_a_block_taller_than_the_window():
    # DOWN scrolls a too-tall block instead of dismissing it; any other key
    # dismisses it, so the drawn window moves down a line before continuing
    ui = makeUI()
    try:
        text = "\n".join("Line %d" % i for i in range(100))
        drawn = []
        with patch.object(ui, "_draw_dialogue", lambda *args: drawn.append(args)):
            with injected_event_frames(
                [
                    [keydown(key=pygame.K_DOWN)],
                    [keydown(key=pygame.K_DOWN)],
                    [keydown()],
                ]
            ):
                ui.showDialogue(text)
        scrollOffsets = [args[1] for args in drawn]
        assert scrollOffsets == [1, 2, 2]
    finally:
        ui.cleanup()


def test_showDialogue_does_not_scroll_past_the_last_line():
    # UP at the top and DOWN at the bottom are both clamped
    ui = makeUI()
    try:
        text = "\n".join("Line %d" % i for i in range(3))
        drawn = []
        with patch.object(ui, "_draw_dialogue", lambda *args: drawn.append(args)):
            with injected_event_frames(
                [[keydown(key=pygame.K_UP)], [keydown(key=pygame.K_DOWN)], [keydown()]]
            ):
                ui.showDialogue(text)
        # the whole block fits, so there is nowhere to scroll to
        assert [args[1] for args in drawn] == [0, 0, 0]
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


def test_draw_game_screen_handles_a_prompt_that_needs_wrapping():
    # the goal announcement is appended to the prompt and is wider than the
    # window on one line - drawing it wraps rather than raising or clipping
    ui = makeUI()
    try:
        ui.currentLocationName = "Docks"
        ui.goalProgress = "$10000 / $10000"
        ui.currentPrompt.text = (
            "What would you like to do?  [GOAL REACHED! You've built your fortune "
            "of $10000! Keep fishing, or retire from the Home menu.]"
        )
        assert (
            len(ui._wrapText(ui.currentPrompt.text, ui.font_medium, ui._textWidth()))
            > 1
        )
        ui._draw_game_screen("The Docks", ["Cast a line", "Go home"])
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
        with injected_events(
            [keydown(key=pygame.K_DOWN), keydown(key=pygame.K_RETURN)]
        ):
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
