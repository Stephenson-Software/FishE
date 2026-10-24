"""setPicture across FishE's four front-ends (RFC 0025): the console shows
nothing, the two web front-ends carry the picture on every screen and hand
the browser its bytes, and pygame draws it above the menu."""

import json
import os
import sys
import urllib.error
import urllib.request

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pygame  # noqa: E402

from player.player import Player  # noqa: E402
from prompt.prompt import Prompt  # noqa: E402
from stats.stats import Stats  # noqa: E402
from ui import pygameUserInterface  # noqa: E402
from ui.pygameUserInterface import PygameUserInterface  # noqa: E402
from ui.pyodideUserInterface import (  # noqa: E402
    PyodideUserInterface,
    SharedArrayBufferBridge,
)
from ui.webUserInterface import WebUserInterface  # noqa: E402
from world.timeService import TimeService  # noqa: E402

from test_pyodideUserInterface import FakeJs, installFakeJs, restoreJs  # noqa: E402

REPOSITORY_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
DOCKS_ALT = "The docks at eight in the morning."


def gameObjects():
    player = Player()
    return Prompt("What would you like to do?"), TimeService(player, Stats()), player


@pytest.fixture
def atRepositoryRoot(monkeypatch):
    # pictures/ is read relative to where the game runs, like schemas/.
    monkeypatch.chdir(REPOSITORY_ROOT)


# --- the contract --------------------------------------------------------


def test_setPicture_is_sticky_until_cleared_and_needs_alt_text():
    ui = WebUserInterface(*gameObjects(), start_server=False)
    ui.setPicture("docks", DOCKS_ALT)
    assert ui.picture() == {"key": "docks", "alt": DOCKS_ALT}
    with pytest.raises(ValueError):
        ui.setPicture("shop")
    with pytest.raises(ValueError):
        ui.setPicture("../docks", DOCKS_ALT)
    ui.setPicture(None)
    assert ui.picture() is None


# --- server-backed web ---------------------------------------------------


def test_web_screens_carry_the_picture_key_and_alt_not_the_image():
    ui = WebUserInterface(*gameObjects(), start_server=False)
    ui.setPicture("docks", DOCKS_ALT)
    ui._present({"type": "options", "descriptor": "Docks", "options": []})
    assert ui.get_state()["screen"]["picture"] == {"key": "docks", "alt": DOCKS_ALT}


def test_web_server_serves_a_picture_and_404s_anything_else(atRepositoryRoot):
    ui = WebUserInterface(*gameObjects(), port=0, endedScreenTimeoutSeconds=0.1)
    try:
        base = "http://127.0.0.1:%d" % ui.address[1]
        response = urllib.request.urlopen(base + "/picture/docks", timeout=2)
        assert response.headers["Content-Type"] == "image/png"
        assert response.read()[:8] == b"\x89PNG\r\n\x1a\n"
        for path in ("/picture/nowhere", "/picture/..%2Fschemas%2Fplayer"):
            with pytest.raises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(base + path, timeout=2)
            assert error.value.code == 404, path
    finally:
        ui.cleanup()


# --- Pyodide -------------------------------------------------------------


class PictureJs(FakeJs):
    def __init__(self):
        super().__init__()
        self.pictures = []

    def sendPicture(self, key):
        self.pictures.append(key)


def test_pyodide_hands_each_picture_over_once_before_the_screen_naming_it():
    js = PictureJs()
    previous = installFakeJs(js)
    try:
        ui = PyodideUserInterface(
            *gameObjects(), bridge=SharedArrayBufferBridge(js=js), pollIntervalSeconds=0
        )
        ui.setPicture("docks", DOCKS_ALT)
        ui._present({"type": "options", "descriptor": "Docks", "options": []})
        ui._present({"type": "dialogue", "text": "Salty."})
        assert js.pictures == ["docks"]
        screen = json.loads(js.posted[-1])["screen"]
        assert screen["picture"] == {"key": "docks", "alt": DOCKS_ALT}
    finally:
        restoreJs(previous)


# --- pygame --------------------------------------------------------------


@pytest.fixture
def pygameUI(atRepositoryRoot):
    ui = PygameUserInterface(*gameObjects())
    try:
        yield ui
    finally:
        ui.cleanup()


def test_pygame_draws_no_picture_until_one_is_set(pygameUI):
    assert pygameUI._pictureSurface() is None


def test_pygame_loads_the_picture_once_and_keeps_it(pygameUI, monkeypatch):
    pygameUI.setPicture("docks", DOCKS_ALT)
    first = pygameUI._pictureSurface()
    assert first is not None and first.get_size() == (640, 360)
    monkeypatch.setattr(
        pygame.image, "load", lambda path: pytest.fail("loaded twice: " + path)
    )
    assert pygameUI._pictureSurface() is first


def test_pygame_plays_on_as_text_when_a_picture_is_missing(pygameUI):
    pygameUI.setPicture("nowhere", "Nothing to see.")
    assert pygameUI._pictureSurface() is None
    pygameUI._draw_game_screen("Docks", ["Fish"])


def test_pygame_scales_the_picture_to_the_window_without_stretching(pygameUI):
    width, height = pygameUI._pictureSize((640, 360))
    assert height <= pygameUI.height * pygameUserInterface.PICTURE_MAX_HEIGHT_FRACTION
    assert width <= pygameUI._textWidth()
    assert abs(width / height - 640 / 360) < 0.02


def test_pygame_draws_the_picture_above_the_menu(pygameUI):
    pygameUI.setPicture("docks", DOCKS_ALT)
    pygameUI._draw_game_screen("You breathe in the fresh air. Salty.", ["Fish"])
    # The window and its height are the whole window again afterwards.
    assert pygameUI.screen.get_size() == (pygameUI.width, pygameUI.height)
    width, height = pygameUI._pictureSize((640, 360))
    top = int(pygameUI.height * 0.02)
    centre = pygameUI.screen.get_at((pygameUI.width // 2, top + height // 2))
    assert centre[:3] != (0, 0, 0)
