# @author Daniel McCoy Stephenson
#
# The economics of boats: what each hull costs, how much crew it carries, and
# what that crew is worth per day.
#
# This module is deliberately just the catalogue plus the numbers derived from
# it, with no knowledge of the fleet - so src/business/boats.py (the fleet,
# crew assignment and daily production) can depend on it without a cycle.

BOAT_PRICE = 500
MAX_WORKERS = 5
WORKER_DAILY_WAGE = 10
WORKER_FISH_PER_DAY = 5

# Boat upgrades: a bigger boat holds more crew and each worker lands more fish
# per day. Tier 1 is exactly the original flat boat/crew numbers above, so
# existing saves and behavior are unchanged until a player chooses to upgrade.
#
# exportCapacity is how many fish the boat can carry to another village in one
# run (see src/business/export.py); a Rowboat can't make the crossing at all,
# so tier 1 is 0 and exporting is a genuine reason to upgrade.
BOAT_TIERS = [
    {
        "name": "Rowboat",
        "cost": BOAT_PRICE,
        "resaleValue": int(BOAT_PRICE * 0.7),
        "maxWorkers": MAX_WORKERS,
        "fishPerDay": WORKER_FISH_PER_DAY,
        "exportCapacity": 0,
    },
    {
        "name": "Trawler",
        "cost": 2000,
        "resaleValue": 1400,
        "maxWorkers": 8,
        "fishPerDay": 7,
        "exportCapacity": 250,
    },
    {
        "name": "Fishing Fleet",
        "cost": 6000,
        "resaleValue": 4200,
        "maxWorkers": 12,
        "fishPerDay": 10,
        "exportCapacity": 600,
    },
]


def currentTier(player):
    """The tier the player's business counts as: their best hull, and always
    >= 1 once they own anything at all.

    Everything that stages itself on progress - NPC dialogue, which export
    markets are reachable - means the best boat in the fleet, not the first
    one bought or the one currently selected."""
    return player.boatTier if player.boatTier > 0 else 1


def tierInfo(tier):
    return BOAT_TIERS[tier - 1]
