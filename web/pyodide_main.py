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
from fishE import FishE


def main():
    # play() publishes the ended screen through the front-end's cleanup() on
    # every way out of the game - including "Quit" from the save-file manager,
    # which ends the run rather than the process so a tab with no process to
    # end is not a special case here (see FishE.play).
    game = FishE(interfaceType=UIType.PYODIDE)
    game.play()


main()
