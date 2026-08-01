import json
import os
import queue
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from ui.baseUserInterface import BaseUserInterface
from prompt.prompt import Prompt
from player.player import Player
from world.timeService import TimeService
from housing import housing


# The browser client (renderer + styles) is shared verbatim with the Pyodide
# front-end, which serves the same two files from web/. Keeping one copy is what
# stops a screen type from being handled in one web front-end but not the other.
# They are inlined into the page below rather than served as separate routes so
# the server stays a two-route affair and the page needs a single request.
WEB_ASSET_DIRECTORY = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "web")
)


def _readWebAsset(name):
    """Read a shared browser-client file from web/, or explain why it could not."""
    path = os.path.join(WEB_ASSET_DIRECTORY, name)
    try:
        with open(path, "r", encoding="utf-8") as assetFile:
            return assetFile.read()
    except OSError as e:
        raise RuntimeError(
            f"FishE's web front-end could not read its browser client "
            f"'{name}' (looked in {path}): {e}. That file ships in the "
            f"repository's web/ directory, alongside src/. Run the game from a "
            f"complete checkout, or — if this is a container image — make sure "
            f"the image copies web/ in as well as src/."
        ) from e


CLIENT_CSS = _readWebAsset("client.css")
CLIENT_JS = _readWebAsset("client.js")


# The single-page client. It polls /state and renders whatever screen the game
# is currently waiting on, posting the player's response to /input. Served as-is
# (no templating); it talks to the server via relative URLs.
HTML_PAGE = (
    """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FishE</title>
<style>
"""
    + CLIENT_CSS
    + """</style>
</head>
<body>
<h2>FishE <span class="tagline">— fish a seaside village and build a fortune of $10,000</span></h2>
<div id="app">Connecting&hellip;</div>
<p class="controls">Tip: click an option or press its number key (1-9). Enter or Space continues.</p>
<script>
"""
    + CLIENT_JS
    + """
// Transport: this front-end runs the game on a server, so responses are POSTed
// and new screens are discovered by polling. (The Pyodide front-end swaps this
// block for a Worker/SharedArrayBuffer transport and shares everything above.)
FisheClient.init(function (value) {
  fetch("/input", { method: "POST", body: JSON.stringify({ value: value }) });
});
let version = -1;
let failures = 0;
async function poll() {
  try {
    const response = await fetch("/state");
    const state = await response.json();
    const recovered = failures >= 5;
    failures = 0;
    if (recovered) version = -1;  // force a re-render to clear the disconnect banner
    if (state.version !== version) { version = state.version; FisheClient.render(state.screen); }
  } catch (e) {
    failures++;
    // Don't clobber the intentional "game ended" screen with a scary banner.
    const screen = FisheClient.getCurrentScreen();
    if (failures === 5 && !(screen && screen.type === "ended")) {
      FisheClient.renderDisconnected();
    }
  }
  setTimeout(poll, 300);
}
poll();
</script>
</body>
</html>
"""
)


def _makeRequestHandler(ui):
    """Build a request handler bound to a specific WebUserInterface instance."""

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path in ("/", "/index.html"):
                self._send(200, "text/html; charset=utf-8", HTML_PAGE.encode("utf-8"))
            elif self.path.startswith("/state"):
                body = json.dumps(ui.get_state()).encode("utf-8")
                self._send(200, "application/json", body)
            else:
                self._send(404, "text/plain", b"Not found")

        def do_POST(self):
            if self.path.startswith("/input"):
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length) if length else b"{}"
                try:
                    value = json.loads(raw or b"{}").get("value", "")
                except (ValueError, TypeError):
                    value = ""
                ui.submit_input(value)
                self._send(200, "application/json", b"{}")
            else:
                self._send(404, "text/plain", b"Not found")

        def _send(self, status, contentType, body):
            self.send_response(status)
            self.send_header("Content-Type", contentType)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass  # keep the game's stdout clean

    return _Handler


# @author Daniel McCoy Stephenson
class WebUserInterface(BaseUserInterface):
    """A browser-based front-end for FishE.

    The synchronous game loop is unchanged: each input primitive publishes the
    current screen and blocks until the browser submits a response, coordinated
    through a thread-safe rendezvous. A small stdlib HTTP server (run in a daemon
    thread) serves the screen state (GET /state) and the page (GET /), and
    accepts the player's response (POST /input)."""

    def __init__(
        self,
        currentPrompt: Prompt,
        timeService: TimeService,
        player: Player,
        host="127.0.0.1",
        port=8000,
        start_server=True,
    ):
        super().__init__(currentPrompt, timeService, player)
        self._lock = threading.Lock()
        self._screen = {"type": "loading"}
        self._version = 0
        self._inputQueue = queue.Queue()
        self._server = None
        if start_server:
            self._server = ThreadingHTTPServer((host, port), _makeRequestHandler(self))
            self._server.daemon_threads = True
            threading.Thread(target=self._server.serve_forever, daemon=True).start()

    @property
    def address(self):
        """The (host, port) the server is bound to, or None if not started."""
        return self._server.server_address if self._server else None

    # --- web rendezvous ---------------------------------------------------
    def get_state(self):
        """Snapshot of the current screen for the browser to render."""
        with self._lock:
            return {"version": self._version, "screen": self._screen}

    def submit_input(self, value):
        """Deliver the player's browser response to the waiting game thread."""
        self._inputQueue.put(value)

    # --- transport seams ---------------------------------------------------
    # Every screen below is built once and shared by both web front-ends; only
    # how a screen reaches the browser (_present) and how the response comes
    # back (_awaitInput) differ. PyodideUserInterface overrides just these two,
    # so a new screen type never has to be written twice.
    def _present(self, screen):
        with self._lock:
            self._screen = screen
            self._version += 1

    def _awaitInput(self):
        """Block until the browser submits a response, and return it."""
        return self._inputQueue.get()

    def _header(self):
        return {
            "day": self.timeService.day,
            "time": self.times[self.timeService.time],
            "money": float(self.player.money),
            "fish": self.player.fishCount,
            "energy": self.player.energy,
            "maxEnergy": housing.maxEnergy(self.player),
            "location": self.currentLocationName,
            "goal": self.goalProgress,
            "operator": self.player.operatorMode,
        }

    # --- BaseUserInterface primitives ------------------------------------
    def lotsOfSpace(self):
        # The browser renders a fresh screen each time; nothing to clear.
        pass

    def divider(self):
        pass

    def showOptions(self, descriptor, optionList):
        self._present(
            {
                "type": "options",
                "descriptor": descriptor,
                "prompt": self.currentPrompt.text,
                "options": list(optionList),
                "header": self._header(),
            }
        )
        valid = {str(i + 1) for i in range(len(optionList))}
        while True:
            choice = str(self._awaitInput())
            if choice in valid:
                return choice
            # ignore anything that isn't a listed option and keep waiting

    def showDialogue(self, text):
        self._present({"type": "dialogue", "text": text})
        self._awaitInput()
        self.currentPrompt.text = "What would you like to do?"

    def promptForText(self, promptText):
        self._present({"type": "prompt", "text": promptText})
        return str(self._awaitInput())

    def promptForNumber(self, promptText):
        # Flag the prompt as numeric so the browser can offer a numeric keyboard
        # and block submission of non-numbers (the base default can't say so).
        self._present({"type": "prompt", "text": promptText, "numeric": True})
        try:
            return float(self._awaitInput())
        except (ValueError, TypeError):
            return None

    def showBusy(self, message, seconds=1.0):
        # Published as its own screen type so the browser shows the message
        # instead of sitting on the previous screen. No input is consumed —
        # whatever the game presents next supersedes it.
        self._present({"type": "busy", "message": message})
        time.sleep(seconds)

    def timedKeyPress(self, message):
        self._present({"type": "timed", "message": message})
        startTime = time.time()
        self._awaitInput()
        return time.time() - startTime

    def cleanup(self):
        self._present({"type": "ended"})
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
