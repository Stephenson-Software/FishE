"""Example: run FishE with the browser-based web front-end.

This shows how to drive the existing game through the WebUserInterface — no game
logic changes, just a different UIType. Run it and open the printed URL:

    python3 examples/web_app.py

The whole game (save-file manager, fishing, shop, bank, tavern, dialogue) then
plays in the browser. The server binds 127.0.0.1:8000 by default; set
FISHE_WEB_HOST/FISHE_WEB_PORT (read by UserInterfaceFactory's WEB branch) to
change that — e.g. FISHE_WEB_HOST=0.0.0.0 so it's reachable from outside its
own host, such as from inside a container.
"""

import os
import sys

# Make the game package importable when running this file directly.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ui.enum.uiType import UIType  # noqa: E402
from fishE import FishE  # noqa: E402


def main():
    host = os.environ.get("FISHE_WEB_HOST", "127.0.0.1")
    port = os.environ.get("FISHE_WEB_PORT", "8000")
    print(f"FishE web app is starting at http://{host}:{port}")
    print("Open that URL in your browser to play. Press Ctrl+C here to stop.")
    # Building FishE starts the web server and then waits (in the save-file
    # manager) for the browser to interact, so play happens entirely in-browser.
    game = FishE(interfaceType=UIType.WEB)
    game.play()


if __name__ == "__main__":
    main()
