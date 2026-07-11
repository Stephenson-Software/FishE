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

# Shared string so every call site that surfaces an eviction to the player
# (see TimeService.increaseDay's return value) says the same thing.
EVICTION_MESSAGE = "You couldn't cover your rent and were evicted from your room!"

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
    if tier < 0 or tier >= len(HOUSING_TIERS):
        raise ValueError("Invalid housing tier: %r" % (tier,))
    return HOUSING_TIERS[tier]


def maxEnergy(player):
    return tierInfo(currentTier(player))["maxEnergy"]


def netCostToMove(player, targetTier):
    """Net cost to move from the current rung to targetTier: the target's
    purchase price minus the current rung's resale value. Only owned tiers
    define a "cost"/"resaleValue" at all, so a homeless or renting rung on
    either side of the move contributes 0 via the dict defaults below.
    Negative means the move pays the player cash back."""
    currentInfo = tierInfo(currentTier(player))
    targetInfo = tierInfo(targetTier)
    return targetInfo.get("cost", 0) - currentInfo.get("resaleValue", 0)


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
    # A move to a lower-cap tier (including eviction) shouldn't leave the
    # player above their new cap until their next sleep.
    player.energy = min(player.energy, tierInfo(targetTier)["maxEnergy"])
    if stats is not None:
        stats.highestHomeTier = max(stats.highestHomeTier, targetTier)
    return True


def runDailyRent(player, stats=None):
    """Charge the player's daily rent if they're currently renting. If they
    can't cover it, they're evicted back to Homeless - the same "shrinks
    instead of going into debt" idea used for unaffordable crew wages in
    src/business. Returns a summary dict: {"rentPaid": int, "evicted": bool}
    so callers can tell the player what happened."""
    info = tierInfo(currentTier(player))
    if info["status"] != "renting":
        return {"rentPaid": 0, "evicted": False}

    rent = info["dailyRent"]
    if not player.canAfford(rent):
        # Evicted; no refund, renting was never equity. Routed through
        # moveHome so eviction gets the same energy-cap reconciliation as
        # any other move, instead of duplicating that logic here.
        moveHome(player, 0, stats)
        return {"rentPaid": 0, "evicted": True}

    player.spendMoney(rent)
    if stats is not None:
        stats.totalRentPaid += rent
    return {"rentPaid": rent, "evicted": False}
