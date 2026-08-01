import pytest
from unittest.mock import patch

from src.business import business
from src.business import export
from src.player.player import Player
from src.stats.stats import Stats


def createExporter(tier=2, money=1000, fish=None):
    player = Player()
    player.hasBoat = True
    player.boatTier = tier
    player.money = money
    for species, count in (fish or {}).items():
        player.addFish(species, count)
    return player


def test_rowboat_cannot_export():
    # prepare - the starter boat
    player = createExporter(tier=1)

    # check - exporting is a reason to upgrade, not something tier 1 can do
    assert export.exportCapacity(player) == 0
    assert export.canExport(player) is False
    assert export.availableMarkets(player) == []


def test_no_boat_cannot_export():
    # prepare
    player = Player()

    # check
    assert export.exportCapacity(player) == 0
    assert export.canExport(player) is False
    assert export.availableMarkets(player) == []


def test_trawler_reaches_the_nearer_markets():
    # prepare
    player = createExporter(tier=2)

    # call
    markets = export.availableMarkets(player)

    # check - every market a Trawler can reach allows tier 2
    assert export.canExport(player) is True
    assert markets
    assert all(market["minBoatTier"] <= 2 for market in markets)
    assert "Thornhaven" not in [market["name"] for market in markets]


def test_fishing_fleet_reaches_every_market():
    # prepare
    player = createExporter(tier=3)

    # check
    assert export.availableMarkets(player) == export.EXPORT_MARKETS


def test_capacity_grows_with_the_boat():
    # check - a bigger boat is what raises the ceiling on a run
    assert (
        export.exportCapacity(createExporter(tier=2))
        == business.tierInfo(2)["exportCapacity"]
    )
    assert export.exportCapacity(createExporter(tier=3)) > export.exportCapacity(
        createExporter(tier=2)
    )


def test_buildCargo_loads_the_most_valuable_fish_first():
    # prepare - more fish than a Trawler's hold can take
    capacity = business.tierInfo(2)["exportCapacity"]
    player = createExporter(
        tier=2, fish={"Minnow": capacity, "Golden Koi": 2, "Marlin": 3}
    )

    # call
    cargo = export.buildCargo(player)

    # check - the hold fills with the best fish, minnows are left behind
    assert len(cargo) == capacity
    assert cargo[:2] == ["Golden Koi", "Golden Koi"]
    assert cargo[2:5] == ["Marlin"] * 3
    assert set(cargo[5:]) == {"Minnow"}


def test_buildCargo_takes_everything_when_under_capacity():
    # prepare
    player = createExporter(tier=2, fish={"Bass": 10})

    # call
    cargo = export.buildCargo(player)

    # check
    assert cargo == ["Bass"] * 10


def test_estimateEarnings_is_net_of_freight():
    # prepare - a cargo of a species with a known value range
    market = {"name": "Test", "priceMultiplier": 2.0, "shippingCost": 10}
    cargo = ["Bass"] * 4  # Bass is $5-9, midpoint $7

    # call
    estimate = export.estimateEarnings(cargo, market)

    # check - 4 x $7 x 2.0, less the $10 freight
    assert estimate == 4 * 7 * 2.0 - 10


def test_estimateEarnings_can_be_negative_for_a_small_load():
    # prepare - one fish against the most expensive freight
    market = max(export.EXPORT_MARKETS, key=lambda m: m["shippingCost"])

    # call
    estimate = export.estimateEarnings(["Minnow"], market)

    # check - the player is shown the loss before they commit to it
    assert estimate < 0


def test_runExport_sells_the_hold_at_a_premium():
    # prepare - a full Trawler load of Bass, with fishValue pinned to the top
    # of the range so the payout is exact rather than a range
    capacity = business.tierInfo(2)["exportCapacity"]
    player = createExporter(tier=2, money=1000, fish={"Bass": capacity})
    market = export.EXPORT_MARKETS[0]
    stats = Stats()

    # call
    with patch("src.business.export.fish.fishValue", return_value=9):
        summary = export.runExport(player, market, stats)

    # check - every fish sold at the market's multiple of its own value
    expected = capacity * 9 * market["priceMultiplier"]
    assert summary["shipped"] is True
    assert summary["fishExported"] == capacity
    assert summary["gross"] == pytest.approx(expected)
    assert summary["earned"] == pytest.approx(expected - market["shippingCost"])
    assert player.fishCount == 0
    assert player.money == pytest.approx(1000 - market["shippingCost"] + expected)


def test_runExport_leaves_fish_that_did_not_fit():
    # prepare - more fish than the hold takes
    capacity = business.tierInfo(2)["exportCapacity"]
    player = createExporter(tier=2, fish={"Minnow": capacity + 30})

    # call
    summary = export.runExport(player, export.EXPORT_MARKETS[0])

    # check - the overflow stays in the inventory for another run
    assert summary["fishExported"] == capacity
    assert player.fishCount == 30
    assert player.fishByType == {"Minnow": 30}


def test_runExport_charges_freight_up_front():
    # prepare - enough money for the freight and nothing else
    market = export.EXPORT_MARKETS[1]
    player = createExporter(tier=2, money=market["shippingCost"], fish={"Bass": 5})

    # call
    summary = export.runExport(player, market)

    # check - the freight came out of the player's pocket, not the proceeds
    assert summary["shipped"] is True
    assert player.money == pytest.approx(summary["gross"])


def test_runExport_refuses_when_freight_is_unaffordable():
    # prepare - a hold full of fish but not enough cash to sail
    market = export.EXPORT_MARKETS[1]
    player = createExporter(tier=2, money=market["shippingCost"] - 1, fish={"Bass": 50})

    # call
    summary = export.runExport(player, market)

    # check - refused outright rather than putting the player into debt
    assert summary["shipped"] is False
    assert summary["reason"] == "cannot_afford_freight"
    assert player.fishCount == 50
    assert player.money == market["shippingCost"] - 1


def test_runExport_never_puts_the_player_into_debt():
    # prepare - the worst case the menu allows: one cheap fish, big freight
    market = max(export.EXPORT_MARKETS, key=lambda m: m["shippingCost"])
    player = createExporter(tier=3, money=market["shippingCost"], fish={"Minnow": 1})

    # call
    summary = export.runExport(player, market)

    # check - a losing run is allowed, but money can't go below zero (the
    # player schema requires it)
    assert summary["shipped"] is True
    assert summary["earned"] < 0
    assert player.money >= 0


def test_runExport_refuses_an_empty_hold():
    # prepare
    player = createExporter(tier=2)

    # call
    summary = export.runExport(player, export.EXPORT_MARKETS[0])

    # check
    assert summary["shipped"] is False
    assert summary["reason"] == "empty_hold"
    assert player.money == 1000


def test_runExport_refuses_a_boat_that_cannot_make_the_crossing():
    # prepare - a Trawler aiming at the tier 3 market
    farMarket = next(m for m in export.EXPORT_MARKETS if m["minBoatTier"] == 3)
    player = createExporter(tier=2, fish={"Bass": 100})

    # call
    summary = export.runExport(player, farMarket)

    # check
    assert summary["shipped"] is False
    assert summary["reason"] == "boat_too_small"
    assert player.fishCount == 100


def test_runExport_refuses_a_rowboat():
    # prepare
    player = createExporter(tier=1, fish={"Bass": 100})

    # call
    summary = export.runExport(player, export.EXPORT_MARKETS[0])

    # check
    assert summary["shipped"] is False
    assert summary["reason"] == "boat_too_small"


def test_runExport_records_lifetime_stats():
    # prepare
    player = createExporter(tier=2, fish={"Bass": 10})
    market = export.EXPORT_MARKETS[0]
    stats = Stats()

    # call
    summary = export.runExport(player, market, stats)

    # check - gross counts toward money made; freight is tracked separately
    assert stats.totalFishExported == 10
    assert stats.totalMoneyFromExports == pytest.approx(summary["gross"])
    assert stats.totalMoneyMade == pytest.approx(summary["gross"])
    assert stats.totalShippingPaid == market["shippingCost"]


def test_runExport_handles_a_legacy_untyped_hold():
    # prepare - a save from before fish had species: a count with no breakdown
    player = createExporter(tier=2)
    player.fishCount = 20

    # call
    summary = export.runExport(player, export.EXPORT_MARKETS[0])

    # check - untyped fish still ship, priced at the old flat range
    assert summary["shipped"] is True
    assert summary["fishExported"] == 20
    assert player.fishCount == 0
    assert summary["gross"] > 0


def test_operator_mode_ignores_the_freight_bill():
    # prepare - the debug cheat, with no money at all
    market = export.EXPORT_MARKETS[1]
    player = createExporter(tier=2, money=0, fish={"Bass": 5})
    player.operatorMode = True

    # call
    summary = export.runExport(player, market)

    # check - freight neither blocks the run nor comes out of the wallet
    assert summary["shipped"] is True
    assert player.money == pytest.approx(summary["gross"])


def test_every_market_pays_a_premium_over_the_village_shop():
    # check - shipping fish out has to beat selling them at home, or the
    # freight and the lost day would never be worth it
    for market in export.EXPORT_MARKETS:
        assert market["priceMultiplier"] > 1


def test_markets_trade_a_bigger_premium_for_a_bigger_freight_bill():
    # check - each market up the list pays more per fish and costs more to
    # reach, which is what makes the choice depend on the size of the load
    for nearer, farther in zip(export.EXPORT_MARKETS, export.EXPORT_MARKETS[1:]):
        assert farther["priceMultiplier"] > nearer["priceMultiplier"]
        assert farther["shippingCost"] > nearer["shippingCost"]


def test_every_market_is_reachable_by_some_boat():
    # check - no market is gated behind a boat tier that doesn't exist
    for market in export.EXPORT_MARKETS:
        assert 1 <= market["minBoatTier"] <= len(business.BOAT_TIERS)
        assert business.tierInfo(market["minBoatTier"])["exportCapacity"] > 0


def test_estimateEarnings_prices_a_legacy_untyped_hold():
    # prepare - a save from before fish had species, so bestFirst yields
    # untyped entries with no catalogue range to read
    market = {"name": "Test", "priceMultiplier": 2.0, "shippingCost": 0}

    # call
    estimate = export.estimateEarnings([None, None], market)

    # check - priced at the middle of the original flat $3-5 range
    assert estimate == 2 * 4.0 * 2.0
