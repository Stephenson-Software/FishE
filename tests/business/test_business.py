from src.business import boats
from src.business import business
from src.player.player import Player


def test_currentTier_is_zero_without_a_fleet():
    # prepare - nothing on the water
    player = Player()

    # check - currentTier still answers 1 (the catalogue has no tier 0), but
    # the player's own tier is 0, which is what gates every boat-only feature
    assert player.boatTier == 0
    assert player.hasBoat is False
    assert business.currentTier(player) == 1


def test_currentTier_reflects_the_best_boat_in_the_fleet():
    # prepare - a fleet whose boats are not all the same size
    player = Player()
    boats.addBoat(player, 1)
    boats.addBoat(player, 3, boats.ROLE_PIRACY)
    boats.addBoat(player, 2, boats.ROLE_HAULING)

    # check - progress is measured by the best hull owned, not the first bought
    assert business.currentTier(player) == 3
    assert player.boatTier == 3


def test_tierInfo_matches_the_catalogue():
    # check - every tier is complete, and each rung is a real upgrade on the last
    for index, tier in enumerate(business.BOAT_TIERS, start=1):
        assert business.tierInfo(index) is tier
        for field in ("name", "cost", "resaleValue", "maxWorkers", "fishPerDay"):
            assert field in tier
    for smaller, bigger in zip(business.BOAT_TIERS, business.BOAT_TIERS[1:]):
        assert bigger["cost"] > smaller["cost"]
        assert bigger["maxWorkers"] > smaller["maxWorkers"]
        assert bigger["fishPerDay"] > smaller["fishPerDay"]
        assert bigger["exportCapacity"] >= smaller["exportCapacity"]
