import sys
import os

# Match the import style production code uses (bare `ui.*`/`player.*`), so class
# identities line up with the runtime MRO. pytest.ini exposes both `.` and `src`,
# and the project's modules import each other without the `src.` prefix.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest
from unittest.mock import patch

from ui.baseUserInterface import (
    BaseUserInterface,
    unavailableMessage,
    unavailableSuffix,
)
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

    def showOptions(self, descriptor, optionList, unavailableOptions=None):
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


class NoOptionsNPC:
    """An NPC with zero available dialogue options - e.g. every option's
    condition is currently false. showInteractiveDialogue falls back to a
    plain introduction instead of showing an empty question menu."""

    name = "Tester"

    def get_dialogue_options(self):
        return []

    def get_dialogue_response(self, index):
        return ""

    def introduce(self):
        return "Tester: Not much to say."


def test_inherited_interactive_dialogue_falls_back_to_introduction_when_no_options():
    # prepare - no choices are consumed since showOptions is never reached
    prompt, timeService, player = makeArgs()
    ui = RecordingUserInterface(prompt, timeService, player, choices=[])

    # call
    ui.showInteractiveDialogue(NoOptionsNPC())

    # check - the introduction was shown via showDialogue, not a question menu
    assert ui.shownDialogues == ["Tester: Not much to say."]
    assert ui.currentPrompt.text == "What would you like to do?"


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


def makeRecordingUI(choices=()):
    prompt, timeService, player = makeArgs()
    return RecordingUserInterface(prompt, timeService, player, choices=list(choices))


def test_unavailableReasons_maps_option_numbers_onto_a_parallel_list():
    # check - call sites key by 1-based option number (what len(optionList)
    # gives them as they append); front-ends want it lined up with the options
    ui = makeRecordingUI()
    reasons = ui.unavailableReasons(["Fish", "Go Home", "Quit"], {1: "too tired"})

    assert reasons == ["too tired", None, None]


def test_unavailableReasons_defaults_to_everything_available():
    # check - a menu that passes nothing is unchanged in every front-end
    ui = makeRecordingUI()

    assert ui.unavailableReasons(["A", "B"], None) == [None, None]
    assert ui.unavailableReasons(["A", "B"], {}) == [None, None]


def test_unavailableReasons_rejects_a_number_outside_the_menu():
    # check - marking an option that isn't there means the call site's numbers
    # have drifted from its option list, which would silently leave the wrong
    # row (or no row) greyed out; say so instead
    ui = makeRecordingUI()
    with pytest.raises(ValueError) as raised:
        ui.unavailableReasons(["Only"], {2: "nope"})

    message = str(raised.value)
    assert "1 option" in message
    assert "len(optionList)" in message


def test_unavailableReasons_never_blocks_every_option():
    # check - a menu where nothing can be picked is one no front-end can get
    # out of, so the marks are dropped and the game gives its own refusal
    ui = makeRecordingUI()
    reasons = ui.unavailableReasons(["A", "B"], {1: "no", 2: "also no"})

    assert reasons == [None, None]


def test_selectableNumbers_excludes_the_unavailable_rows():
    # check - the set every front-end validates the player's answer against
    ui = makeRecordingUI()

    assert ui.selectableNumbers(["too tired", None, None]) == {"2", "3"}
    assert ui.selectableNumbers([None]) == {"1"}


def test_unavailable_wording_is_shared_by_the_text_front_ends():
    # check - console and pygame both tag rows through these helpers, so the
    # phrasing can't drift between them
    assert unavailableSuffix(None) == ""
    assert unavailableSuffix("no fish") == " (unavailable: no fish)"
    assert unavailableMessage("no fish") == "You can't do that right now: no fish."
