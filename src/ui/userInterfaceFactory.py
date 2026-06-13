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
        else:
            raise ValueError(f"Unsupported UI type: {ui_type}")
