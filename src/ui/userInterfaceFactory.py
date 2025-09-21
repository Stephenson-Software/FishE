from ui.enum.uiType import UIType
from ui.consoleUserInterface import ConsoleUserInterface
from ui.pygameUserInterface import PygameUserInterface
from prompt.prompt import Prompt
from player.player import Player
from world.timeService import TimeService


# @author Daniel McCoy Stephenson
class UserInterfaceFactory:
    """Factory class to create user interfaces based on type"""
    
    @staticmethod
    def create_user_interface(ui_type: UIType, currentPrompt: Prompt, timeService: TimeService, player: Player):
        """Create a user interface of the specified type"""
        if ui_type == UIType.CONSOLE:
            return ConsoleUserInterface(currentPrompt, timeService, player)
        elif ui_type == UIType.PYGAME:
            return PygameUserInterface(currentPrompt, timeService, player)
        else:
            raise ValueError(f"Unsupported UI type: {ui_type}")