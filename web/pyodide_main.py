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
        game.play()
    except SystemExit:
        # Choosing "Quit" in the save-file manager calls exit(). In a browser
        # tab there is no process to end, and letting SystemExit escape would
        # surface as a Worker error, so it is treated as a normal finish.
        pass

    # Nothing else calls cleanup() when the game loop ends, and without it the
    # tab would sit on the last screen forever rather than saying it's over.
    if game is not None:
        game.userInterface.cleanup()
    else:
        # Quit before the game finished being built: there is no interface to
        # clean up, so tell the page directly.
        SharedArrayBufferBridge().postScreen({"type": "ended"})


main()
