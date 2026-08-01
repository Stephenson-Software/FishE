# @author Daniel McCoy Stephenson
#
# The fishing business: once the player owns a boat they can hire villagers as
# workers, who bring in a passive catch each day in exchange for a daily wage.
# This turns accumulated money into ongoing production rather than just a
# number that grows. Every hire is a named villager (see src/npc/villagers)
# the player can then talk to at the docks; player.workers remains the
# headcount the production maths runs on.

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
        "resaleValue": int(BOAT_PRICE * 0.7),
        "maxWorkers": MAX_WORKERS,
        "fishPerDay": WORKER_FISH_PER_DAY,
    },
    {
        "name": "Trawler",
        "cost": 2000,
        "resaleValue": 1400,
        "maxWorkers": 8,
        "fishPerDay": 7,
    },
    {
        "name": "Fishing Fleet",
        "cost": 6000,
        "resaleValue": 4200,
        "maxWorkers": 12,
        "fishPerDay": 10,
    },
]


def currentTier(player):
    """Resolve the player's effective boat tier (always >= 1 once they own a
    boat). Older saves/tests may set hasBoat without ever touching boatTier,
    so an unset (0) tier is treated as tier 1 - the original boat."""
    return player.boatTier if player.boatTier > 0 else 1


def tierInfo(tier):
    return BOAT_TIERS[tier - 1]


def sellBoat(player):
    """Sell the boat back for its current tier's resale value. Returns True if
    a boat was sold; False if the player didn't own one. Any remaining crew is
    dismissed too, since they have nowhere left to work."""
    if not player.hasBoat:
        return False
    player.money += tierInfo(currentTier(player))["resaleValue"]
    player.hasBoat = False
    player.boatTier = 0
    player.workers = 0
    player.hiredWorkers = []
    return True


def _trimCrewRoster(player):
    """Drop named crew until the roster fits the headcount, and return the
    names dropped (most recent hire first).

    workers counts every hand aboard, named or not, so any unnamed hands from
    an older save are absorbed before a named villager is asked to leave."""
    dropped = []
    while len(player.hiredWorkers) > player.workers:
        dropped.append(player.hiredWorkers.pop())
    return dropped


def hireWorker(player, name=None):
    """Take on one more hand, optionally a named villager. Returns True if the
    hire happened; False if there's no boat, no free berth, or that villager
    is already on the crew."""
    if not player.hasBoat:
        return False
    if player.workers >= tierInfo(currentTier(player))["maxWorkers"]:
        return False
    if name is not None:
        if name in player.hiredWorkers:
            return False
        player.hiredWorkers.append(name)
    player.workers += 1
    return True


def dismissWorker(player, name=None):
    """Let one hand go. With a name, that specific villager leaves; without
    one, an unnamed hand goes first (see _trimCrewRoster). Returns True if
    someone was dismissed; False if there was no such crew member."""
    if player.workers <= 0:
        return False
    if name is not None:
        if name not in player.hiredWorkers:
            return False
        player.hiredWorkers.remove(name)
    player.workers -= 1
    _trimCrewRoster(player)
    return True


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
        "quitNames": [],
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
        summary["quitNames"] = _trimCrewRoster(player)
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
