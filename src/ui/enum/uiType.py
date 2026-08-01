from enum import Enum


# @author Daniel McCoy Stephenson
class UIType(Enum):
    CONSOLE = "console"
    PYGAME = "pygame"
    WEB = "web"
    # The game running in the player's own browser under Pyodide, with saves in
    # that browser's IndexedDB — as opposed to WEB, where the game and its save
    # files live on a server and the browser is only a terminal for it.
    PYODIDE = "pyodide"
