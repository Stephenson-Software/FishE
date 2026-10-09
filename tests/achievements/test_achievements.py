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


def test_every_milestone_stat_is_a_real_stats_attribute():
    # prepare - isEarned falls back to 0 for a missing attribute, so a typo in
    # a milestone's "stat" would make it silently unearnable
    stats = createStats()

    # check
    for milestone in achievements.MILESTONES:
        assert hasattr(stats, milestone["stat"]), milestone["name"]


def test_milestone_names_are_unique_and_distinct_from_the_goal():
    # prepare
    names = [m["name"] for m in achievements.MILESTONES]

    # check - names are what stats.earnedMilestones records, so they must not collide
    assert len(set(names)) == len(names)
    assert achievements.GOAL_MILESTONE_NAME not in names


def test_every_milestone_has_a_positive_threshold_and_a_description():
    # check - a threshold of 0 would be earned by every brand new game
    for milestone in achievements.MILESTONES:
        assert milestone["threshold"] > 0, milestone["name"]
        assert milestone["description"], milestone["name"]


def test_isEarned_missing_stat_is_not_earned():
    # prepare
    stats = createStats()
    milestone = {"name": "X", "stat": "noSuchStat", "threshold": 1}

    # call
    earned = achievements.isEarned(milestone, stats)

    # check
    assert earned is False


def test_getMilestoneStatuses_preserves_order_and_flags_earned():
    # prepare - clears "First Catch" (1) but not "Seasoned Angler" (100)
    stats = createStats()
    stats.totalFishCaught = 1

    # call
    statuses = achievements.getMilestoneStatuses(stats)

    # check
    assert [m for m, _ in statuses] == achievements.MILESTONES
    earned = {m["name"]: e for m, e in statuses}
    assert earned["First Catch"] is True
    assert earned["Seasoned Angler"] is False


def test_getMilestoneStatuses_does_not_record_anything():
    # prepare
    stats = createStats()
    stats.totalFishCaught = 1

    # call
    achievements.getMilestoneStatuses(stats)

    # check - only getNewlyEarned records announcements
    assert stats.earnedMilestones == []


def test_getNewlyEarned_returns_several_at_once_in_milestone_order():
    # prepare - clears First Catch, Seasoned Angler and Pocket Money together
    stats = createStats()
    stats.totalFishCaught = 100
    stats.totalMoneyMade = 100

    # call
    newly = achievements.getNewlyEarned(stats)

    # check
    assert [m["name"] for m in newly] == [
        "First Catch",
        "Seasoned Angler",
        "Pocket Money",
    ]
    assert stats.earnedMilestones == [
        "First Catch",
        "Seasoned Angler",
        "Pocket Money",
    ]


def test_getNewlyEarned_skips_milestones_already_recorded_by_a_loaded_save():
    # prepare - a save that already announced First Catch
    stats = createStats()
    stats.totalFishCaught = 100
    stats.earnedMilestones = ["First Catch"]

    # call
    newly = achievements.getNewlyEarned(stats)

    # check
    assert [m["name"] for m in newly] == ["Seasoned Angler"]
    assert stats.earnedMilestones == ["First Catch", "Seasoned Angler"]


def test_getNewlyEarned_on_a_fresh_game_returns_nothing():
    # prepare
    stats = createStats()

    # call
    newly = achievements.getNewlyEarned(stats)

    # check
    assert newly == []
    assert stats.earnedMilestones == []


def test_arcadeIdForName_maps_the_goal():
    # call
    arcadeId = achievements.arcadeIdForName(achievements.GOAL_MILESTONE_NAME)

    # check
    assert arcadeId == achievements.GOAL_ARCADE_ID


def test_arcadeIdForName_maps_a_milestone_with_an_arcade_id():
    # call
    arcadeId = achievements.arcadeIdForName("First Catch")

    # check
    assert arcadeId == "first-catch"


def test_arcadeIdForName_is_none_for_a_milestone_without_an_arcade_id():
    # call
    arcadeId = achievements.arcadeIdForName("Seasoned Angler")

    # check
    assert arcadeId is None


def test_arcadeIdForName_is_none_for_an_unknown_name():
    # call
    arcadeId = achievements.arcadeIdForName("No Such Milestone")

    # check
    assert arcadeId is None


def test_arcadeDeclarations_lists_milestones_then_goal_then_retired():
    # prepare
    expectedMilestoneIds = [
        m["arcadeId"] for m in achievements.MILESTONES if "arcadeId" in m
    ]

    # call
    declared = achievements.arcadeDeclarations()

    # check
    assert [d["id"] for d in declared] == expectedMilestoneIds + [
        achievements.GOAL_ARCADE_ID,
        achievements.RETIRED_ARCADE_ID,
    ]
    assert declared[-2] == {
        "id": achievements.GOAL_ARCADE_ID,
        "title": achievements.GOAL_MILESTONE_NAME,
        "description": achievements.GOAL_DESCRIPTION,
        "hidden": False,
    }
    assert declared[-1] == {
        "id": achievements.RETIRED_ARCADE_ID,
        "title": achievements.RETIRED_TITLE,
        "description": achievements.RETIRED_DESCRIPTION,
        "hidden": False,
    }


def test_arcadeDeclarations_take_title_and_description_from_the_milestone():
    # prepare
    byId = {d["id"]: d for d in achievements.arcadeDeclarations()}

    # check
    for milestone in achievements.MILESTONES:
        if "arcadeId" not in milestone:
            continue
        declared = byId[milestone["arcadeId"]]
        assert declared["title"] == milestone["name"]
        assert declared["description"] == milestone["description"]
        assert declared["hidden"] is bool(milestone.get("arcadeHidden", False))
