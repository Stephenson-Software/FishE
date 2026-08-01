import sys
import os

# Match the import style production code uses (bare `ui.*`/`player.*`), so class
# identities line up with the runtime MRO. pytest.ini exposes both `.` and `src`,
# and the project's modules import each other without the `src.` prefix.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest
from unittest.mock import patch

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


def test_showBusy_is_inherited_and_only_waits():
    # prepare - RecordingUserInterface implements the abstract primitives only,
    # so it exercises the default a new front-end would get for free
    prompt, timeService, player = makeArgs()
    ui = RecordingUserInterface(prompt, timeService, player, choices=[])

    # call
    with patch("ui.baseUserInterface.time.sleep") as sleep:
        ui.showBusy("Fishing...", 2)

    # check - the pause happens and nothing is shown or acknowledged
    sleep.assert_called_once_with(2)
    assert ui.shownDialogues == []
    assert ui.currentPrompt.text == "What would you like to do?"


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


class ConditionalNPC:
    """An NPC whose second question only appears once `unlocked` is truthy -
    the shape villagers/locations use to gate crew dialogue behind hiring."""

    name = "Tester"

    def __init__(self):
        self.unlocked = []
        self.options = [
            {"question": "Q1", "response": "R1"},
            {
                "question": "Q2",
                "response": "R2",
                "condition": lambda: bool(self.unlocked),
            },
        ]

    def get_dialogue_options(self):
        return [o for o in self.options if o.get("condition", lambda: True)()]

    def get_dialogue_response(self, index):
        return self.get_dialogue_options()[index]["response"]

    def introduce(self):
        return "Hello"


def test_inherited_interactive_dialogue_reflects_unlocked_options():
    # prepare - the flow every front-end without an override inherits (pygame
    # and web both use it), so conditional options have to work here
    prompt, timeService, player = makeArgs()
    npc = ConditionalNPC()

    # call - only Q1 exists, so "2" is [Back]
    ui = RecordingUserInterface(prompt, timeService, player, choices=["1", "2"])
    ui.showInteractiveDialogue(npc)

    # check
    assert ui.shownDialogues == ["Tester: R1"]

    # call - unlock Q2 on the same NPC and pick it; "3" is now [Back]
    npc.unlocked.append(1)
    ui = RecordingUserInterface(prompt, timeService, player, choices=["2", "3"])
    ui.showInteractiveDialogue(npc)

    # check - the newly available question resolves to its own response
    assert ui.shownDialogues == ["Tester: R2"]
