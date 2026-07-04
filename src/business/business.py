# @author Daniel McCoy Stephenson
#
# The fishing business: once the player owns a boat they can hire workers, who
# bring in a passive catch each day in exchange for a daily wage. This turns
# accumulated money into ongoing production rather than just a number that grows.

from fish import fish

BOAT_PRICE = 500
MAX_WORKERS = 5
WORKER_DAILY_WAGE = 10
WORKER_FISH_PER_DAY = 5

# Boat upgrades: a bigger boat holds more crew and each worker lands more fish
# per day. Tier 1 is exactly the original flat boat/crew numbers above, so
# existing saves and behavior are unchanged until a player chooses to upgrade.
BOAT_TIERS = [
    {
        "name": "Rowboat",
        "cost": BOAT_PRICE,
        "maxWorkers": MAX_WORKERS,
        "fishPerDay": WORKER_FISH_PER_DAY,
    },
    {"name": "Trawler", "cost": 2000, "maxWorkers": 8, "fishPerDay": 7},
    {"name": "Fishing Fleet", "cost": 6000, "maxWorkers": 12, "fishPerDay": 10},
]


def currentTier(player):
    """Resolve the player's effective boat tier (always >= 1 once they own a
    boat). Older saves/tests may set hasBoat without ever touching boatTier,
    so an unset (0) tier is treated as tier 1 - the original boat."""
    return player.boatTier if player.boatTier > 0 else 1


def tierInfo(tier):
    return BOAT_TIERS[tier - 1]


def runDailyProduction(player, stats=None):
    """Apply one day of the fishing business and return a summary.

    Each worker catches WORKER_FISH_PER_DAY fish for WORKER_DAILY_WAGE in wages.
    If the player can't cover the full payroll, the workers they can't pay quit
    (so an over-hired, broke business shrinks instead of going into debt)."""
    summary = {
        "workers": player.workers,
        "fishCaught": 0,
        "wagesPaid": 0,
        "quit": 0,
    }
    if not player.hasBoat or player.workers <= 0:
        return summary

    if player.operatorMode:
        affordable = player.workers
    else:
        affordable = min(player.workers, int(player.money // WORKER_DAILY_WAGE))
    if affordable < player.workers:
        summary["quit"] = player.workers - affordable
        player.workers = affordable
    summary["workers"] = player.workers

    if affordable <= 0:
        return summary

    wages = affordable * WORKER_DAILY_WAGE
    player.spendMoney(wages)
    # Each worker fishes the same waters as the player, landing a rarity-rolled
    # species (not just the cheapest one), so the crew's income is competitive
    # with simply upgrading your own gear. A bigger boat means a bigger catch
    # per worker, not just more worker slots.
    fishPerWorker = tierInfo(currentTier(player))["fishPerDay"]
    caught = 0
    for _ in range(affordable):
        player.addFish(fish.rollFishType(), fishPerWorker)
        caught += fishPerWorker
    summary["wagesPaid"] = wages
    summary["fishCaught"] = caught
    if stats is not None:
        stats.totalFishCaught += caught
        stats.totalFishCaughtByCrew += caught
        stats.totalWagesPaid += wages
        stats.daysInBusiness += 1
    return summary
