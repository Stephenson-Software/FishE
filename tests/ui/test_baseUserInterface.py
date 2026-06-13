import sys
import os

# Match the import style production code uses (bare `ui.*`/`player.*`), so class
# identities line up with the runtime MRO. pytest.ini exposes both `.` and `src`,
# and the project's modules import each other without the `src.` prefix.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from ui.baseUserInterface import BaseUserInterface
from ui.userInterface import UserInterface
from ui.consoleUserInterface import ConsoleUserInterface
from player.player import Player
from prompt.prompt import Prompt
from stats.stats import Stats
from world.timeService import TimeService


def makeArgs():
    prompt = Prompt("What would you like to do?")
    player = Player()
    stats = Stats()
    timeService = TimeService(player, stats)
    return prompt, timeService, player


def test_base_user_interface_is_abstract():
    # check - the contract cannot be instantiated directly
    prompt, timeService, player = makeArgs()
    with pytest.raises(TypeError):
        BaseUserInterface(prompt, timeService, player)


def test_front_ends_implement_the_interface():
    # check - the text front-ends are BaseUserInterface implementations
    assert issubclass(UserInterface, BaseUserInterface)
    assert issubclass(ConsoleUserInterface, BaseUserInterface)


class RecordingUserInterface(BaseUserInterface):
    """Minimal front-end that records primitive calls and replays scripted
    showOptions choices — used to exercise the inherited dialogue flow."""

    def __init__(self, prompt, timeService, player, choices):
        super().__init__(prompt, timeService, player)
        self.choices = list(choices)
        self.shownDialogues = []

    def lotsOfSpace(self):
        pass

    def divider(self):
        pass

    def showOptions(self, descriptor, optionList):
        return self.choices.pop(0)

    def showDialogue(self, text):
        self.shownDialogues.append(text)

    def promptForText(self, promptText):
        return self.choices.pop(0)

    def timedKeyPress(self, message):
        return 0.0

    def cleanup(self):
        pass


class FakeNPC:
    name = "Tester"

    def get_dialogue_options(self):
        return [{"question": "Q1", "response": "R1"}]

    def get_dialogue_response(self, index):
        return "R1"

    def introduce(self):
        return "Hello"


def test_promptForNumber_parses_or_returns_none():
    # prepare - first reply is numeric, second is not
    prompt, timeService, player = makeArgs()
    ui = RecordingUserInterface(prompt, timeService, player, choices=["12.5", "abc"])

    # check - numeric parses to float; non-numeric yields None (no exception)
    assert ui.promptForNumber("How much?") == 12.5
    assert ui.promptForNumber("How much?") is None


def test_inherited_interactive_dialogue_uses_primitives():
    # prepare - pick the first question, then choose [Back]
    prompt, timeService, player = makeArgs()
    ui = RecordingUserInterface(prompt, timeService, player, choices=["1", "2"])

    # call - the dialogue flow is inherited from BaseUserInterface
    ui.showInteractiveDialogue(FakeNPC())

    # check - the response was shown via the showDialogue primitive, then it exited
    assert ui.shownDialogues == ["Tester: R1"]
    assert ui.currentPrompt.text == "What would you like to do?"
