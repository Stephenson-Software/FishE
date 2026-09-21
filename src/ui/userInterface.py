# @author Daniel McCoy Stephenson
"""The text/console front-end - FishE's default user interface.

The rendering now lives in tak (tak.ui.console.ConsoleUserInterface); FishE's
BaseUserInterface supplies the constructor and the village's header. The
console prints exactly what it always did: the header chips one per line,
the first bare and the rest behind " | "."""

from tak.ui.console import ConsoleUserInterface

from ui.baseUserInterface import BaseUserInterface


class UserInterface(BaseUserInterface, ConsoleUserInterface):
    pass
