#!/usr/bin/env python3
# @author Daniel McCoy Stephenson
"""Build web/game.zip - the bundle the browser's Pyodide Worker downloads.

    python3 web/build_zip.py

Puts src/, schemas/ and pictures/ in, plus version.txt, art/stills.json and
the Worker's entry point, and the tak package itself under src/tak (see
tak.web.bundle). The browser client is no longer bundled: the page fetches it
from the kit's assets at /tak/.
"""

import os

from tak.web.bundle import build

REPOSITORY_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
)
OUTPUT_PATH = os.path.join("web", "game.zip")

# pictures/ holds the location stills (RFC 0025) and art/stills.json names
# them and carries their alt text; the scene files they were rendered from stay
# out of the bundle. The Dockerfile has to COPY every one of these
# (tests/test_dockerfile.py checks it).
SOURCE_DIRECTORIES = ("src", "schemas", "pictures")
EXTRA_FILES = ("version.txt", "web/pyodide_main.py", "art/stills.json")

if __name__ == "__main__":
    build(
        REPOSITORY_ROOT,
        outputPath=OUTPUT_PATH,
        sourceDirectories=SOURCE_DIRECTORIES,
        extraFiles=EXTRA_FILES,
    )
