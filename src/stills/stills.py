# @author Daniel McCoy Stephenson
"""The picture above each place's menu (RFC 0025).

art/stills.json names one still per place and its alt text; the PNGs are in
pictures/ and ride inside game.zip. Both paths are relative to where the game
runs, like schemas/. A game started anywhere the manifest cannot be read
simply shows no pictures - and the console never shows them at all."""

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


def placeShown(location, player):
    """The still this location shows, or None.

    Home is drawn as a room, and a homeless player ("You have nowhere to stay
    tonight") has none - so home shows no picture until there is one."""
    if location == LocationType.HOME:
        status = housing.tierInfo(housing.currentTier(player))["status"]
        if status == "homeless":
            return None
    return location


def show(ui, location, alts, player):
    """Put this place's still above the screens that follow, or clear it."""
    place = placeShown(location, player)
    if place in alts:
        ui.setPicture(place, alts[place])
    else:
        ui.setPicture(None)
