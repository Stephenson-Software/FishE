import pytest

from src.housing import housing
from src.player.player import Player
from src.stats.stats import Stats


def test_tierInfo_rejects_out_of_range_tier():
    # check - fails loudly on bad data instead of silently wrapping around
    # via Python's negative-index behavior
    with pytest.raises(ValueError):
        housing.tierInfo(-1)
    with pytest.raises(ValueError):
        housing.tierInfo(len(housing.HOUSING_TIERS))


def test_currentTier_defaults_to_homeless():
    # prepare - a brand new player
    player = Player()

    # check
    assert housing.currentTier(player) == 0
    assert housing.tierInfo(housing.currentTier(player))["status"] == "homeless"


def test_currentTier_reflects_moves():
    # prepare
    player = Player()
    player.homeTier = 3

    # check
    assert housing.currentTier(player) == 3


def test_homeless_tier_is_free_with_a_low_energy_cap():
    # check - homeless is the free floor of the ladder, with a real penalty
    info = housing.tierInfo(0)
    assert info["status"] == "homeless"
    assert "cost" not in info
    assert info["maxEnergy"] < housing.tierInfo(1)["maxEnergy"]


def test_renting_tier_has_no_purchase_cost_but_charges_daily_rent():
    info = housing.tierInfo(1)
    assert info["status"] == "renting"
    assert "cost" not in info
    assert info["dailyRent"] > 0
    assert info["maxEnergy"] > housing.tierInfo(0)["maxEnergy"]


def test_cheapest_owned_tier_costs_money():
    # check - unlike the old free "starter" tier, owning anything costs
    # something now that homelessness/renting exist below it
    info = housing.tierInfo(2)
    assert info["status"] == "owned"
    assert info["cost"] > 0
    assert info["resaleValue"] > 0


def test_maxEnergy_reflects_tier():
    # prepare
    player = Player()
    player.homeTier = 2

    # check
    assert housing.maxEnergy(player) == housing.tierInfo(2)["maxEnergy"]
    assert housing.maxEnergy(player) > housing.tierInfo(0)["maxEnergy"]


def test_netCostToMove_homeless_to_renting_is_free():
    # prepare - moving in doesn't cost anything upfront; rent is charged daily
    player = Player()

    # check
    assert housing.netCostToMove(player, 1) == 0


def test_netCostToMove_renting_to_owned_is_the_full_price():
    # prepare - a renter has no equity, so buying costs the full price
    player = Player()
    player.homeTier = 1

    # check
    assert housing.netCostToMove(player, 2) == housing.tierInfo(2)["cost"]


def test_netCostToMove_between_owned_tiers_is_discounted_by_resale_value():
    # prepare
    player = Player()
    player.homeTier = 2

    # check
    expected = housing.tierInfo(3)["cost"] - housing.tierInfo(2)["resaleValue"]
    assert housing.netCostToMove(player, 3) == expected


def test_netCostToMove_selling_an_owned_home_to_rent_pays_cash_back():
    # prepare - selling tier 2 (owned) to go back to renting refunds its
    # resale value, since renting itself has no cost
    player = Player()
    player.homeTier = 2

    # check
    assert housing.netCostToMove(player, 1) == -housing.tierInfo(2)["resaleValue"]


def test_netCostToMove_leaving_a_rental_for_homelessness_is_free():
    # prepare - a rental was never owned, so there's nothing to refund, but
    # also nothing owed to leave
    player = Player()
    player.homeTier = 1

    # check
    assert housing.netCostToMove(player, 0) == 0


def test_moveHome_up_spends_net_cost():
    # prepare
    player = Player()
    player.money = 1000
    stats = Stats()
    netCost = housing.netCostToMove(player, 1)

    # call
    moved = housing.moveHome(player, 1, stats)

    # check
    assert moved is True
    assert player.homeTier == 1
    assert player.money == 1000 - netCost
    assert stats.highestHomeTier == 1


def test_moveHome_up_fails_when_unaffordable():
    # prepare - not enough to buy the cheapest owned tier from a rental
    player = Player()
    player.homeTier = 1
    player.money = 0

    # call
    moved = housing.moveHome(player, 2)

    # check - nothing changes
    assert moved is False
    assert player.homeTier == 1
    assert player.money == 0


def test_moveHome_down_from_rental_to_homeless_is_free_and_always_succeeds():
    # prepare
    player = Player()
    player.homeTier = 1
    player.money = 0

    # call
    moved = housing.moveHome(player, 0)

    # check
    assert moved is True
    assert player.homeTier == 0
    assert player.money == 0


def test_moveHome_down_from_owned_pays_cash_back():
    # prepare
    player = Player()
    player.homeTier = 2
    player.money = 0
    refund = -housing.netCostToMove(player, 1)

    # call
    moved = housing.moveHome(player, 1)

    # check - a cash-back move always succeeds, even with no money
    assert moved is True
    assert player.homeTier == 1
    assert player.money == refund


def test_moveHome_down_reclamps_energy_to_new_cap():
    # prepare - Waterfront Manor (cap 200) full energy, trading down to
    # Driftwood Shack (cap 100)
    player = Player()
    player.homeTier = 5
    player.energy = 200
    player.money = 10000

    # call
    housing.moveHome(player, 2)

    # check - energy is clamped immediately, not left over-cap until sleep
    assert player.energy == housing.tierInfo(2)["maxEnergy"]


def test_moveHome_up_does_not_raise_energy_above_current():
    # prepare - low energy shouldn't be topped up just by moving to a home
    # with a higher cap; only sleeping restores energy
    player = Player()
    player.energy = 10
    player.money = 10000

    # call
    housing.moveHome(player, 2)

    # check
    assert player.energy == 10


def test_moveHome_highestHomeTier_does_not_regress():
    # prepare - a player who has previously owned a higher tier
    player = Player()
    player.homeTier = 3
    stats = Stats()
    stats.highestHomeTier = 3

    # call - move back down to homeless
    housing.moveHome(player, 0, stats)

    # check - the lifetime "highest reached" stat remembers the peak
    assert player.homeTier == 0
    assert stats.highestHomeTier == 3


def test_runDailyRent_no_op_when_not_renting():
    # prepare - a homeless player
    player = Player()
    player.money = 100
    stats = Stats()

    # call
    summary = housing.runDailyRent(player, stats)

    # check
    assert summary == {"rentPaid": 0, "evicted": False}
    assert player.money == 100
    assert stats.totalRentPaid == 0


def test_runDailyRent_charges_rent_while_renting():
    # prepare
    player = Player()
    player.homeTier = 1
    player.money = 100
    stats = Stats()
    expectedRent = housing.tierInfo(1)["dailyRent"]

    # call
    summary = housing.runDailyRent(player, stats)

    # check
    assert summary == {"rentPaid": expectedRent, "evicted": False}
    assert player.money == 100 - expectedRent
    assert stats.totalRentPaid == expectedRent


def test_runDailyRent_evicts_when_unaffordable():
    # prepare - renting but broke
    player = Player()
    player.homeTier = 1
    player.money = 0
    stats = Stats()

    # call
    summary = housing.runDailyRent(player, stats)

    # check - evicted back to homeless, no partial payment
    assert summary == {"rentPaid": 0, "evicted": True}
    assert player.homeTier == 0
    assert player.money == 0
    assert stats.totalRentPaid == 0


def test_runDailyRent_evicting_reclamps_energy_to_homeless_cap():
    # prepare - renting (energy cap 90) with more energy than Homeless allows
    player = Player()
    player.homeTier = 1
    player.energy = 90
    player.money = 0
    stats = Stats()

    # call
    housing.runDailyRent(player, stats)

    # check - energy is clamped down to the new (Homeless) cap immediately,
    # not left over-cap until the next sleep
    assert player.energy == housing.tierInfo(0)["maxEnergy"]


def test_runDailyRent_does_not_charge_owned_homes():
    # prepare
    player = Player()
    player.homeTier = 2
    player.money = 100
    stats = Stats()

    # call
    summary = housing.runDailyRent(player, stats)

    # check - owning is a one-time cost, not a recurring one
    assert summary == {"rentPaid": 0, "evicted": False}
    assert player.money == 100
