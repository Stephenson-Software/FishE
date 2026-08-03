import time
from abc import ABC, abstractmethod
from prompt.prompt import Prompt
from player.player import Player
from world.timeService import TimeService


def unavailableSuffix(reason):
    """How a text front-end tags a menu row the game would refuse.

    Shared by the console and pygame front-ends so the wording is identical in
    both; the web front-end sends the bare reason to the browser instead, which
    styles it rather than appending it to the label."""
    return "" if reason is None else " (unavailable: %s)" % reason


def unavailableMessage(reason):
    """What to say when the player picks an option that can't be picked.

    Names the blocker and what to do about it rather than a bare "try again",
    which would read as though they had mistyped."""
    return "You can't do that right now: %s." % reason


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
    def showOptions(self, descriptor, optionList, unavailableOptions=None):
        """Show numbered options and return the chosen option's number as a string.

        unavailableOptions is an optional {optionNumber: reason} mapping naming
        the 1-based options the game would refuse right now, each with a short
        reason ("needs 10 energy - sleep at home"). Every front-end must show
        those options as unpickable, spell the reason out beside them, and
        refuse to return their number - see unavailableReasons()."""
        pass

    def unavailableReasons(self, optionList, unavailableOptions):
        """One entry per option: the reason it can't be picked, or None.

        Call sites pass {optionNumber: reason} rather than a parallel list
        because a menu is built by appending, so the row just added is always
        len(optionList) and the numbers can't drift out of step as options
        appear and disappear with the player's progress. Front-ends want the
        parallel list, so the conversion happens once, here.
        """
        reasons = [None] * len(optionList)
        for number, reason in (unavailableOptions or {}).items():
            if not 1 <= number <= len(optionList):
                raise ValueError(
                    "showOptions was told option %r is unavailable (%r), but "
                    "the menu only has %d option(s). The keys of "
                    "unavailableOptions are 1-based option numbers into the "
                    "list passed alongside it - a menu that appends its rows "
                    "should mark one with len(optionList) right after "
                    "appending it." % (number, reason, len(optionList))
                )
            reasons[number - 1] = reason
        # Marking every option unavailable would leave the player facing a menu
        # that accepts nothing, which no front-end can recover from. Fall back
        # to a normal menu instead and let the game give its own refusal.
        if optionList and all(reason is not None for reason in reasons):
            return [None] * len(optionList)
        return reasons

    def selectableNumbers(self, reasons):
        """The 1-based option numbers a front-end may return, as strings."""
        return {
            str(index + 1) for index, reason in enumerate(reasons) if reason is None
        }

    @abstractmethod
    def showDialogue(self, text):
        """Show a block of text and wait for the player to acknowledge it."""
        pass

    @abstractmethod
    def promptForText(self, promptText):
        """Show a prompt and return the line of text the player enters."""
        pass

    @abstractmethod
    def timedKeyPress(self, message):
        """Show a message and return the seconds until the player reacts.

        Used by timing challenges (e.g. the fishing minigame); a front-end that
        cannot measure a reaction may return 0.0 to count it as instant."""
        pass

    @abstractmethod
    def cleanup(self):
        """Release any resources held by the front-end."""
        pass

    def showBusy(self, message, seconds=1.0):
        """Show a message while the game pauses, without waiting for input.

        Used by the short "Fishing..." style beats, which otherwise have no way
        to say anything: showDialogue would demand a keypress the game never
        asked for. Concrete (not abstract) so a front-end that has nothing to
        draw still gets the pause; every front-end in this repo overrides it to
        actually show the message."""
        time.sleep(seconds)

    def promptForNumber(self, promptText):
        """Prompt for a number via promptForText; return a float or None if the
        player's input was not numeric. Works for every front-end."""
        try:
            return float(self.promptForText(promptText))
        except (ValueError, TypeError):
            return None

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
