# @author Daniel McCoy Stephenson
"""The picture above each place's menu (RFC 0025).

art/stills.json names one still per place - home has one per rung of the
housing ladder - and its alt text; the PNGs are in pictures/ and ride inside
game.zip. Both paths are relative to where the game runs, like schemas/. A
game started anywhere the manifest cannot be read simply shows no pictures -
and the console never shows them at all."""

import json
import os

from housing import housing
from location.enum.locationType import LocationType

MANIFEST_PATH = os.path.join("art", "stills.json")


def load(path=MANIFEST_PATH):
    """{place: alt text} for every still the manifest names, or {}."""
    try:
        with open(path, encoding="utf-8") as manifest:
            stills = json.load(manifest)["stills"]
    except (OSError, ValueError, KeyError, TypeError):
        return {}
    return {
        place: entry["alt"]
        for place, entry in stills.items()
        if isinstance(entry, dict) and entry.get("alt")
    }


# The home still for each rung of housing.HOUSING_TIERS, in the ladder's
# order: home is wherever the player lives, so the picture follows the rung
# (src/housing). Indexed by rung rather than keyed by a tier's name, so the
# ladder's names stay the housing module's own; tests/stills pairs each rung's
# name with its still, so a renamed, added or reordered rung fails there
# instead of quietly showing another rung's house. The homeless rung has no
# roof to draw, so no still.
HOME_STILLS = (
    None,
    "home-rented",
    "home-shack",
    "home-cottage",
    "home-cabin",
    "home-manor",
)


def homeStill(player):
    """The still of the home this player lives in now, or None."""
    rung = housing.currentTier(player)
    if housing.tierInfo(rung)["status"] == "homeless" or rung >= len(HOME_STILLS):
        return None
    return HOME_STILLS[rung]


def placeShown(location, player):
    """The still this location shows, or None.

    Home shows the player's current home - read from player.homeTier each
    time, so a move shows on the next visit home - and a homeless player
    ("You have nowhere to stay tonight") has none."""
    if location == LocationType.HOME:
        return homeStill(player)
    return location


def show(ui, location, alts, player):
    """Put this place's still above the screens that follow, or clear it."""
    place = placeShown(location, player)
    if place in alts:
        ui.setPicture(place, alts[place])
    else:
        ui.setPicture(None)
