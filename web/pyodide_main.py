# @author Daniel McCoy Stephenson
"""Pyodide entry point — runs inside the Web Worker once game.zip is unpacked.

By the time this file is exec()'d, web/game-worker.js has already:
  - put /game/src on sys.path and chdir'd to /game, so the schema paths the
    save readers validate against ("schemas/player.json") resolve
  - created /saves, restored it from IndexedDB, and pointed FISHE_SAVE_DIR at it
  - installed the JavaScript globals the front-end needs: sendToMain, Atomics,
    sabMeta, sabData, sabRingSize, and syncSaves

So there is nothing browser-specific left to do here: build the game against
the Pyodide front-end and play it, exactly as examples/web_app.py does for the
server-backed one.
"""

from ui.enum.uiType import UIType
from ui.pyodideUserInterface import SharedArrayBufferBridge
from fishE import FishE


def main():
    game = None
    try:
        game = FishE(interfaceType=UIType.PYODIDE)
        # play() publishes the ended screen itself, from a finally, so every
        # front-end is told the session is over rather than only this one.
        game.play()
    except SystemExit:
        # Nothing in the game raises this any more, but a browser tab has no
        # process to end and letting SystemExit escape would surface as a Worker
        # error, so it is still treated as a normal finish.
        pass

    if game is None:
        # The game never finished being built, so there is no interface to have
        # cleaned up: tell the page directly.
        SharedArrayBufferBridge().postScreen({"type": "ended"})


main()
