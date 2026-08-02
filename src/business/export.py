# @author Daniel McCoy Stephenson
#
# Exporting fish to neighbouring villages.
#
# Gilbert's shop only has SHOP_DAILY_BUDGET to spend a day, so a full crew
# eventually lands more fish than the village's only buyer can absorb and the
# hoard just sits there. A boat big enough to make the crossing - a Trawler or
# better - opens up buyers who have no daily budget at all. What limits an
# export run instead is the hold's capacity (per boat tier, see
# business.BOAT_TIERS), the freight charged up front, and the day the round
# trip costs.
#
# Each market trades a bigger premium for a bigger freight bill, so which one
# is worth sailing to depends on how much fish is in the hold: a small load
# barely covers Thornhaven's freight, while a full Fishing Fleet's hold earns
# far more there than it would down the coast at Saltmarsh.

from business import business
from business import boats
from fish import fish


EXPORT_MARKETS = [
    {
        "name": "Saltmarsh",
        "description": "a half-day down the coast; modest prices, cheap freight",
        "minBoatTier": 2,
        "priceMultiplier": 1.2,
        "shippingCost": 25,
    },
    {
        "name": "Kestrel Cove",
        "description": "a bigger harbour town that pays well for a real haul",
        "minBoatTier": 2,
        "priceMultiplier": 1.5,
        "shippingCost": 250,
    },
    {
        "name": "Thornhaven",
        "description": "the far city market - only a Fishing Fleet can make the crossing",
        "minBoatTier": 3,
        "priceMultiplier": 2.0,
        "shippingCost": 900,
    },
]

def exportCapacity(player):
    """How many fish one run can carry (0 with no boat, or none big enough to
    make the crossing).

    The run goes out on whichever boat carries the most: a hauling boat's hold
    is fitted for cargo, so it beats a same-sized hull in any other role - which
    is the passive half of what dedicating a boat to hauling buys you."""
    best = 0
    for boat in player.boats:
        capacity = business.tierInfo(boat["tier"]).get("exportCapacity", 0)
        if boat["role"] == boats.ROLE_HAULING:
            capacity = int(capacity * boats.HAULING_CAPACITY_BONUS)
        best = max(best, capacity)
    return best


def exportBoat(player):
    """The boat an export run would actually sail on - the one with the biggest
    effective hold. None if nothing in the fleet can make the crossing."""
    best = None
    bestCapacity = 0
    for boat in player.boats:
        capacity = business.tierInfo(boat["tier"]).get("exportCapacity", 0)
        if boat["role"] == boats.ROLE_HAULING:
            capacity = int(capacity * boats.HAULING_CAPACITY_BONUS)
        if capacity > bestCapacity:
            best, bestCapacity = boat, capacity
    return best


def canExport(player):
    """Whether the player's boat can export at all."""
    return exportCapacity(player) > 0


def availableMarkets(player):
    """The markets the player's fleet can reach, in order."""
    if not player.boats:
        return []
    tier = business.currentTier(player)
    return [market for market in EXPORT_MARKETS if market["minBoatTier"] <= tier]


def buildCargo(player):
    """The fish that would be loaded on the next run: the most valuable species
    first, up to what the hold can carry."""
    queue = fish.bestFirst(player.fishByType, player.fishCount)
    return queue[: exportCapacity(player)]


def estimateEarnings(cargo, market):
    """Roughly what a cargo fetches at a market, net of freight.

    Each fish sells for a random price inside its species' range, so this uses
    the midpoint of that range - it's shown to the player before they commit,
    where an honest estimate matters more than a precise one."""
    gross = 0.0
    for species in cargo:
        fishType = fish.getFishType(species)
        if fishType is None:
            # Legacy untyped fish, priced at the middle of the old $3-5 range.
            midpoint = 4.0
        else:
            midpoint = (fishType["minValue"] + fishType["maxValue"]) / 2
        gross += midpoint * market["priceMultiplier"]
    return gross - market["shippingCost"]


def runExport(player, market, stats=None):
    """Ship a hold of fish to another village and return a summary.

    Freight is charged up front rather than deducted from the proceeds, so a
    run can never put the player into debt - if they can't cover it, the run
    is refused with a reason instead. The summary's "reason" is None on a
    successful run and otherwise names why nothing shipped, so the caller can
    tell the player what to do about it."""
    summary = {
        "market": market["name"],
        "shipped": False,
        "reason": None,
        "fishExported": 0,
        "gross": 0.0,
        "shippingCost": market["shippingCost"],
        "earned": 0.0,
    }

    if exportCapacity(player) <= 0:
        summary["reason"] = "boat_too_small"
        return summary
    if market["minBoatTier"] > business.currentTier(player):
        summary["reason"] = "boat_too_small"
        return summary
    if player.fishCount <= 0:
        summary["reason"] = "empty_hold"
        return summary
    if not player.canAfford(market["shippingCost"]):
        summary["reason"] = "cannot_afford_freight"
        return summary

    cargo = buildCargo(player)
    player.spendMoney(market["shippingCost"])

    gross = 0.0
    for species in cargo:
        value = fish.fishValue(species) * market["priceMultiplier"]
        gross += value
        player.removeFish(species)
    player.money += gross

    summary["shipped"] = True
    summary["fishExported"] = len(cargo)
    summary["gross"] = gross
    summary["earned"] = gross - market["shippingCost"]

    if stats is not None:
        stats.totalMoneyMade += gross
        stats.totalFishExported += len(cargo)
        stats.totalMoneyFromExports += gross
        stats.totalShippingPaid += market["shippingCost"]
    return summary
