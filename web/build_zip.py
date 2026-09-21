#!/usr/bin/env python3
# @author Daniel McCoy Stephenson
"""Build web/game.zip - the bundle the browser's Pyodide Worker downloads.

    python3 web/build_zip.py

Puts src/ and schemas/ in, plus version.txt and the Worker's entry point, and
the tak package itself under src/tak (see tak.web.bundle). The browser client
is no longer bundled: the page fetches it from the kit's assets at /tak/.
"""
import os

from tak.web.bundle import build

REPOSITORY_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
)
OUTPUT_PATH = os.path.join("web", "game.zip")

if __name__ == "__main__":
    build(
        REPOSITORY_ROOT,
        outputPath=OUTPUT_PATH,
        extraFiles=("version.txt", "web/pyodide_main.py"),
    )
