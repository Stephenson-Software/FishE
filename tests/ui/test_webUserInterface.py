import sys
import os
import json
import time
import threading
import urllib.error
import urllib.request

import pytest

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


def makeWebUI(start_server=False, port=0, endedScreenTimeoutSeconds=0.1):
    prompt = Prompt("What would you like to do?")
    player = Player()
    stats = Stats()
    timeService = TimeService(player, stats)
    # No browser polls these servers, so cleanup()'s wait for the ended screen
    # to be collected always runs to its timeout; the production default (two
    # seconds) would be paid by every test that starts one.
    return WebUserInterface(
        prompt,
        timeService,
        player,
        port=port,
        start_server=start_server,
        endedScreenTimeoutSeconds=endedScreenTimeoutSeconds,
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


def test_cleanup_publishes_the_ended_screen():
    # check - the run's last screen says the game is over, whether or not a
    # server is involved (the Pyodide front-end inherits this path)
    ui = makeWebUI()
    ui.cleanup()

    assert ui.get_state()["screen"] == {"type": "ended"}


def test_cleanup_holds_the_server_open_until_the_ended_screen_is_fetched():
    # The browser only learns the game finished on its next poll, so closing
    # the socket the instant the ended screen is published loses it: the page
    # would show "Lost connection" to a player who had just retired.
    ui = makeWebUI(start_server=True, port=0, endedScreenTimeoutSeconds=2.0)
    host, port = ui.address
    base = "http://127.0.0.1:%d" % port

    thread, box = runInThread(ui.cleanup)
    try:
        waitForScreen(ui, "ended")
        # Still serving: the ended screen has not been collected yet.
        assert thread.is_alive()
        state = json.loads(urllib.request.urlopen(base + "/state", timeout=2).read())
        assert state["screen"] == {"type": "ended"}
    finally:
        thread.join(timeout=3)

    # check - once the page has it, the server is closed rather than left running
    assert not thread.is_alive()
    assert ui.address is None


def test_cleanup_stops_waiting_when_nothing_is_listening():
    # A closed tab (or a game driven by anything other than a browser) never
    # fetches the ended screen, so the wait has to end on its own.
    ui = makeWebUI(start_server=True, port=0, endedScreenTimeoutSeconds=0.2)

    startTime = time.time()
    ui.cleanup()
    elapsed = time.time() - startTime

    assert 0.2 <= elapsed < 2.0
    assert ui.address is None


def test_record_state_delivered_keeps_the_highest_version_seen():
    # Two polls can overlap, and the older one can finish last; the newer
    # screen must not be reported as uncollected because of it.
    ui = makeWebUI()
    ui._present({"type": "dialogue", "text": "Caught a fish!"})
    version = ui.get_state()["version"]

    ui.record_state_delivered(version)
    ui.record_state_delivered(version - 1)

    assert ui._awaitScreenDelivery(timeout=0) is True


def test_waiting_for_delivery_reports_an_uncollected_screen():
    # check - a screen published after the last delivery is not treated as seen
    ui = makeWebUI()
    ui.record_state_delivered(ui.get_state()["version"])
    ui._present({"type": "dialogue", "text": "Caught a fish!"})

    assert ui._awaitScreenDelivery(timeout=0) is False


def test_client_stops_polling_once_the_game_has_ended():
    # check - the server is gone by the time the page renders the ended
    # screen, so the poll loop stops rather than failing every 300ms for the
    # rest of the tab's life
    page = webUserInterface.htmlPage()

    assert 'state.screen.type === "ended"' in page


def test_taken_port_is_explained_rather_than_traced():
    # The front-end does not exist yet when the bind fails, so there is no
    # showDialogue to say it through - a second copy of the game would
    # otherwise reach the player as an errno raised from inside http.server.
    running = makeWebUI(start_server=True)
    port = running.address[1]
    try:
        with pytest.raises(OSError) as raised:
            makeWebUI(start_server=True, port=port)
    finally:
        running.cleanup()

    message = str(raised.value)
    assert "FISHE_WEB_PORT" in message
    assert "already listening" in message
    assert str(port) in message


def test_bound_address_is_announced_once_the_server_is_listening(capsys):
    # The entry point cannot say this: building FishE starts the server and
    # then blocks in the save-file manager, so the announcement has to come
    # from here - and it has to name the port the socket actually got, which
    # a caller that asked for an ephemeral one could not have known.
    ui = makeWebUI(start_server=True)
    try:
        boundPort = ui.address[1]
    finally:
        ui.cleanup()

    printed = capsys.readouterr().out
    assert f"http://127.0.0.1:{boundPort}/" in printed
    assert "Open that URL in your browser to play" in printed


def test_nothing_is_announced_when_no_server_was_started(capsys):
    # check - the Pyodide front-end subclasses this one with start_server=False
    # and has no address to announce; a URL there would name nothing at all
    makeWebUI(start_server=False)

    assert capsys.readouterr().out == ""


def test_nothing_is_announced_when_the_port_is_already_taken(capsys):
    # check - a bind that fails is not preceded by an address that will never
    # answer, which is what announcing before binding used to produce
    running = makeWebUI(start_server=True)
    port = running.address[1]
    capsys.readouterr()  # discard the running server's own announcement
    try:
        with pytest.raises(OSError):
            makeWebUI(start_server=True, port=port)
    finally:
        running.cleanup()

    assert "http://" not in capsys.readouterr().out


def test_address_defaults_to_loopback_and_the_documented_port(monkeypatch):
    # check - with neither variable set, the resolver hands back the one
    # default that the constructor and the factory branch both use
    monkeypatch.delenv("FISHE_WEB_HOST", raising=False)
    monkeypatch.delenv("FISHE_WEB_PORT", raising=False)

    assert webUserInterface.resolveAddressFromEnvironment() == (
        webUserInterface.DEFAULT_HOST,
        webUserInterface.DEFAULT_PORT,
    )
    assert (webUserInterface.DEFAULT_HOST, webUserInterface.DEFAULT_PORT) == (
        "127.0.0.1",
        8000,
    )


def test_address_is_taken_from_the_environment_when_set(monkeypatch):
    # check - FISHE_WEB_HOST=0.0.0.0 is how the game is reached from outside
    # its own container, and the port arrives as an int ready to bind
    monkeypatch.setenv("FISHE_WEB_HOST", "0.0.0.0")
    monkeypatch.setenv("FISHE_WEB_PORT", "9123")

    assert webUserInterface.resolveAddressFromEnvironment() == ("0.0.0.0", 9123)


def test_misspelled_port_names_the_variable_it_came_from(monkeypatch):
    # check - the value is converted before anything is printed or bound, and
    # the complaint names what the player would have to change
    monkeypatch.setenv("FISHE_WEB_PORT", "80801x")

    with pytest.raises(ValueError, match="FISHE_WEB_PORT"):
        webUserInterface.resolveAddressFromEnvironment()
