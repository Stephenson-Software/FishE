import json
import os
import sys
import tempfile

# Use the bare `ui.*`/`player.*` import style (matching production) so class
# identities line up with the runtime MRO; pytest.ini exposes both `.` and `src`.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from ui.baseUserInterface import BaseUserInterface
from ui.enum.uiType import UIType
from ui.pyodideUserInterface import (
    PyodideUserInterface,
    SharedArrayBufferBridge,
)
from ui.userInterfaceFactory import UserInterfaceFactory
from ui.webUserInterface import WebUserInterface
from player.player import Player
from prompt.prompt import Prompt
from stats.stats import Stats
from world.timeService import TimeService

RING_SIZE = 8192


class FakeAtomics:
    """The two Atomics operations the bridge uses, over a plain Python list."""

    @staticmethod
    def load(array, index):
        return array[index]

    @staticmethod
    def store(array, index, value):
        array[index] = value


class FakeJs:
    """Stand-in for Pyodide's `js` module and the globals game-worker.js sets.

    The ring buffer is modelled exactly as the real one: sabMeta[0] is the write
    index (advanced only by the browser), sabMeta[1] the read index (advanced
    only by Python), both monotonic and taken modulo the ring size.
    """

    def __init__(self, ringSize=RING_SIZE):
        self.Atomics = FakeAtomics
        self.sabMeta = [0, 0]
        self.sabData = bytearray(ringSize)
        self.sabRingSize = ringSize
        self.posted = []
        self.syncCallCount = 0

    def sendToMain(self, message):
        self.posted.append(message)

    def syncSaves(self):
        self.syncCallCount += 1

    # --- the browser side of the ring -------------------------------------
    def writePlayerInput(self, value):
        """Mirror of writeToRing() in web/index.html."""
        self._writeToRing(json.dumps({"type": "input", "value": value}))

    def _writeToRing(self, text):
        payload = (text + "\n").encode("utf-8")
        writeIndex = self.sabMeta[0]
        for offset, byte in enumerate(payload):
            self.sabData[(writeIndex + offset) % self.sabRingSize] = byte
        self.sabMeta[0] = writeIndex + len(payload)


def installFakeJs(js):
    """Register a fake `js` module the way Pyodide would, and undo it after."""
    previous = sys.modules.get("js")
    sys.modules["js"] = js
    return previous


def restoreJs(previous):
    if previous is None:
        sys.modules.pop("js", None)
    else:
        sys.modules["js"] = previous


@pytest.fixture
def fakeJs():
    js = FakeJs()
    previous = installFakeJs(js)
    try:
        yield js
    finally:
        restoreJs(previous)


def makePyodideUI(js):
    prompt = Prompt("What would you like to do?")
    player = Player()
    stats = Stats()
    timeService = TimeService(player, stats)
    return PyodideUserInterface(
        prompt,
        timeService,
        player,
        bridge=SharedArrayBufferBridge(js=js),
        # Nothing in these tests ever has to wait for input that isn't already
        # in the ring, so the poll interval only affects the failure case.
        pollIntervalSeconds=0,
    )


def lastScreen(js):
    return json.loads(js.posted[-1])["screen"]


# --- contract ------------------------------------------------------------


def test_pyodide_ui_implements_interface(fakeJs):
    ui = makePyodideUI(fakeJs)
    assert isinstance(ui, BaseUserInterface)
    # It shares WebUserInterface's screens rather than redefining them, which
    # is what keeps the two web front-ends from drifting apart.
    assert isinstance(ui, WebUserInterface)


def test_no_http_server_is_started(fakeJs):
    ui = makePyodideUI(fakeJs)
    assert ui.address is None


# --- screens out ---------------------------------------------------------


def test_screens_are_posted_to_the_main_thread(fakeJs):
    ui = makePyodideUI(fakeJs)
    fakeJs.writePlayerInput("1")

    ui.showOptions("The Docks", ["Fish", "Leave"])

    frame = json.loads(fakeJs.posted[-1])
    assert frame["type"] == "screen"
    assert frame["screen"]["type"] == "options"
    assert frame["screen"]["options"] == ["Fish", "Leave"]


def test_posted_screens_carry_the_shared_header(fakeJs):
    ui = makePyodideUI(fakeJs)
    fakeJs.writePlayerInput("1")

    ui.showOptions("The Docks", ["Fish"])

    header = lastScreen(fakeJs)["header"]
    assert header["day"] == ui.timeService.day
    assert header["maxEnergy"] >= header["energy"]


def test_present_still_updates_the_state_snapshot(fakeJs):
    # get_state() is inherited bookkeeping rather than a transport; keeping it
    # working means the screen contract is testable the same way for both
    # web front-ends.
    ui = makePyodideUI(fakeJs)
    fakeJs.writePlayerInput("")

    ui.showDialogue("You caught a fish!")

    assert ui.get_state()["screen"]["text"] == "You caught a fish!"


# --- input in ------------------------------------------------------------


def test_showOptions_round_trips_a_choice_through_the_ring(fakeJs):
    ui = makePyodideUI(fakeJs)
    fakeJs.writePlayerInput("2")

    assert ui.showOptions("The Docks", ["Fish", "Leave"]) == "2"


def test_showOptions_ignores_invalid_input_then_accepts_valid(fakeJs):
    ui = makePyodideUI(fakeJs)
    fakeJs.writePlayerInput("9")  # not one of the two options
    fakeJs.writePlayerInput("1")

    assert ui.showOptions("The Docks", ["Fish", "Leave"]) == "1"


def test_promptForText_round_trips_text_with_newlines(fakeJs):
    # The response is JSON-encoded precisely so text like this can't be read as
    # two ring messages and truncate the player's answer.
    ui = makePyodideUI(fakeJs)
    fakeJs.writePlayerInput("Salty\nDog")

    assert ui.promptForText("Name your business:") == "Salty\nDog"


def test_promptForNumber_parses_and_marks_the_screen_numeric(fakeJs):
    ui = makePyodideUI(fakeJs)
    fakeJs.writePlayerInput("12.5")

    assert ui.promptForNumber("How many?") == 12.5
    assert lastScreen(fakeJs)["numeric"] is True


def test_non_ascii_input_survives_the_ring(fakeJs):
    ui = makePyodideUI(fakeJs)
    fakeJs.writePlayerInput("Café du Quai")

    assert ui.promptForText("Name your business:") == "Café du Quai"


def test_messages_that_are_not_input_are_ignored(fakeJs):
    ui = makePyodideUI(fakeJs)
    fakeJs._writeToRing(json.dumps({"type": "resize", "w": 10}))
    fakeJs._writeToRing("not json at all")
    fakeJs.writePlayerInput("1")

    assert ui.showOptions("The Docks", ["Fish"]) == "1"


def test_submit_input_still_works_alongside_the_ring(fakeJs):
    ui = makePyodideUI(fakeJs)
    ui.submit_input("1")

    assert ui.showOptions("The Docks", ["Fish"]) == "1"


def test_ring_wraps_around_without_losing_a_message(fakeJs):
    # Push the indices near the end of the buffer so the next message straddles
    # the wrap point, which is where an off-by-one would show up.
    ui = makePyodideUI(fakeJs)
    fakeJs.sabMeta[0] = RING_SIZE - 4
    fakeJs.sabMeta[1] = RING_SIZE - 4
    fakeJs.writePlayerInput("Harbourmaster")

    assert ui.promptForText("Name?") == "Harbourmaster"


# --- independence from the server-backed front-end's files ---------------


def test_the_front_end_works_with_no_web_directory_on_disk(fakeJs, monkeypatch):
    """Regression: the Worker's filesystem has src/ but not web/client.*.

    web/client.js and web/client.css reach the browser over HTTP, so they are
    not on the filesystem the Python game sees. WebUserInterface reads them to
    build its own page, and PyodideUserInterface subclasses it — so reading
    them at import time made the game fail to start in a real browser with
    FileNotFoundError on /game/web/client.css. Nothing on this front-end's path
    may touch them.
    """
    from ui import webUserInterface

    monkeypatch.setattr(webUserInterface, "WEB_ASSET_DIRECTORY", "/no/such/directory")
    monkeypatch.setattr(webUserInterface, "_clientAssetCache", {})
    monkeypatch.setattr(webUserInterface, "_pageCache", {})

    ui = makePyodideUI(fakeJs)
    fakeJs.writePlayerInput("1")

    assert ui.showOptions("The Docks", ["Fish", "Leave"]) == "1"
    assert lastScreen(fakeJs)["options"] == ["Fish", "Leave"]


def test_the_server_backed_page_is_not_built_unless_it_is_asked_for(fakeJs):
    # The page is what needs those files; building it eagerly is what put the
    # read on every importer's path.
    from ui import webUserInterface

    webUserInterface._pageCache.clear()

    makePyodideUI(fakeJs)

    assert webUserInterface._pageCache == {}


# --- construction errors -------------------------------------------------


def test_bridge_outside_a_browser_explains_itself():
    previous = sys.modules.pop("js", None)
    try:
        with pytest.raises(RuntimeError) as error:
            SharedArrayBufferBridge()
    finally:
        restoreJs(previous)
    message = str(error.value)
    assert "browser" in message
    assert "UIType.CONSOLE" in message  # tells the player what to use instead


def test_bridge_without_worker_globals_names_what_is_missing(fakeJs):
    fakeJs.sendToMain = None
    with pytest.raises(RuntimeError) as error:
        SharedArrayBufferBridge(js=fakeJs)
    assert "sendToMain" in str(error.value)


# --- factory -------------------------------------------------------------


def test_factory_creates_the_pyodide_front_end(fakeJs):
    prompt = Prompt("What would you like to do?")
    player = Player()
    stats = Stats()
    timeService = TimeService(player, stats)

    ui = UserInterfaceFactory.create_user_interface(
        UIType.PYODIDE, prompt, timeService, player
    )

    assert isinstance(ui, PyodideUserInterface)


# --- end to end ----------------------------------------------------------


def test_a_game_played_in_the_browser_saves_into_browser_storage(fakeJs):
    """The whole point of this front-end, exercised against a real game.

    A save directory that only exists in the Worker's memory, a game booted
    through the Pyodide front-end, and a save that reaches the browser rather
    than stopping at the filesystem.
    """
    from fishE import FishE

    # Mirror of makeSyncSaves() in web/game-worker.js: walk the save directory
    # and hand the file map to the browser to store.
    browserStorage = {}

    with tempfile.TemporaryDirectory() as saveDirectory:

        def syncSaves():
            browserStorage.clear()
            for root, _dirs, files in os.walk(saveDirectory):
                for name in files:
                    path = os.path.join(root, name)
                    with open(path) as saveFile:
                        browserStorage[path] = saveFile.read()

        fakeJs.syncSaves = syncSaves

        previousSaveDirectory = os.environ.get("FISHE_SAVE_DIR")
        os.environ["FISHE_SAVE_DIR"] = saveDirectory
        try:
            # "Create New Save (Slot 1)" is the only option on a fresh install.
            fakeJs.writePlayerInput("1")
            game = FishE(interfaceType=UIType.PYODIDE)

            menu = json.loads(fakeJs.posted[0])["screen"]
            assert menu["descriptor"] == "FishE - Save File Manager"

            game.player.money = 4321
            game.save()
        finally:
            if previousSaveDirectory is None:
                os.environ.pop("FISHE_SAVE_DIR", None)
            else:
                os.environ["FISHE_SAVE_DIR"] = previousSaveDirectory

        playerSaves = [p for p in browserStorage if p.endswith("player.json")]
        assert len(playerSaves) == 1
        assert "slot_1" in playerSaves[0]
        assert json.loads(browserStorage[playerSaves[0]])["money"] == 4321


def test_quitting_ends_the_page_instead_of_raising(fakeJs):
    # "Quit" calls exit(), which in a tab has no process to end: the Worker
    # would report it as an error rather than the game finishing. The entry
    # point is exec'd here the same way web/game-worker.js runs it.
    entryPoint = os.path.join(
        os.path.dirname(__file__), "..", "..", "web", "pyodide_main.py"
    )

    with tempfile.TemporaryDirectory() as saveDirectory:
        previousSaveDirectory = os.environ.get("FISHE_SAVE_DIR")
        os.environ["FISHE_SAVE_DIR"] = saveDirectory
        try:
            # A fresh save directory offers "Create New Save (Slot 1)" then "Quit".
            fakeJs.writePlayerInput("2")
            with open(entryPoint) as entryPointFile:
                exec(compile(entryPointFile.read(), entryPoint, "exec"), {})
        finally:
            if previousSaveDirectory is None:
                os.environ.pop("FISHE_SAVE_DIR", None)
            else:
                os.environ["FISHE_SAVE_DIR"] = previousSaveDirectory

    assert lastScreen(fakeJs) == {"type": "ended"}
