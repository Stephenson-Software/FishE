# @author Daniel McCoy Stephenson
"""Static file server for the browser-native (Pyodide) build of FishE.

    python3 web/serve.py        # then open the URL it prints

The server itself is tak's (tak.web.serve): it never runs the game, only hands
the browser web/index.html, web/game.zip and the kit's assets at /tak/, with
the Cross-Origin-Opener-Policy / Cross-Origin-Embedder-Policy headers that
SharedArrayBuffer - and therefore all player input - depends on. Any proxy in
front of it must preserve them. FISHE_WEB_HOST / FISHE_WEB_PORT move it; the
port defaults to 8080 (what the Dockerfile sets), distinct from the
server-backed front-end's 8000 so both can run at once.
"""

import os

from tak.web.serve import main

REPOSITORY_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
)

if __name__ == "__main__":
    main(REPOSITORY_ROOT, title="FishE", envPrefix="FISHE")
