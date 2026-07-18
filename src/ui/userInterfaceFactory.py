import os

from ui.enum.uiType import UIType
from ui.consoleUserInterface import ConsoleUserInterface
from prompt.prompt import Prompt
from player.player import Player
from world.timeService import TimeService


# @author Daniel McCoy Stephenson
class UserInterfaceFactory:
    """Creates the requested front-end behind the BaseUserInterface contract.

    To add a new front-end (e.g. a web interface): implement BaseUserInterface,
    add a UIType value, and add a branch here. Heavy/optional front-ends (like
    pygame) are imported lazily inside their branch so the default text mode has
    no extra dependencies."""

    @staticmethod
    def create_user_interface(
        ui_type: UIType,
        currentPrompt: Prompt,
        timeService: TimeService,
        player: Player,
    ):
        """Create a user interface of the specified type."""
        if ui_type == UIType.CONSOLE:
            return ConsoleUserInterface(currentPrompt, timeService, player)
        elif ui_type == UIType.PYGAME:
            # Imported lazily so text mode does not require pygame.
            from ui.pygameUserInterface import PygameUserInterface

            return PygameUserInterface(currentPrompt, timeService, player)
        elif ui_type == UIType.WEB:
            # Imported lazily so other modes don't start the HTTP machinery.
            from ui.webUserInterface import WebUserInterface

            # WebUserInterface itself defaults to 127.0.0.1:8000 (unreachable
            # from outside its own host/container). Let FISHE_WEB_HOST/
            # FISHE_WEB_PORT override that — e.g. FISHE_WEB_HOST=0.0.0.0 so a
            # container's port mapping/reverse proxy can actually reach it —
            # while leaving the default unchanged for anyone not setting them.
            host = os.environ.get("FISHE_WEB_HOST", "127.0.0.1")
            port_str = os.environ.get("FISHE_WEB_PORT", "8000")
            try:
                port = int(port_str)
            except ValueError:
                raise ValueError(
                    f"FISHE_WEB_PORT must be an integer, got: {port_str!r}"
                )
            return WebUserInterface(
                currentPrompt, timeService, player, host=host, port=port
            )
        else:
            raise ValueError(f"Unsupported UI type: {ui_type}")
