# @author Daniel McCoy Stephenson
#
# Home ownership: the place you live. Moving to a nicer (or more modest) home
# trades in your current one for the target tier - the net cost is the target
# tier's price minus your current tier's resale value, so upgrading costs the
# difference and downgrading puts cash back in your pocket. Benefits are
# purely personal comfort (a higher energy cap): since you live here, there's
# no rental income - that's what investment properties are for (see
# src/investments), which the player owns but doesn't live in.

# Tier 1 is exactly today's numbers (free, 100 energy), so existing saves and
# default-player behavior are unchanged until a player chooses to move.
HOUSING_TIERS = [
    {"name": "Driftwood Shack", "cost": 0, "resaleValue": 0, "maxEnergy": 100},
    {"name": "Cozy Cottage", "cost": 750, "resaleValue": 525, "maxEnergy": 120},
    {"name": "Sturdy Cabin", "cost": 3000, "resaleValue": 2100, "maxEnergy": 150},
    {"name": "Waterfront Manor", "cost": 10000, "resaleValue": 7000, "maxEnergy": 200},
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


def netCostToMove(player, targetTier):
    """Net cost to trade the current home in for targetTier: the target's
    price minus the current home's resale value. Negative means the move
    pays the player cash back (moving to a more modest home)."""
    current = currentTier(player)
    return tierInfo(targetTier)["cost"] - tierInfo(current)["resaleValue"]


def moveHome(player, targetTier, stats=None):
    """Trade the current home in for targetTier. Returns True if the move was
    made; False if it would cost money the player doesn't have (a cash-back
    move always succeeds)."""
    netCost = netCostToMove(player, targetTier)
    if netCost > 0:
        if not player.canAfford(netCost):
            return False
        player.spendMoney(netCost)
    else:
        player.money += -netCost

    player.homeTier = targetTier
    if stats is not None:
        stats.highestHomeTier = max(stats.highestHomeTier, targetTier)
    return True
