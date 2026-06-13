from unittest.mock import patch

from src.business import business
from src.player.player import Player
from src.stats.stats import Stats


def test_no_production_without_a_boat():
    # prepare - workers but no boat
    player = Player()
    player.workers = 3
    player.money = 1000

    # call
    summary = business.runDailyProduction(player)

    # check - nothing happens until there's a boat
    assert summary["fishCaught"] == 0
    assert summary["wagesPaid"] == 0
    assert player.money == 1000
    assert player.fishCount == 0


def test_workers_catch_fish_and_draw_wages():
    # prepare - a boat and two workers, plenty of money
    player = Player()
    player.hasBoat = True
    player.workers = 2
    player.money = 1000
    stats = Stats()

    # call
    summary = business.runDailyProduction(player, stats)

    # check
    expectedFish = 2 * business.WORKER_FISH_PER_DAY
    expectedWages = 2 * business.WORKER_DAILY_WAGE
    assert summary["fishCaught"] == expectedFish
    assert summary["wagesPaid"] == expectedWages
    assert player.fishCount == expectedFish
    assert player.money == 1000 - expectedWages
    assert stats.totalFishCaught == expectedFish


def test_workers_catch_rolled_species_not_just_minnow():
    # prepare - a boat and one worker; force the rolled species to Bass
    player = Player()
    player.hasBoat = True
    player.workers = 1
    player.money = 1000

    # call - workers fish a rarity-rolled species, not a hard-coded one
    with patch.object(business.fish, "rollFishType", return_value="Bass"):
        business.runDailyProduction(player)

    # check - the catch landed as the rolled species
    assert player.fishByType.get("Bass") == business.WORKER_FISH_PER_DAY
    assert "Minnow" not in player.fishByType


def test_unaffordable_workers_quit():
    # prepare - 3 workers but only enough money for one day's wage of one worker
    player = Player()
    player.hasBoat = True
    player.workers = 3
    player.money = business.WORKER_DAILY_WAGE  # covers exactly one worker

    # call
    summary = business.runDailyProduction(player)

    # check - the two unpayable workers quit; the remaining one is paid and fishes
    assert summary["quit"] == 2
    assert player.workers == 1
    assert summary["wagesPaid"] == business.WORKER_DAILY_WAGE
    assert summary["fishCaught"] == business.WORKER_FISH_PER_DAY
    assert player.money == 0


def test_all_workers_quit_when_broke():
    # prepare - a boat and workers but no money
    player = Player()
    player.hasBoat = True
    player.workers = 2
    player.money = 0

    # call
    summary = business.runDailyProduction(player)

    # check - everyone quits, nothing caught
    assert player.workers == 0
    assert summary["quit"] == 2
    assert summary["fishCaught"] == 0
    assert player.fishCount == 0
