import random

# @author Daniel McCoy Stephenson
#
# Catalogue of fish species. Each has a rarity weight (used to pick which
# species is hooked on a trip) and a value range (used when selling). Rarer
# fish are worth more, so what you catch — not just how many — now matters.

FISH_TYPES = [
    {"name": "Minnow", "weight": 60, "minValue": 2, "maxValue": 4},
    {"name": "Bass", "weight": 30, "minValue": 5, "maxValue": 9},
    {"name": "Marlin", "weight": 9, "minValue": 15, "maxValue": 25},
    {"name": "Golden Koi", "weight": 1, "minValue": 50, "maxValue": 80},
]


def getFishType(name):
    """Return the catalogue entry for a species name, or None if unknown."""
    for fishType in FISH_TYPES:
        if fishType["name"] == name:
            return fishType
    return None


def rollFishType():
    """Pick a species weighted by rarity and return its name."""
    weights = [fishType["weight"] for fishType in FISH_TYPES]
    return random.choices(FISH_TYPES, weights=weights)[0]["name"]


def bestFirst(fishByType, fishCount):
    """One entry per held fish, most valuable species first.

    Shared by every buyer that can only take part of a hoard - the shop (whose
    daily budget runs out) and the export markets (whose hold has a capacity) -
    so the fish left behind are always the cheapest ones. A legacy save with
    only an aggregate count and no species breakdown yields that many unknown
    entries, which fishValue prices at the original flat range."""
    if not fishByType:
        return [None] * fishCount
    queue = []
    for species, count in fishByType.items():
        queue.extend([species] * count)
    queue.sort(key=lambda s: (getFishType(s) or {}).get("maxValue", 0), reverse=True)
    return queue


def fishValue(name):
    """Return a per-fish sale price for the given species.

    Falls back to the original flat $3-5 range for an unknown species so that
    legacy saves (which tracked only an undifferentiated fish count) still sell.
    """
    fishType = getFishType(name)
    if fishType is None:
        return random.randint(3, 5)
    return random.randint(fishType["minValue"], fishType["maxValue"])
