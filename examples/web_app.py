"""Example: run FishE with the server-backed web front-end.

This shows how to drive the existing game through the WebUserInterface — no game
logic changes, just a different UIType. The game runs here, in this process, and
the browser is a terminal for it: one game and one set of save files under
data/, shared by everyone who opens the page.

To give each player their own game and their own saves, run the browser-native
front-end instead (`python3 web/serve.py`), which hands the game to Pyodide in
the player's own tab and keeps the save slots in that browser's IndexedDB.

Run it and open the printed URL:

    python3 examples/web_app.py

The whole game (save-file manager, fishing, shop, bank, tavern, dialogue) then
plays in the browser. The server binds 127.0.0.1:8000 by default (the default
and the two variables that move it live in WebUserInterface); set
FISHE_WEB_HOST/FISHE_WEB_PORT to change that — e.g. FISHE_WEB_HOST=0.0.0.0 so
it's reachable from outside its own host, such as from inside a container. The
URL is printed once the server is bound, so what it names is always served.
"""

import os
import sys

# Make the game package importable when running this file directly.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ui.enum.uiType import UIType  # noqa: E402
from fishE import FishE  # noqa: E402


def main():
    # Building FishE starts the web server and then waits (in the save-file
    # manager) for the browser to interact, so play happens entirely in-browser.
    # The URL is announced by the front-end once that server is bound, rather
    # than from here beforehand: control never comes back to this function to
    # say what was bound, and a port that is misspelled or already taken would
    # otherwise be preceded by an address that will never answer.
    game = FishE(interfaceType=UIType.WEB)
    game.play()


if __name__ == "__main__":
    main()
