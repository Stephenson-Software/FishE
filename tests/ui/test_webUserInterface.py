import sys
import os
import json
import time
import threading
import urllib.request

# Use the bare `ui.*`/`player.*` import style (matching production) so class
# identities line up with the runtime MRO; pytest.ini exposes both `.` and `src`.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from ui.baseUserInterface import BaseUserInterface
from ui.webUserInterface import WebUserInterface
from player.player import Player
from prompt.prompt import Prompt
from stats.stats import Stats
from world.timeService import TimeService


def makeWebUI(start_server=False, port=0):
    prompt = Prompt("What would you like to do?")
    player = Player()
    stats = Stats()
    timeService = TimeService(player, stats)
    return WebUserInterface(
        prompt, timeService, player, port=port, start_server=start_server
    )


def runInThread(fn):
    box = {}
    thread = threading.Thread(target=lambda: box.__setitem__("result", fn()))
    thread.start()
    return thread, box


def waitForScreen(ui, screenType, timeout=2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if ui.get_state()["screen"].get("type") == screenType:
            return
        time.sleep(0.01)
    raise AssertionError("screen %r was never presented" % screenType)


def test_web_ui_implements_interface():
    # check - it is a BaseUserInterface and instantiable (all primitives present)
    assert issubclass(WebUserInterface, BaseUserInterface)
    ui = makeWebUI()
    assert ui.get_state()["screen"]["type"] == "loading"


def test_showOptions_round_trips_a_choice():
    ui = makeWebUI()
    thread, box = runInThread(lambda: ui.showOptions("Pick one", ["Apple", "Banana"]))

    waitForScreen(ui, "options")
    screen = ui.get_state()["screen"]
    assert screen["options"] == ["Apple", "Banana"]
    assert "header" in screen and "day" in screen["header"]

    ui.submit_input("2")
    thread.join(timeout=2)
    assert box["result"] == "2"


def test_showOptions_ignores_invalid_then_accepts_valid():
    ui = makeWebUI()
    thread, box = runInThread(lambda: ui.showOptions("Pick", ["Only"]))
    waitForScreen(ui, "options")

    ui.submit_input("9")  # not a listed option -> ignored
    ui.submit_input("1")  # valid
    thread.join(timeout=2)
    assert box["result"] == "1"


def test_promptForText_round_trips_text():
    ui = makeWebUI()
    thread, box = runInThread(lambda: ui.promptForText("Your name?"))
    waitForScreen(ui, "prompt")

    ui.submit_input("Gilbert")
    thread.join(timeout=2)
    assert box["result"] == "Gilbert"


def test_promptForNumber_uses_web_input():
    ui = makeWebUI()
    thread, box = runInThread(lambda: ui.promptForNumber("How much?"))
    waitForScreen(ui, "prompt")

    ui.submit_input("12.5")
    thread.join(timeout=2)
    assert box["result"] == 12.5


def test_showDialogue_waits_then_resets_prompt():
    ui = makeWebUI()
    ui.currentPrompt.text = "something"
    thread, box = runInThread(lambda: ui.showDialogue("Hello there"))
    waitForScreen(ui, "dialogue")

    assert ui.get_state()["screen"]["text"] == "Hello there"
    ui.submit_input("")
    thread.join(timeout=2)
    assert ui.currentPrompt.text == "What would you like to do?"


def test_timedKeyPress_returns_elapsed_seconds():
    ui = makeWebUI()
    thread, box = runInThread(lambda: ui.timedKeyPress("React!"))
    waitForScreen(ui, "timed")

    ui.submit_input("")
    thread.join(timeout=2)
    assert box["result"] >= 0.0


def test_http_server_serves_and_accepts_input():
    # Integration smoke test against a real ephemeral-port server.
    ui = makeWebUI(start_server=True, port=0)
    try:
        host, port = ui.address
        base = "http://127.0.0.1:%d" % port

        page = urllib.request.urlopen(base + "/", timeout=2).read().decode("utf-8")
        assert "FishE" in page

        state = json.loads(urllib.request.urlopen(base + "/state", timeout=2).read())
        assert "version" in state and "screen" in state

        # Present an options screen, then submit a choice over HTTP.
        thread, box = runInThread(lambda: ui.showOptions("Pick", ["A", "B"]))
        waitForScreen(ui, "options")
        request = urllib.request.Request(
            base + "/input",
            data=json.dumps({"value": "1"}).encode("utf-8"),
            method="POST",
        )
        urllib.request.urlopen(request, timeout=2).read()
        thread.join(timeout=2)
        assert box["result"] == "1"
    finally:
        ui.cleanup()
