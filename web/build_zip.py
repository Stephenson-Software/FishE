#!/usr/bin/env python3
# @author Daniel McCoy Stephenson
"""Build web/game.zip — the bundle the browser's Pyodide Worker downloads.

Everything the game needs to run in a tab goes in: the Python source tree, the
JSON Schemas the save readers validate against, and the Worker's entry point.
Run from the repository root (the Dockerfile does this at build time):

    python3 web/build_zip.py
"""
import os
import zipfile

OUTPUT_PATH = "web/game.zip"

# Paths are stored repo-relative so the Worker can unpack into /game and get a
# tree that matches a checkout — which is what makes the cwd-relative schema
# paths in the *JsonReaderWriter modules resolve there.
SOURCE_DIRECTORIES = ("src", "schemas")
# client.js/client.css are fetched over HTTP by the page, so the browser does
# not need them from the bundle — they are included anyway because
# webUserInterface reads them from the filesystem, and PyodideUserInterface
# subclasses it. Belt and braces: the read is lazy so it never happens in the
# browser, and if a future change makes it happen, the files are there.
EXTRA_FILES = (
    "version.txt",
    "web/pyodide_main.py",
    "web/client.js",
    "web/client.css",
)


def build(outputPath=OUTPUT_PATH):
    with zipfile.ZipFile(outputPath, "w", zipfile.ZIP_DEFLATED) as bundle:
        for directory in SOURCE_DIRECTORIES:
            for root, dirs, files in os.walk(directory):
                dirs[:] = [d for d in dirs if d != "__pycache__"]
                for name in files:
                    if name.endswith(".pyc"):
                        continue
                    path = os.path.join(root, name)
                    bundle.write(path, path)
        for path in EXTRA_FILES:
            if os.path.exists(path):
                bundle.write(path, path)
    print(f"Built {outputPath}")


if __name__ == "__main__":
    build()
