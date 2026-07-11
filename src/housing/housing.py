# @author Daniel McCoy Stephenson
#
# Home ownership: a second property-ownership track alongside the fishing
# business (see src/business). Upgrading your home raises the energy cap you
# refill to when you sleep and adds a small passive daily rental income (a
# spare room let out to visiting fishermen), independent of any crew wages.

# Housing tiers: tier 1 is exactly today's numbers (free, 100 energy, no
# income), so existing saves and default-player behavior are unchanged until a
# player chooses to upgrade - the same backward-compat approach BOAT_TIERS
# uses in src/business/business.py.
HOUSING_TIERS = [
    {"name": "Driftwood Shack", "cost": 0, "maxEnergy": 100, "dailyRentalIncome": 0},
    {"name": "Cozy Cottage", "cost": 750, "maxEnergy": 120, "dailyRentalIncome": 5},
    {"name": "Sturdy Cabin", "cost": 3000, "maxEnergy": 150, "dailyRentalIncome": 15},
    {
        "name": "Waterfront Manor",
        "cost": 10000,
        "maxEnergy": 200,
        "dailyRentalIncome": 40,
    },
]


def currentTier(player):
    """Resolve the player's effective home tier (always >= 1). Older
    saves/tests may never touch homeTier, so an unset (0) tier is treated as
    tier 1 - the original Driftwood Shack."""
    return player.homeTier if player.homeTier > 0 else 1


def tierInfo(tier):
    return HOUSING_TIERS[tier - 1]


def maxEnergy(player):
    return tierInfo(currentTier(player))["maxEnergy"]


def runDailyRentalIncome(player, stats=None):
    """Apply one day of passive rental income from the player's home and
    return the amount earned. A no-op at tier 1, which pays no rent."""
    income = tierInfo(currentTier(player))["dailyRentalIncome"]
    if income <= 0:
        return 0

    player.money += income
    if stats is not None:
        stats.totalRentalIncome += income
        stats.totalMoneyMade += income
    return income
