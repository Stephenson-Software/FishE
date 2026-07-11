from src.housing import housing
from src.player.player import Player
from src.stats.stats import Stats


def test_currentTier_defaults_to_1_when_unset():
    # prepare - an older save/test that never touches homeTier
    player = Player()
    player.homeTier = 0

    # check - treated as the original (tier 1) Driftwood Shack
    assert housing.currentTier(player) == 1


def test_currentTier_reflects_upgrades():
    # prepare
    player = Player()
    player.homeTier = 3

    # check
    assert housing.currentTier(player) == 3


def test_tier1_matches_original_free_defaults():
    # check - tier 1 preserves today's numbers exactly, so a fresh player's
    # behavior is unchanged (free, 100 energy cap, no rental income)
    info = housing.tierInfo(1)
    assert info["cost"] == 0
    assert info["maxEnergy"] == 100
    assert info["dailyRentalIncome"] == 0


def test_maxEnergy_reflects_tier():
    # prepare
    player = Player()
    player.homeTier = 2

    # check
    assert housing.maxEnergy(player) == housing.tierInfo(2)["maxEnergy"]
    assert housing.maxEnergy(player) > housing.tierInfo(1)["maxEnergy"]


def test_no_rental_income_at_tier1():
    # prepare
    player = Player()
    player.money = 100
    stats = Stats()

    # call
    income = housing.runDailyRentalIncome(player, stats)

    # check - a fresh player's Driftwood Shack pays no rent
    assert income == 0
    assert player.money == 100
    assert stats.totalRentalIncome == 0


def test_rental_income_paid_at_higher_tier():
    # prepare
    player = Player()
    player.homeTier = 2
    player.money = 100
    stats = Stats()

    # call
    income = housing.runDailyRentalIncome(player, stats)

    # check
    expectedIncome = housing.tierInfo(2)["dailyRentalIncome"]
    assert income == expectedIncome
    assert player.money == 100 + expectedIncome
    assert stats.totalRentalIncome == expectedIncome
    assert stats.totalMoneyMade == expectedIncome


def test_rental_income_accumulates_across_days():
    # prepare
    player = Player()
    player.homeTier = 3
    stats = Stats()

    # call
    housing.runDailyRentalIncome(player, stats)
    housing.runDailyRentalIncome(player, stats)

    # check - lifetime total accumulates rather than resets
    expectedIncome = housing.tierInfo(3)["dailyRentalIncome"]
    assert stats.totalRentalIncome == expectedIncome * 2
