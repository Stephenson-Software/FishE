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


def test_currentTier_defaults_to_1_when_unset():
    # prepare - an older save/test that sets hasBoat without ever touching
    # boatTier
    player = Player()
    player.hasBoat = True

    # check - treated as the original (tier 1) boat
    assert player.boatTier == 0
    assert business.currentTier(player) == 1


def test_currentTier_reflects_upgrades():
    # prepare
    player = Player()
    player.hasBoat = True
    player.boatTier = 2

    # check
    assert business.currentTier(player) == 2


def test_higher_tier_boat_yields_more_fish_per_worker():
    # prepare - an upgraded boat (tier 2) with one worker
    player = Player()
    player.hasBoat = True
    player.boatTier = 2
    player.workers = 1
    player.money = 1000
    stats = Stats()

    # call
    summary = business.runDailyProduction(player, stats)

    # check - tier 2's fishPerDay beats the flat tier-1 constant
    tier2FishPerDay = business.tierInfo(2)["fishPerDay"]
    assert tier2FishPerDay > business.WORKER_FISH_PER_DAY
    assert summary["fishCaught"] == tier2FishPerDay
    assert stats.totalFishCaughtByCrew == tier2FishPerDay


def test_runDailyProduction_tracks_lifetime_business_stats():
    # prepare
    player = Player()
    player.hasBoat = True
    player.workers = 2
    player.money = 1000
    stats = Stats()

    # call
    summary = business.runDailyProduction(player, stats)

    # check - lifetime counters advance alongside the day's summary
    assert stats.totalFishCaughtByCrew == summary["fishCaught"]
    assert stats.totalWagesPaid == summary["wagesPaid"]
    assert stats.daysInBusiness == 1

    # a second day accumulates rather than resets
    business.runDailyProduction(player, stats)
    assert stats.daysInBusiness == 2


def test_sellBoat_refunds_resale_value_and_clears_boat_and_crew():
    # prepare - a Trawler (tier 2) with two workers
    player = Player()
    player.hasBoat = True
    player.boatTier = 2
    player.workers = 2
    player.money = 0
    resaleValue = business.tierInfo(2)["resaleValue"]

    # call
    sold = business.sellBoat(player)

    # check - refunded, and boat/tier/crew all cleared
    assert sold is True
    assert player.money == resaleValue
    assert player.hasBoat is False
    assert player.boatTier == 0
    assert player.workers == 0


def test_sellBoat_fails_when_no_boat_owned():
    # prepare
    player = Player()
    player.hasBoat = False
    startingMoney = player.money

    # call
    sold = business.sellBoat(player)

    # check - nothing changes
    assert sold is False
    assert player.money == startingMoney
