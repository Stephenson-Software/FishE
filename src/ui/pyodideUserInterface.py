# @author Daniel McCoy Stephenson
"""The browser-native front-end: the whole game runs in the player's tab under
Pyodide, with saves in that browser's IndexedDB. The Worker bridge, the input
ring and the screens now live in tak (tak.ui.pyodide); this module is FishE's
adapter with the (currentPrompt, timeService, player) constructor.
"""

from tak.ui import pyodide as kitPyodide
from tak.ui.pyodide import (  # noqa: F401 - re-exported
    INPUT_POLL_INTERVAL_SECONDS,
    SharedArrayBufferBridge,
)

from ui.baseUserInterface import BaseUserInterface
from ui.webUserInterface import TAGLINE, TIP, TITLE


class PyodideUserInterface(BaseUserInterface, kitPyodide.PyodideUserInterface):
    def __init__(
        self,
        currentPrompt,
        timeService,
        player,
        bridge=None,
        pollIntervalSeconds=INPUT_POLL_INTERVAL_SECONDS,
    ):
        super().__init__(
            currentPrompt,
            timeService,
            player,
            title=TITLE,
            tagline=TAGLINE,
            tip=TIP,
            bridge=bridge,
            pollIntervalSeconds=pollIntervalSeconds,
        )
