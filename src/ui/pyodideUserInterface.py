# @author Daniel McCoy Stephenson
"""FishE's browser-native front-end: the game itself runs in the player's tab.

WebUserInterface puts the game on a server and the browser polls it, which means
one server-side game and one set of server-side save files shared by everyone
who opens the page. This front-end instead runs the whole Python game inside a
Web Worker under Pyodide, so every tab has its own game and its own saves — the
latter kept in the browser's IndexedDB (see browserSaveSync and
web/game-worker.js).

Only the transport differs from WebUserInterface, which this class subclasses:
every screen the player sees is still built by WebUserInterface's primitives, so
a new screen type is written once and appears in both. Here a screen is posted
to the main thread as a JSON string, and the player's response is read from the
SharedArrayBuffer ring buffer that web/index.html writes into.

Why a ring buffer rather than Worker messages: the game loop is synchronous, so
it blocks the Worker while waiting for input, and a blocked Worker can never run
an onmessage handler. Shared memory is readable without the event loop, so the
main thread can hand input to a blocked game.
"""

import json
import time

from browserSaveSync import getJsModule
from ui.webUserInterface import WebUserInterface


# How long to sleep between checks of the input ring while waiting on the
# player. Short enough to feel instant, long enough that a player reading a
# screen isn't spun on. time.sleep() in Pyodide yields via Atomics.wait, so
# this genuinely idles the Worker rather than burning the tab's CPU.
INPUT_POLL_INTERVAL_SECONDS = 0.02

_MESSAGE_TERMINATOR = 10  # b"\n" — the ring's message boundary


class SharedArrayBufferBridge:
    """Talks to the JavaScript side of the Pyodide front-end.

    web/game-worker.js installs the globals used here before starting the game:
    ``sendToMain`` (post a message to the main thread), and ``sabMeta`` /
    ``sabData`` / ``sabRingSize`` / ``Atomics`` for the input ring buffer.
    """

    def __init__(self, js=None):
        if js is None:
            js = getJsModule()
        if js is None:
            raise RuntimeError(
                "The Pyodide front-end can only run inside a browser: the 'js' "
                "module it needs exists only under Pyodide. To play in a "
                "browser, serve the game with 'python3 web/serve.py' and open "
                "the page it prints. To play from a terminal or a desktop "
                "window instead, use UIType.CONSOLE or UIType.PYGAME."
            )
        missing = [
            name
            for name in ("sendToMain", "Atomics", "sabMeta", "sabData", "sabRingSize")
            if getattr(js, name, None) is None
        ]
        if missing:
            raise RuntimeError(
                "The Pyodide front-end is missing the JavaScript globals its "
                f"Worker is supposed to install: {', '.join(missing)}. This "
                "happens when the game is started by something other than "
                "web/game-worker.js — start it from that Worker (web/index.html "
                "does), or use UIType.CONSOLE outside a browser."
            )
        self._js = js
        self._ringSize = int(js.sabRingSize)

    def postScreen(self, screen):
        """Send a screen to the main thread for rendering.

        Sent as a JSON string rather than a converted JS object: the screen is
        a plain nested dict/list structure, and a string crosses the Worker
        boundary without any Pyodide FFI conversion to get wrong.
        """
        self._js.sendToMain(json.dumps({"type": "screen", "screen": screen}))

    def readInput(self):
        """Return the player's next response, or None if none has arrived yet."""
        line = self._readLine()
        if not line:
            return None
        try:
            message = json.loads(line)
        except ValueError:
            # Not something this front-end sent; ignoring it keeps a stray
            # write from ending the wait with a bogus response.
            return None
        if message.get("type") != "input":
            return None
        return message.get("value", "")

    def _readLine(self):
        """Pull one newline-terminated message out of the ring buffer."""
        Atomics = self._js.Atomics
        meta = self._js.sabMeta
        data = self._js.sabData

        writeIndex = int(Atomics.load(meta, 0))
        readIndex = int(Atomics.load(meta, 1))
        if writeIndex == readIndex:
            return ""

        raw = bytearray()
        while readIndex != writeIndex:
            byte = int(data[readIndex % self._ringSize])
            readIndex += 1
            if byte == _MESSAGE_TERMINATOR:
                break
            raw.append(byte)
        Atomics.store(meta, 1, readIndex)
        # Player-entered text (a business name, say) can be any UTF-8; a partial
        # sequence is dropped rather than raising in the middle of the game.
        return raw.decode("utf-8", errors="ignore")


# @author Daniel McCoy Stephenson
class PyodideUserInterface(WebUserInterface):
    """WebUserInterface's screens, delivered over the Pyodide Worker bridge."""

    def __init__(
        self,
        currentPrompt,
        timeService,
        player,
        bridge=None,
        pollIntervalSeconds=INPUT_POLL_INTERVAL_SECONDS,
    ):
        # start_server=False: there is no server here, and no sockets to bind
        # in the browser. get_state()/submit_input() still work, which keeps the
        # inherited screen bookkeeping (and its tests) intact.
        super().__init__(currentPrompt, timeService, player, start_server=False)
        self._bridge = bridge if bridge is not None else SharedArrayBufferBridge()
        self._pollIntervalSeconds = pollIntervalSeconds

    def _present(self, screen):
        # Record it the way WebUserInterface does (version bookkeeping, and so a
        # late-attaching reader can still ask for the current screen), then push
        # it to the browser instead of waiting to be polled for it.
        super()._present(screen)
        self._bridge.postScreen(screen)

    def _awaitInput(self):
        # The queue is still honoured so submit_input() works for tests and for
        # anything driving the interface directly; the ring buffer is what the
        # browser actually writes to.
        while True:
            if not self._inputQueue.empty():
                return self._inputQueue.get()
            value = self._bridge.readInput()
            if value is not None:
                return value
            time.sleep(self._pollIntervalSeconds)
