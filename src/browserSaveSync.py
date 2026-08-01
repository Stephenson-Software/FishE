# @author Daniel McCoy Stephenson
"""Flush FishE's save files to browser storage when running under Pyodide.

The Pyodide front-end runs the whole game inside a Web Worker, so its save
slots live in the Worker's in-memory Emscripten filesystem — memory that is
discarded the moment the tab closes. ``web/game-worker.js`` exposes a
``syncSaves()`` JavaScript global that walks the save directory and hands the
files to the main thread, which writes them to IndexedDB (see that file for why
the write cannot happen in the Worker itself).

Every code path that writes or deletes a save must call ``syncBrowserSaves()``
afterwards, or the change lives only until the tab is closed.

Outside Pyodide (console, pygame, and the HTTP web front-end) the ``js`` module
does not exist, so this is a no-op and the on-disk files are the real saves.
"""

import sys


def syncBrowserSaves():
    """Persist the save directory to browser storage, if running in a browser.

    Returns True if a flush was performed, False if there was nothing to flush
    to (i.e. this is not a browser build). Never raises: a browser that refuses
    to store data must not take the game down with it.
    """
    # Imported via sys.modules rather than `import js` so that a plain CPython
    # run doesn't depend on a module that only exists inside Pyodide, and so a
    # test can install a fake one.
    js = sys.modules.get("js")
    if js is None:
        return False

    syncSaves = getattr(js, "syncSaves", None)
    if syncSaves is None:
        return False

    try:
        syncSaves()
        return True
    except Exception as e:
        print(
            "\n Warning: could not save your progress to browser storage: "
            f"{e}\n Progress is kept for this session, but may be lost when "
            "you reload. Check that this site is allowed to store data and "
            "that you are not in a private/incognito window."
        )
        return False
