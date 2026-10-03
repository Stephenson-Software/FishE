"""FishE's arcade achievements (tak.arcade, Stephenson-Software RFC 0014).

tak.arcade.unlock is replaced by a recorder, so these check which ids the game
reports and when - never the network. Every declared id has to be reachable
from a real code path, and reporting one must not change a byte of the save."""

import json
import os
import tempfile
from unittest.mock import MagicMock

import pytest
import tak.arcade

from src import fishE
from src.achievements import achievements
from src.location.enum.locationType import LocationType
from src.player.player import Player
from src.player.playerJsonReaderWriter import PlayerJsonReaderWriter
from src.stats.stats import Stats
from src.stats.statsJsonReaderWriter import StatsJsonReaderWriter
from src.prompt.prompt import Prompt
from src.world.timeService import TimeService

from tests.test_fishE import (
    createGameForPersistence,
    createGameForPlay,
    createGameThroughInit,
)
from tests.location.test_home import createHome


@pytest.fixture
def unlocks(monkeypatch):
    calls = []
    monkeypatch.setattr(
        tak.arcade, "unlock", lambda achievementId: calls.append(achievementId)
    )
    return calls


DECLARED = [a["id"] for a in achievements.arcadeDeclarations()]


def test_declarations_are_valid_unique_and_spoiler_safe():
    assert 6 <= len(DECLARED) <= 12
    assert len(set(DECLARED)) == len(DECLARED)
    for declared in achievements.arcadeDeclarations():
        assert tak.arcade.ID_PATTERN.match(declared["id"]), declared
        assert declared["title"] and declared["description"]
    # the two ids arcade-social's example already uses for FishE
    assert "first-catch" in DECLARED and "reached-goal" in DECLARED
    assert [a["id"] for a in achievements.arcadeDeclarations() if a["hidden"]] == [
        "letter-of-marque"
    ]


def playOneTurn(game):
    game.locations[LocationType.HOME].run.return_value = LocationType.NONE
    game.play()


@pytest.mark.parametrize(
    "milestone",
    [m for m in achievements.MILESTONES if "arcadeId" in m],
    ids=lambda m: m["arcadeId"],
)
def test_each_milestone_is_unlocked_when_the_game_loop_announces_it(unlocks, milestone):
    game = createGameForPlay()
    setattr(game.stats, milestone["stat"], milestone["threshold"])

    playOneTurn(game)

    assert "Milestone unlocked: %s!" % milestone["name"] in game.prompt.text
    assert milestone["arcadeId"] in unlocks


def test_a_milestone_without_an_arcade_id_reports_nothing(unlocks):
    game = createGameForPlay()
    game.stats.totalFishCaught = 100  # First Catch (arcade) + Seasoned Angler (not)

    playOneTurn(game)

    assert "Milestone unlocked: Seasoned Angler!" in game.prompt.text
    assert unlocks == ["first-catch"]


def test_a_milestone_is_reported_once_not_on_every_turn(unlocks):
    game = createGameForPlay()
    game.stats.totalFishCaught = 1
    game.locations[LocationType.HOME].run.return_value = LocationType.HOME
    turns = iter([LocationType.HOME, LocationType.HOME, LocationType.NONE])
    game.locations[LocationType.HOME].run.side_effect = lambda: next(turns)

    game.play()

    assert unlocks == ["first-catch"]


def test_reaching_the_goal_is_unlocked_once(unlocks):
    game = createGameForPlay()
    game.player.money = fishE.GOAL_AMOUNT

    playOneTurn(game)
    assert game.announceGoalIfReached() is False  # already announced

    assert unlocks.count("reached-goal") == 1


def test_retiring_is_unlocked(unlocks):
    home = createHome()
    home.userInterface.showDialogue = MagicMock()

    home.retire()

    assert unlocks == ["retired"]


def test_choosing_retire_from_the_home_menu_unlocks_the_ending(unlocks):
    home = createHome()
    home.stats.earnedMilestones.append(achievements.GOAL_MILESTONE_NAME)
    home.userInterface.showOptions = MagicMock(return_value="5")
    home.userInterface.showDialogue = MagicMock()

    assert home.run() == LocationType.NONE
    assert unlocks == ["retired"]


def test_every_declared_id_is_reachable(unlocks):
    for milestone in achievements.MILESTONES:
        if "arcadeId" in milestone:
            game = createGameForPlay()
            setattr(game.stats, milestone["stat"], milestone["threshold"])
            playOneTurn(game)
    game = createGameForPlay()
    game.player.money = fishE.GOAL_AMOUNT
    playOneTurn(game)
    home = createHome()
    home.userInterface.showDialogue = MagicMock()
    home.retire()

    assert set(unlocks) == set(DECLARED)


def test_loading_a_save_re_asserts_what_it_already_earned(unlocks):
    with tempfile.TemporaryDirectory() as data_directory:
        stats = Stats()
        stats.totalFishCaught = 5
        stats.earnedMilestones = ["First Catch", "Pocket Money", "Reached Goal"]
        createGameThroughInit(
            data_directory,
            {
                "player.json": PlayerJsonReaderWriter().createJsonFromPlayer(Player()),
                "stats.json": StatsJsonReaderWriter().createJsonFromStats(stats),
            },
        )

    assert unlocks == ["first-catch", "reached-goal"]


def test_a_new_game_reports_nothing(unlocks):
    with tempfile.TemporaryDirectory() as data_directory:
        createGameThroughInit(data_directory, {})
    assert unlocks == []


def test_an_unlock_that_raises_never_reaches_the_game(monkeypatch):
    def boom(achievementId):
        raise RuntimeError("bridge gone")

    monkeypatch.setattr(tak.arcade, "unlock", boom)
    game = createGameForPlay()
    game.stats.totalFishCaught = 1
    game.player.money = fishE.GOAL_AMOUNT

    playOneTurn(game)

    assert "First Catch" in game.stats.earnedMilestones


def savedBytes(data_directory, earn):
    fishE.Player, fishE.Stats, fishE.TimeService = Player, Stats, TimeService
    game = createGameForPersistence(data_directory)
    game.player = Player()
    game.stats = Stats()
    game.timeService = TimeService(game.player, game.stats)
    game.prompt = Prompt("What would you like to do?")
    game.player.money = fishE.GOAL_AMOUNT
    earn(game)
    game.save()
    slot = os.path.join(data_directory, "slot_1")
    files = {}
    for name in sorted(os.listdir(slot)):
        with open(os.path.join(slot, name), "rb") as saved:
            files[name] = saved.read()
    return files


def test_unlocking_does_not_change_a_byte_of_the_save(monkeypatch):
    recorded = []
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        monkeypatch.setattr(tak.arcade, "unlock", lambda i: None)
        quiet = savedBytes(a, lambda game: game.announceGoalIfReached())
        monkeypatch.setattr(tak.arcade, "unlock", recorded.append)
        loud = savedBytes(b, lambda game: game.announceGoalIfReached())
    assert recorded == ["reached-goal"]
    assert quiet == loud
    assert json.loads(quiet["stats.json"])["earnedMilestones"]
