# @author Daniel McCoy Stephenson
#
# Home ownership: where the player lives, modeled as a single ladder from
# nothing to owning the nicest place in the village. Every player starts
# Homeless (free, but a real penalty - a much lower energy cap). From there
# they can rent a room (a recurring daily cost, no equity - moving out later
# refunds nothing) or, once they can afford it, buy a home outright. Owned
# tiers trade up/down like real estate: the net cost of a move is the target's
# price minus whatever cash the current home's resale value returns, so
# upgrading costs the difference and downgrading (or selling to go back to
# renting) puts cash back in the player's pocket. Only owned tiers have
# resale value - a rented room was never owned, so leaving one is free but
# refunds nothing.
#
# Investment properties (src/investments) are the opposite idea: assets the
# player owns but doesn't live in, bought purely for income.

HOUSING_TIERS = [
    {"name": "Homeless", "status": "homeless", "maxEnergy": 60},
    {"name": "Rented Room", "status": "renting", "maxEnergy": 90, "dailyRent": 10},
    {
        "name": "Driftwood Shack",
        "status": "owned",
        "cost": 300,
        "resaleValue": 210,
        "maxEnergy": 100,
    },
    {
        "name": "Cozy Cottage",
        "status": "owned",
        "cost": 750,
        "resaleValue": 525,
        "maxEnergy": 120,
    },
    {
        "name": "Sturdy Cabin",
        "status": "owned",
        "cost": 3000,
        "resaleValue": 2100,
        "maxEnergy": 150,
    },
    {
        "name": "Waterfront Manor",
        "status": "owned",
        "cost": 10000,
        "resaleValue": 7000,
        "maxEnergy": 200,
    },
]


def currentTier(player):
    """Resolve the player's effective rung on the housing ladder (0-indexed;
    0 is Homeless, the default for a brand new player)."""
    return max(0, min(player.homeTier, len(HOUSING_TIERS) - 1))


def tierInfo(tier):
    return HOUSING_TIERS[tier]


def maxEnergy(player):
    return tierInfo(currentTier(player))["maxEnergy"]


def netCostToMove(player, targetTier):
    """Net cost to move from the current rung to targetTier: the target's
    purchase price (0 unless it's an owned tier) minus the current rung's
    resale value (0 unless the player currently owns their home). Negative
    means the move pays the player cash back."""
    currentInfo = tierInfo(currentTier(player))
    targetInfo = tierInfo(targetTier)
    proceeds = (
        currentInfo.get("resaleValue", 0) if currentInfo["status"] == "owned" else 0
    )
    price = targetInfo.get("cost", 0) if targetInfo["status"] == "owned" else 0
    return price - proceeds


def moveHome(player, targetTier, stats=None):
    """Move the player to targetTier. Returns True if the move was made;
    False if it would cost money the player doesn't have (a cash-back or
    free move always succeeds)."""
    netCost = netCostToMove(player, targetTier)
    if netCost > 0:
        if not player.canAfford(netCost):
            return False
        player.spendMoney(netCost)
    elif netCost < 0:
        player.money += -netCost

    player.homeTier = targetTier
    if stats is not None:
        stats.highestHomeTier = max(stats.highestHomeTier, targetTier)
    return True


def runDailyRent(player, stats=None):
    """Charge the player's daily rent if they're currently renting. If they
    can't cover it, they're evicted back to Homeless - the same "shrinks
    instead of going into debt" idea used for unaffordable crew wages in
    src/business. Returns the rent actually paid (0 if not renting, or if
    evicted)."""
    info = tierInfo(currentTier(player))
    if info["status"] != "renting":
        return 0

    rent = info["dailyRent"]
    if not player.canAfford(rent):
        player.homeTier = 0  # evicted; no refund, renting was never equity
        return 0

    player.spendMoney(rent)
    if stats is not None:
        stats.totalRentPaid += rent
    return rent
