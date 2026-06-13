from src.achievements import achievements
from src.stats.stats import Stats


def createStats():
    return Stats()


def test_isEarned_threshold():
    # prepare
    stats = createStats()
    milestone = {"name": "X", "stat": "totalFishCaught", "threshold": 5}

    # check - below threshold not earned, at/above earned
    stats.totalFishCaught = 4
    assert achievements.isEarned(milestone, stats) is False
    stats.totalFishCaught = 5
    assert achievements.isEarned(milestone, stats) is True


def test_getMilestoneStatuses_covers_all():
    # prepare
    stats = createStats()

    # call
    statuses = achievements.getMilestoneStatuses(stats)

    # check - one entry per defined milestone, none earned on a fresh game
    assert len(statuses) == len(achievements.MILESTONES)
    assert all(earned is False for _, earned in statuses)


def test_getNewlyEarned_records_and_does_not_repeat():
    # prepare - enough fish to clear the "First Catch" (1) milestone
    stats = createStats()
    stats.totalFishCaught = 1

    # call - first pass returns it and records it
    firstPass = achievements.getNewlyEarned(stats)
    names = [m["name"] for m in firstPass]
    assert "First Catch" in names
    assert "First Catch" in stats.earnedMilestones

    # call again - already recorded, so not returned a second time
    secondPass = achievements.getNewlyEarned(stats)
    assert all(m["name"] != "First Catch" for m in secondPass)


def test_stats_default_earnedMilestones_is_empty():
    # check
    assert createStats().earnedMilestones == []
