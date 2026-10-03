# @author Daniel McCoy Stephenson
"""FishE's achievements on arcade (Stephenson-Software RFC 0014), via tak.arcade.

Each function here is called at the moment something is earned - a milestone
announced, the goal reached, the run retired - and on load, to re-assert what
an existing save has already earned. tak.arcade.unlock is fire-and-forget and
idempotent: it does nothing outside the browser on arcade or for a player who
is not signed in, and the service ignores a repeat. Nothing here reads or
writes save state beyond reading stats.earnedMilestones; a failure is
swallowed, never raised into the game.
"""

from achievements.achievements import (
    RETIRED_ARCADE_ID,
    arcadeIdForName,
)


def unlock(achievementId):
    """Report one achievement. Never raises."""
    try:
        from tak import arcade

        arcade.unlock(achievementId)
    except Exception:
        pass


def milestonesEarned(milestones):
    """Report the arcade ids of milestones just earned (rows of MILESTONES)."""
    for milestone in milestones:
        achievementId = milestone.get("arcadeId")
        if achievementId:
            unlock(achievementId)


def nameEarned(name):
    """Report the arcade id an earned milestone name (or the goal) stands for."""
    achievementId = arcadeIdForName(name)
    if achievementId:
        unlock(achievementId)


def retired():
    unlock(RETIRED_ARCADE_ID)


def catchUp(stats):
    """Re-assert every achievement a loaded save has already earned.

    For a save that earned milestones before arcade achievements existed, or
    while the player was signed out. Reads stats.earnedMilestones only."""
    for name in list(getattr(stats, "earnedMilestones", []) or []):
        nameEarned(name)
