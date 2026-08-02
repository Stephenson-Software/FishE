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


def getJsModule():
    """Return Pyodide's `js` module, or None when not running in a browser.

    `js` is importable under Pyodide but is NOT already in sys.modules — it
    only lands there once something imports it. So this has to actually
    attempt the import: looking in sys.modules alone reports "not a browser"
    while running in one, which silently turned saving into a no-op and made
    the Pyodide front-end refuse to start.

    sys.modules is still consulted first, and `import` would consult it anyway,
    so a test can inject a stand-in under that name.
    """
    js = sys.modules.get("js")
    if js is not None:
        return js
    try:
        import js  # noqa: F811 — only importable inside Pyodide
    except ImportError:
        return None
    return js


def syncBrowserSaves():
    """Persist the save directory to browser storage, if running in a browser.

    Returns True if a flush was performed, False if there was nothing to flush
    to (i.e. this is not a browser build). Never raises: a browser that refuses
    to store data must not take the game down with it.
    """
    js = getJsModule()
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
