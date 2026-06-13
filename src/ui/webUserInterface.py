import json
import queue
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from ui.baseUserInterface import BaseUserInterface
from prompt.prompt import Prompt
from player.player import Player
from world.timeService import TimeService


# The single-page client. It polls /state and renders whatever screen the game
# is currently waiting on, posting the player's response to /input. Served as-is
# (no templating); it talks to the server via relative URLs.
HTML_PAGE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>FishE</title>
<style>
  body { font-family: monospace; background: #0b1d2a; color: #e0f0ff;
         max-width: 680px; margin: 2rem auto; padding: 0 1rem; }
  .header { color: #7fb0d0; border-bottom: 1px solid #2a4a5a;
            padding-bottom: .5rem; margin-bottom: 1rem; }
  .descriptor { margin: 1rem 0; font-size: 1.1rem; }
  .prompt { color: #9fd0ff; margin: 1rem 0; }
  .dialogue { white-space: pre-wrap; margin: 1rem 0; line-height: 1.5; }
  button { display: block; width: 100%; text-align: left; margin: .3rem 0;
           padding: .6rem; background: #163345; color: #e0f0ff;
           border: 1px solid #2a4a5a; border-radius: 4px; cursor: pointer;
           font-family: monospace; font-size: 1rem; }
  button:hover { background: #1f4a63; }
  button.danger { background: #4a1620; border-color: #7a2a35; }
  button.danger:hover { background: #63202c; }
  input { width: 100%; padding: .6rem; font-family: monospace; font-size: 1rem;
          background: #163345; color: #e0f0ff; border: 1px solid #2a4a5a;
          border-radius: 4px; }
  .tagline { font-size: .8rem; font-weight: normal; color: #7fb0d0; }
  .controls { font-size: .8rem; color: #6a8aa0; border-top: 1px solid #2a4a5a;
              margin-top: 1.5rem; padding-top: .5rem; }
  .low { color: #ff8a8a; font-weight: bold; }
</style>
</head>
<body>
<h2>FishE <span class="tagline">— fish a seaside village and build a fortune of $10,000</span></h2>
<div id="app">Connecting&hellip;</div>
<p class="controls">Tip: click an option or press its number key (1-9). Enter or Space continues.</p>
<script>
let version = -1;
let currentScreen = null;
let failures = 0;
async function poll() {
  try {
    const response = await fetch("/state");
    const state = await response.json();
    const recovered = failures >= 5;
    failures = 0;
    if (recovered) version = -1;  // force a re-render to clear the disconnect banner
    if (state.version !== version) { version = state.version; render(state.screen); }
  } catch (e) {
    failures++;
    // Don't clobber the intentional "game ended" screen with a scary banner.
    if (failures === 5 && !(currentScreen && currentScreen.type === "ended")) {
      renderDisconnected();
    }
  }
  setTimeout(poll, 300);
}
function renderDisconnected() {
  currentScreen = null;
  const app = document.getElementById("app");
  app.innerHTML = "";
  app.append(el("div", { className: "prompt",
    textContent: "Lost connection to the game — is it still running? Retrying…" }));
}
async function send(value) {
  currentScreen = null;  // ignore stray keypresses until the next screen arrives
  document.getElementById("app").innerHTML = "&hellip;";
  await fetch("/input", { method: "POST", body: JSON.stringify({ value: value }) });
}
function el(tag, props, ...kids) {
  const e = document.createElement(tag);
  Object.assign(e, props || {});
  for (const k of kids) e.append(k);
  return e;
}
function render(screen) {
  const app = document.getElementById("app");
  app.innerHTML = "";
  currentScreen = screen;  // let keyboard shortcuts act on what's on screen
  if (!screen || screen.type === "loading") { app.append("Waiting for the game…"); return; }
  if (screen.type === "ended") { app.append("The game has ended. You can close this tab."); return; }
  if (screen.header) {
    const h = screen.header;
    const header = el("div", { className: "header" });
    const addPart = (node) => {
      if (header.childNodes.length) header.append("  |  ");
      header.append(node);
    };
    addPart(`Day ${h.day}`);
    addPart(h.time);
    addPart(`$${h.money.toFixed(2)}`);
    addPart(`Fish: ${h.fish}`);
    // Below the fishing threshold (10) the player is too tired to fish — flag it.
    const energy = el("span", { textContent: `Energy: ${h.energy}` });
    if (h.energy < 10) energy.className = "low";
    addPart(energy);
    if (h.location) addPart(h.location);
    if (h.goal) addPart(`Goal: ${h.goal}`);
    app.append(header);
  }
  if (screen.descriptor) app.append(el("div", { className: "descriptor", textContent: screen.descriptor }));
  if (screen.prompt) app.append(el("div", { className: "prompt", textContent: screen.prompt }));
  if (screen.type === "options") {
    screen.options.forEach((opt, i) => {
      const b = el("button", {
        textContent: `[${i + 1}] ${opt}`,
        className: /delete/i.test(opt) ? "danger" : "",
      });
      b.onclick = () => send(String(i + 1));
      app.append(b);
    });
  } else if (screen.type === "dialogue") {
    app.append(el("div", { className: "dialogue", textContent: screen.text }));
    const b = el("button", { textContent: "Continue" });
    b.onclick = () => send("");
    app.append(b);
  } else if (screen.type === "prompt") {
    app.append(el("div", { className: "descriptor", textContent: screen.text }));
    const inp = el("input", { type: "text" });
    const submit = () => send(inp.value);
    inp.onkeydown = (e) => { if (e.key === "Enter") submit(); };
    const b = el("button", { textContent: "Submit" });
    b.onclick = submit;
    app.append(inp); app.append(b); inp.focus();
  } else if (screen.type === "timed") {
    app.append(el("div", { className: "descriptor", textContent: screen.message }));
    const b = el("button", { textContent: "React!" });
    b.onclick = () => send("");
    app.append(b);
  }
}
// Keyboard control, matching the console/pygame front-ends: number keys pick an
// option; Enter or Space advances a dialogue or the timed prompt. Typing in the
// text field is left to the field itself.
document.addEventListener("keydown", (e) => {
  const s = currentScreen;
  if (!s) return;
  if (e.target && e.target.tagName === "INPUT") return;
  if (s.type === "options") {
    if (e.key >= "1" && e.key <= "9") {
      const n = parseInt(e.key, 10);
      if (n <= s.options.length) { e.preventDefault(); send(String(n)); }
    }
  } else if (s.type === "dialogue" || s.type === "timed") {
    if (e.key === "Enter" || e.key === " ") { e.preventDefault(); send(""); }
  }
});
poll();
</script>
</body>
</html>
"""


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

    def _present(self, screen):
        with self._lock:
            self._screen = screen
            self._version += 1

    def _header(self):
        return {
            "day": self.timeService.day,
            "time": self.times[self.timeService.time],
            "money": float(self.player.money),
            "fish": self.player.fishCount,
            "energy": self.player.energy,
            "location": self.currentLocationName,
            "goal": self.goalProgress,
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
            choice = str(self._inputQueue.get())
            if choice in valid:
                return choice
            # ignore anything that isn't a listed option and keep waiting

    def showDialogue(self, text):
        self._present({"type": "dialogue", "text": text})
        self._inputQueue.get()
        self.currentPrompt.text = "What would you like to do?"

    def promptForText(self, promptText):
        self._present({"type": "prompt", "text": promptText})
        return str(self._inputQueue.get())

    def timedKeyPress(self, message):
        self._present({"type": "timed", "message": message})
        startTime = time.time()
        self._inputQueue.get()
        return time.time() - startTime

    def cleanup(self):
        self._present({"type": "ended"})
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
