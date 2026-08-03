import sys
import os
import json
import time
import threading
import urllib.error
import urllib.request

# Use the bare `ui.*`/`player.*` import style (matching production) so class
# identities line up with the runtime MRO; pytest.ini exposes both `.` and `src`.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from housing import housing
from ui import webUserInterface
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


def test_header_includes_max_energy():
    # check - the header exposes the current tier's cap alongside the raw
    # energy value, so the client can always show "X/Y" instead of just "X"
    ui = makeWebUI()
    header = ui._header()
    assert header["energy"] == ui.player.energy
    assert header["maxEnergy"] == housing.maxEnergy(ui.player)


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


def test_promptForNumber_marks_screen_numeric_and_parses():
    ui = makeWebUI()
    thread, box = runInThread(lambda: ui.promptForNumber("How much?"))
    waitForScreen(ui, "prompt")

    # the prompt is flagged numeric so the browser can constrain input
    assert ui.get_state()["screen"].get("numeric") is True

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


def test_showBusy_presents_the_message_without_consuming_input():
    # The pause has to reach the browser - before showBusy existed the message
    # went to the server's terminal and the page sat on the previous screen.
    ui = makeWebUI()
    thread, box = runInThread(lambda: ui.showBusy("Fishing...", 0.05))
    waitForScreen(ui, "busy")
    assert ui.get_state()["screen"]["message"] == "Fishing..."

    thread.join(timeout=2)
    # A stray submission during the pause is left in the queue for whatever the
    # game asks next, rather than being swallowed by the pause.
    ui.submit_input("1")
    assert ui._inputQueue.get(timeout=1) == "1"


def test_busy_screen_is_rendered_by_the_client():
    # The client only renders screen types it knows about, so a new type on the
    # server needs its branch on the page too.
    assert 'screen.type === "busy"' in webUserInterface.HTML_PAGE


def test_page_declares_a_mobile_viewport():
    # Without this, phone browsers lay the page out at ~980px wide and scale it
    # down, which renders every control too small to read or tap.
    assert (
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        in webUserInterface.HTML_PAGE
    )


def test_page_has_narrow_screen_styles():
    # Narrow-screen adjustments live in their own media query so the desktop
    # layout is untouched; the action buttons go full-width for easier tapping.
    page = webUserInterface.HTML_PAGE
    assert "@media (max-width: 600px)" in page
    narrow = page.split("@media (max-width: 600px)", 1)[1].split("</style>", 1)[0]
    assert "button.action { width: 100%" in narrow


def test_input_font_size_stays_at_least_16px():
    # iOS Safari zooms the page in when focusing an input smaller than 16px;
    # 1rem is 16px at the default root size, so it must not shrink.
    rule = webUserInterface.HTML_PAGE.split("\n  input {", 1)[1].split("}", 1)[0]
    assert "font-size: 1rem" in rule


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


def test_http_server_returns_404_for_unknown_get_path():
    ui = makeWebUI(start_server=True, port=0)
    try:
        host, port = ui.address
        base = "http://127.0.0.1:%d" % port

        try:
            urllib.request.urlopen(base + "/nonexistent", timeout=2)
            assert False, "expected HTTPError"
        except urllib.error.HTTPError as error:
            assert error.code == 404
    finally:
        ui.cleanup()


def test_http_server_returns_404_for_unknown_post_path():
    ui = makeWebUI(start_server=True, port=0)
    try:
        host, port = ui.address
        base = "http://127.0.0.1:%d" % port

        request = urllib.request.Request(
            base + "/nonexistent",
            data=b"{}",
            method="POST",
        )
        try:
            urllib.request.urlopen(request, timeout=2)
            assert False, "expected HTTPError"
        except urllib.error.HTTPError as error:
            assert error.code == 404
    finally:
        ui.cleanup()


def test_http_server_post_input_with_malformed_json_defaults_to_empty_value():
    # A malformed body (or one missing "value") must not crash the handler -
    # it should fall back to submitting an empty string, same as a body-less request.
    ui = makeWebUI(start_server=True, port=0)
    try:
        host, port = ui.address
        base = "http://127.0.0.1:%d" % port

        thread, box = runInThread(lambda: ui.promptForText("Your name?"))
        waitForScreen(ui, "prompt")

        request = urllib.request.Request(
            base + "/input",
            data=b"not valid json",
            method="POST",
        )
        urllib.request.urlopen(request, timeout=2).read()
        thread.join(timeout=2)
        assert box["result"] == ""
    finally:
        ui.cleanup()


def test_showOptions_publishes_the_reason_each_option_is_unavailable():
    # check - the browser needs the reason as data (not baked into the label)
    # so it can grey the button out and style the reason apart from the option
    ui = makeWebUI()
    thread, box = runInThread(
        lambda: ui.showOptions("The docks", ["Fish", "Go Home"], {1: "no energy"})
    )
    waitForScreen(ui, "options")

    screen = ui.get_state()["screen"]
    assert screen["options"] == ["Fish", "Go Home"]
    assert screen["unavailable"] == ["no energy", None]

    ui.submit_input("2")
    thread.join(timeout=2)
    assert box["result"] == "2"


def test_showOptions_always_publishes_an_unavailable_entry_per_option():
    # check - one code path in the client: the list is the same length as the
    # options even when everything is available
    ui = makeWebUI()
    thread, box = runInThread(lambda: ui.showOptions("Pick", ["Apple", "Banana"]))
    waitForScreen(ui, "options")

    assert ui.get_state()["screen"]["unavailable"] == [None, None]

    ui.submit_input("1")
    thread.join(timeout=2)


def test_showOptions_refuses_an_unavailable_choice():
    # check - the greyed-out button is disabled in the browser, but a response
    # for it (a stale click, a hand-rolled POST) is ignored rather than acted on
    ui = makeWebUI()
    thread, box = runInThread(
        lambda: ui.showOptions("The docks", ["Fish", "Go Home"], {1: "no energy"})
    )
    waitForScreen(ui, "options")

    ui.submit_input("1")  # greyed out -> ignored
    ui.submit_input("2")  # available
    thread.join(timeout=2)
    assert box["result"] == "2"
