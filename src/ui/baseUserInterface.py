from abc import ABC, abstractmethod
from prompt.prompt import Prompt
from player.player import Player
from world.timeService import TimeService


# @author Daniel McCoy Stephenson
class BaseUserInterface(ABC):
    """Abstract contract every front-end (text/console, pygame, web, ...) implements.

    Concrete subclasses must implement the rendering/input primitives below.
    Shared state and the higher-level interactive-dialogue flow live here so all
    front-ends behave consistently and only the primitives differ.
    """

    def __init__(self, currentPrompt: Prompt, timeService: TimeService, player: Player):
        self.currentPrompt = currentPrompt
        self.timeService = timeService
        self.player = player

        self.prompt = "Make your choice!"
        self.optionList = []
        # Header fields the game loop sets before each render; empty hides the line.
        self.currentLocationName = ""
        self.goalProgress = ""

        self.times = {
            0: "12:00 AM",
            1: "1:00 AM",
            2: "2:00 AM",
            3: "3:00 AM",
            4: "4:00 AM",
            5: "5:00 AM",
            6: "6:00 AM",
            7: "7:00 AM",
            8: "8:00 AM",
            9: "9:00 AM",
            10: "10:00 AM",
            11: "11:00 AM",
            12: "12:00 PM",
            13: "1:00 PM",
            14: "2:00 PM",
            15: "3:00 PM",
            16: "4:00 PM",
            17: "5:00 PM",
            18: "6:00 PM",
            19: "7:00 PM",
            20: "8:00 PM",
            21: "9:00 PM",
            22: "10:00 PM",
            23: "11:00 PM",
        }

    @abstractmethod
    def lotsOfSpace(self):
        """Clear or add space to the display."""
        pass

    @abstractmethod
    def divider(self):
        """Display a divider between sections."""
        pass

    @abstractmethod
    def showOptions(self, descriptor, optionList):
        """Show numbered options and return the chosen option's number as a string."""
        pass

    @abstractmethod
    def showDialogue(self, text):
        """Show a block of text and wait for the player to acknowledge it."""
        pass

    @abstractmethod
    def cleanup(self):
        """Release any resources held by the front-end."""
        pass

    def showInteractiveDialogue(self, npc):
        """Default interactive NPC conversation built on the primitives above.

        Front-ends inherit this for free; one (the console) overrides it with a
        richer layout. Picks a question via showOptions and shows the response
        via showDialogue until the player chooses to go back."""
        while True:
            dialogueOptions = npc.get_dialogue_options()
            if not dialogueOptions:
                self.showDialogue(npc.introduce())
                self.currentPrompt.text = "What would you like to do?"
                return

            questions = [
                option.get("question", "Option %d" % (index + 1))
                for index, option in enumerate(dialogueOptions)
            ]
            questions.append("[Back]")

            choice = int(self.showOptions("Talking with %s" % npc.name, questions))
            if choice == len(questions):
                self.currentPrompt.text = "What would you like to do?"
                return

            self.showDialogue(
                "%s: %s" % (npc.name, npc.get_dialogue_response(choice - 1))
            )
