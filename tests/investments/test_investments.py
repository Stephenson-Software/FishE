import pytest

from src.investments import investments
from src.player.player import Player
from src.stats.stats import Stats


def test_typeInfo_rejects_out_of_range_id():
    # check - fails loudly on bad data instead of silently wrapping around
    # to the last entry via Python's negative-index behavior
    with pytest.raises(ValueError):
        investments.typeInfo(0)
    with pytest.raises(ValueError):
        investments.typeInfo(len(investments.PROPERTY_TYPES) + 1)


def test_countOwned_reflects_holdings():
    # prepare
    player = Player()
    player.rentalProperties = [1, 1, 2]

    # check
    assert investments.countOwned(player, 1) == 2
    assert investments.countOwned(player, 2) == 1
    assert investments.countOwned(player, 3) == 0


def test_ownedCounts_maps_every_owned_type_in_one_pass():
    # prepare
    player = Player()
    player.rentalProperties = [1, 1, 2]

    # check - only owned types show up; type 3 (never bought) is absent
    # rather than present with a 0
    counts = investments.ownedCounts(player)
    assert counts == {1: 2, 2: 1}
    assert 3 not in counts


def test_ownedCounts_empty_for_fresh_player():
    # prepare
    player = Player()

    # check
    assert investments.ownedCounts(player) == {}


def test_buyProperty_spends_money_and_adds_to_portfolio():
    # prepare
    player = Player()
    player.money = 10000
    stats = Stats()
    cost = investments.typeInfo(1)["cost"]

    # call
    bought = investments.buyProperty(player, 1, stats)

    # check
    assert bought is True
    assert player.rentalProperties == [1]
    assert player.money == 10000 - cost
    assert stats.totalPropertiesBought == 1


def test_buyProperty_fails_when_unaffordable():
    # prepare
    player = Player()
    player.money = 0

    # call
    bought = investments.buyProperty(player, 1)

    # check
    assert bought is False
    assert player.rentalProperties == []
    assert player.money == 0


def test_sellProperty_refunds_resale_value_and_removes_one_unit():
    # prepare - two of the same type owned
    player = Player()
    player.rentalProperties = [1, 1]
    player.money = 0
    resaleValue = investments.typeInfo(1)["resaleValue"]

    # call
    sold = investments.sellProperty(player, 1)

    # check - only one unit removed, not both
    assert sold is True
    assert player.rentalProperties == [1]
    assert player.money == resaleValue


def test_sellProperty_fails_when_not_owned():
    # prepare
    player = Player()
    startingMoney = player.money

    # call
    sold = investments.sellProperty(player, 1)

    # check
    assert sold is False
    assert player.money == startingMoney


def test_runDailyIncome_no_op_with_no_properties():
    # prepare
    player = Player()
    player.money = 100
    stats = Stats()

    # call
    income = investments.runDailyIncome(player, stats)

    # check
    assert income == 0
    assert player.money == 100
    assert stats.totalRentalIncome == 0


def test_runDailyIncome_sums_across_owned_properties():
    # prepare - one of type 1, two of type 2
    player = Player()
    player.rentalProperties = [1, 2, 2]
    player.money = 100
    stats = Stats()
    expectedIncome = (
        investments.typeInfo(1)["dailyIncome"]
        + 2 * investments.typeInfo(2)["dailyIncome"]
    )

    # call
    income = investments.runDailyIncome(player, stats)

    # check
    assert income == expectedIncome
    assert player.money == 100 + expectedIncome
    assert stats.totalRentalIncome == expectedIncome
    assert stats.totalMoneyMade == expectedIncome


def test_runDailyIncome_accumulates_across_days():
    # prepare
    player = Player()
    player.rentalProperties = [1]
    stats = Stats()

    # call
    investments.runDailyIncome(player, stats)
    investments.runDailyIncome(player, stats)

    # check - lifetime total accumulates rather than resets
    expectedIncome = investments.typeInfo(1)["dailyIncome"]
    assert stats.totalRentalIncome == expectedIncome * 2
