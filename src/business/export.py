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

def holdFor(boat):
    """How many fish this boat carries on an export run, whatever her state.

    A hauling boat's hold is fitted for cargo, so it beats a same-sized hull in
    any other role - which is the passive half of what dedicating a boat to
    hauling buys you."""
    capacity = business.tierInfo(boat["tier"]).get("exportCapacity", 0)
    if boat["role"] == boats.ROLE_HAULING:
        capacity = int(capacity * boats.HAULING_CAPACITY_BONUS)
    return capacity


def canSail(boat):
    """Whether this boat can make a crossing at all. The same hull test Take
    the Helm uses (Docks.readyToSail), so a boat the docks screen calls too
    damaged to sail isn't sent across the water anyway (#279). No crew is
    needed - the player sails the run."""
    return boats.isSeaworthy(boat) and not boats.isAtSea(boat)


def exportBoat(player):
    """The boat an export run would actually sail on - the seaworthy one with
    the biggest effective hold. None if nothing in the fleet that could sail
    can make the crossing."""
    best = None
    bestCapacity = 0
    for boat in player.boats:
        if not canSail(boat):
            continue
        capacity = holdFor(boat)
        if capacity > bestCapacity:
            best, bestCapacity = boat, capacity
    return best


def exportCapacity(player):
    """How many fish one run can carry: the hold of the boat it sails on (0
    with no boat, or none both seaworthy and big enough to make the crossing)."""
    runner = exportBoat(player)
    return holdFor(runner) if runner else 0


def canExport(player):
    """Whether the player's fleet can export at all."""
    return exportCapacity(player) > 0


def runnerTier(player):
    """The hull tier the run actually sails on, which is what decides how far
    it can go - not the fleet's best hull, which may be laid up for repairs.
    0 if no boat can make the crossing."""
    runner = exportBoat(player)
    return runner["tier"] if runner else 0


def availableMarkets(player):
    """The markets the boat an export run would sail on can reach, in order."""
    tier = runnerTier(player)
    return [market for market in EXPORT_MARKETS if market["minBoatTier"] <= tier]


def _hullRefusal(player, minTier):
    """Why no boat can make a crossing that needs minTier: one big enough is
    only laid up with damage, or there's none big enough at all."""
    for boat in player.boats:
        if boat["tier"] >= minTier and not boats.isSeaworthy(boat):
            return "boat_too_damaged"
    return "boat_too_small"


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

    if exportCapacity(player) <= 0 or market["minBoatTier"] > runnerTier(player):
        summary["reason"] = _hullRefusal(player, market["minBoatTier"])
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
