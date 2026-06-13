# @author Daniel McCoy Stephenson
#
# Milestones are short-term goals derived entirely from the player's lifetime
# Stats. They are data-driven: add a row to MILESTONES and it is automatically
# tracked, displayed, and announced. A milestone is "earned" once its stat
# reaches its threshold; the set of already-announced milestone names lives on
# Stats (stats.earnedMilestones) so each is announced only once across saves.

MILESTONES = [
    {
        "name": "First Catch",
        "stat": "totalFishCaught",
        "threshold": 1,
        "description": "Catch your first fish",
    },
    {
        "name": "Seasoned Angler",
        "stat": "totalFishCaught",
        "threshold": 100,
        "description": "Catch 100 fish",
    },
    {
        "name": "Master Fisher",
        "stat": "totalFishCaught",
        "threshold": 1000,
        "description": "Catch 1,000 fish",
    },
    {
        "name": "Pocket Money",
        "stat": "totalMoneyMade",
        "threshold": 100,
        "description": "Earn $100 total",
    },
    {
        "name": "Big Earner",
        "stat": "totalMoneyMade",
        "threshold": 1000,
        "description": "Earn $1,000 total",
    },
    {
        "name": "Old Salt",
        "stat": "hoursSpentFishing",
        "threshold": 50,
        "description": "Spend 50 hours fishing",
    },
]


def isEarned(milestone, stats):
    """True if the milestone's stat has reached its threshold."""
    return getattr(stats, milestone["stat"], 0) >= milestone["threshold"]


def getMilestoneStatuses(stats):
    """Return a list of (milestone, earned) for every milestone, in order."""
    return [(milestone, isEarned(milestone, stats)) for milestone in MILESTONES]


def getNewlyEarned(stats):
    """Return milestones newly earned since the last call and record them.

    Records each newly-earned milestone's name on stats.earnedMilestones so it
    is not announced again (including across reloads, since that list is saved).
    """
    newly = []
    for milestone in MILESTONES:
        if isEarned(milestone, stats) and milestone["name"] not in stats.earnedMilestones:
            stats.earnedMilestones.append(milestone["name"])
            newly.append(milestone)
    return newly
