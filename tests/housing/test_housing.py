from src.housing import housing
from src.player.player import Player
from src.stats.stats import Stats


def test_currentTier_defaults_to_1_when_unset():
    # prepare - an older save/test that never touches homeTier
    player = Player()
    player.homeTier = 0

    # check - treated as the original (tier 1) Driftwood Shack
    assert housing.currentTier(player) == 1


def test_currentTier_reflects_moves():
    # prepare
    player = Player()
    player.homeTier = 3

    # check
    assert housing.currentTier(player) == 3


def test_tier1_matches_original_free_defaults():
    # check - tier 1 preserves today's numbers exactly, so a fresh player's
    # behavior is unchanged (free, no resale value, 100 energy cap)
    info = housing.tierInfo(1)
    assert info["cost"] == 0
    assert info["resaleValue"] == 0
    assert info["maxEnergy"] == 100


def test_maxEnergy_reflects_tier():
    # prepare
    player = Player()
    player.homeTier = 2

    # check
    assert housing.maxEnergy(player) == housing.tierInfo(2)["maxEnergy"]
    assert housing.maxEnergy(player) > housing.tierInfo(1)["maxEnergy"]


def test_netCostToMove_up_from_free_tier_equals_target_price():
    # prepare - tier 1 has no resale value, so moving up costs the full price
    player = Player()

    # check
    assert housing.netCostToMove(player, 2) == housing.tierInfo(2)["cost"]


def test_netCostToMove_up_is_discounted_by_current_resale_value():
    # prepare - moving from tier 2 to tier 3 nets the tier-2 resale value off
    player = Player()
    player.homeTier = 2

    # check
    expected = housing.tierInfo(3)["cost"] - housing.tierInfo(2)["resaleValue"]
    assert housing.netCostToMove(player, 3) == expected


def test_netCostToMove_down_can_be_negative():
    # prepare - moving from tier 2 down to the free tier 1 should pay cash
    # back (tier 2's resale value exceeds tier 1's price of 0)
    player = Player()
    player.homeTier = 2

    # check
    assert housing.netCostToMove(player, 1) < 0


def test_moveHome_up_spends_net_cost():
    # prepare
    player = Player()
    player.money = 1000
    stats = Stats()
    netCost = housing.netCostToMove(player, 2)

    # call
    moved = housing.moveHome(player, 2, stats)

    # check
    assert moved is True
    assert player.homeTier == 2
    assert player.money == 1000 - netCost
    assert stats.highestHomeTier == 2


def test_moveHome_up_fails_when_unaffordable():
    # prepare
    player = Player()
    player.money = 0

    # call
    moved = housing.moveHome(player, 2)

    # check - nothing changes
    assert moved is False
    assert player.homeTier == 1
    assert player.money == 0


def test_moveHome_down_pays_cash_back():
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


def test_moveHome_highestHomeTier_does_not_regress():
    # prepare - a player who has previously owned a higher tier
    player = Player()
    player.homeTier = 3
    stats = Stats()
    stats.highestHomeTier = 3

    # call - move back down
    housing.moveHome(player, 1, stats)

    # check - the lifetime "highest owned" stat remembers the peak
    assert player.homeTier == 1
    assert stats.highestHomeTier == 3
