from unittest.mock import patch

from src.business import boats
from src.business import business
from src.business import voyages
from src.npc import villagers
from src.player.player import Player
from src.stats.stats import Stats


def createFleetPlayer(role, tier=3, crew=2, money=1000):
    player = Player()
    player.money = money
    boat = boats.addBoat(player, tier, role, "Marauder")
    for villager in villagers.VILLAGERS[:crew]:
        boats.hireWorker(player, villager["name"])
    return player, boat


def test_fishing_boats_have_no_voyages():
    # check - a fishing boat earns every morning instead; there's nothing to
    # send her out on
    assert voyages.jobsFor(boats.ROLE_FISHING) == []


def test_every_other_role_has_a_job_board():
    for role in (boats.ROLE_HAULING, boats.ROLE_PIRACY, boats.ROLE_TRANSPORT):
        assert voyages.jobsFor(role)


def test_job_boards_are_gated_by_boat_size():
    # prepare - the same role on the smallest and largest hull
    _, small = createFleetPlayer(boats.ROLE_PIRACY, tier=1)
    _, big = createFleetPlayer(boats.ROLE_PIRACY, tier=3)

    # check - a Rowboat can only take the easy target; a fleet can take them all
    assert len(voyages.availableJobs(small)) < len(voyages.availableJobs(big))
    assert voyages.availableJobs(big) == voyages.PIRACY_RAIDS


def test_a_boat_needs_a_crew_to_sail():
    # prepare - a boat with nobody aboard
    player = Player()
    boat = boats.addBoat(player, 2, boats.ROLE_PIRACY)

    # call
    ok, reason = voyages.canSail(boat)

    # check
    assert ok is False
    assert reason == "no_crew"
    assert "no crew aboard" in voyages.unsailableReason(boat)


def test_a_wrecked_boat_stays_in_port():
    # prepare
    player, boat = createFleetPlayer(boats.ROLE_PIRACY)
    boats.damageBoat(boat, boats.UNSEAWORTHY_DAMAGE)

    # call
    ok, reason = voyages.canSail(boat)

    # check - and the message says what it costs to put right
    assert ok is False
    assert reason == "too_damaged"
    assert "$%d" % boats.repairCost(boat) in voyages.unsailableReason(boat)


def test_readyBoats_skips_fishing_boats():
    # prepare - a crewed fishing boat and a crewed pirate
    player = Player()
    boats.addBoat(player, 2, boats.ROLE_FISHING)
    pirate = boats.addBoat(player, 2, boats.ROLE_PIRACY)
    boats.hireWorker(player, "Marta Kell")
    boats.hireWorker(player, "Owen Brackish")
    boats.unassignCrew(player, player.boats[0]["id"], "Owen Brackish")
    boats.assignCrew(player, pirate["id"], "Owen Brackish")

    # call
    ready = voyages.readyBoats(player)

    # check
    assert ready == [pirate]


def test_transport_always_pays_and_never_damages_the_boat():
    # prepare
    player, boat = createFleetPlayer(boats.ROLE_TRANSPORT)
    stats = Stats()
    job = voyages.availableJobs(boat)[0]
    startingMoney = player.money

    # call - run it many times; transport is the guaranteed floor
    for _ in range(20):
        summary = voyages.runTransport(player, boat, job, stats)
        assert summary["outcome"] == "paid"
        assert summary["damage"] == 0

    # check
    expected = voyages.honestPay(boat, job) * 20
    assert player.money == startingMoney + expected
    assert stats.totalTransportRuns == 20
    assert stats.totalMoneyFromVoyages == expected


def test_pay_scales_with_the_crew_aboard():
    # prepare - the same job on the same hull, with one hand and with four
    thin, thinBoat = createFleetPlayer(boats.ROLE_TRANSPORT, crew=1)
    full, fullBoat = createFleetPlayer(boats.ROLE_TRANSPORT, crew=4)
    job = voyages.availableJobs(thinBoat)[0]

    # check
    assert voyages.honestPay(fullBoat, job) > voyages.honestPay(thinBoat, job)


def test_hauling_pays_and_can_batter_the_hull():
    # prepare
    player, boat = createFleetPlayer(boats.ROLE_HAULING)
    job = voyages.availableJobs(boat)[0]
    stats = Stats()

    # call - force the rough-seas roll
    with patch("src.business.voyages.random.random", return_value=0.0):
        summary = voyages.runHauling(player, boat, job, stats)

    # check - the cargo still got through, but she took a beating
    assert summary["outcome"] == "rough_seas"
    assert summary["earned"] == voyages.honestPay(boat, job)
    assert summary["damage"] > 0
    assert boat["damage"] == summary["damage"]
    assert stats.totalHaulingContracts == 1


def test_hauling_in_calm_weather_leaves_her_sound():
    # prepare
    player, boat = createFleetPlayer(boats.ROLE_HAULING)
    job = voyages.availableJobs(boat)[0]

    # call - force the calm roll
    with patch("src.business.voyages.random.random", return_value=0.99):
        summary = voyages.runHauling(player, boat, job)

    # check
    assert summary["outcome"] == "delivered"
    assert summary["damage"] == 0
    assert boat["damage"] == 0


def test_raid_odds_improve_with_a_bigger_boat_and_a_fuller_crew():
    # prepare
    _, weak = createFleetPlayer(boats.ROLE_PIRACY, tier=1, crew=1)
    _, strong = createFleetPlayer(boats.ROLE_PIRACY, tier=3, crew=8)
    raid = voyages.PIRACY_RAIDS[0]

    # check
    assert voyages.successOdds(strong, raid) > voyages.successOdds(weak, raid)


def test_raid_odds_are_never_certain_and_never_hopeless():
    # prepare - the strongest possible attacker on the easiest target, and the
    # weakest on the hardest
    _, strong = createFleetPlayer(boats.ROLE_PIRACY, tier=3, crew=8)
    _, weak = createFleetPlayer(boats.ROLE_PIRACY, tier=1, crew=1)

    # check - piracy stays a gamble at both ends
    assert (
        voyages.successOdds(strong, voyages.PIRACY_RAIDS[0]) <= voyages.MAX_SUCCESS_ODDS
    )
    assert (
        voyages.successOdds(weak, voyages.PIRACY_RAIDS[-1]) >= voyages.MIN_SUCCESS_ODDS
    )


def test_raid_outlook_covers_every_outcome():
    # prepare
    _, boat = createFleetPlayer(boats.ROLE_PIRACY)
    outlook = voyages.raidOutlook(boat, voyages.PIRACY_RAIDS[0])

    # check - the four chances shown to the player account for everything
    assert set(outlook) == {"rich", "success", "drivenOff", "disaster"}
    assert abs(sum(outlook.values()) - 1.0) < 1e-9
    assert all(chance >= 0 for chance in outlook.values())


def test_a_successful_raid_takes_money_and_cargo():
    # prepare
    player, boat = createFleetPlayer(boats.ROLE_PIRACY)
    raid = voyages.PIRACY_RAIDS[0]
    stats = Stats()
    startingMoney = player.money

    # call - force the outcome roll into the "success" band
    with patch(
        "src.business.voyages.random.random",
        return_value=0.99 * voyages.raidOutlook(boat, raid)["rich"] + 0.001,
    ):
        summary = voyages.runRaid(player, boat, raid, stats)

    # check
    assert summary["outcome"] in ("rich", "success")
    assert summary["earned"] > 0
    assert player.money == startingMoney + summary["earned"]
    assert stats.totalPlunder == summary["earned"]
    assert stats.totalRaids == 1


def test_a_rich_raid_pays_more_than_an_ordinary_one():
    # prepare - the same raid, the same loot roll, different outcome bands
    player, boat = createFleetPlayer(boats.ROLE_PIRACY)
    raid = voyages.PIRACY_RAIDS[0]

    with patch("src.business.voyages.random.randint", return_value=raid["loot"][0]):
        with patch("src.business.voyages.random.random", return_value=0.0):
            rich = voyages.runRaid(player, boat, raid)
        outlook = voyages.raidOutlook(boat, raid)
        with patch(
            "src.business.voyages.random.random", return_value=outlook["rich"] + 0.001
        ):
            ordinary = voyages.runRaid(player, boat, raid)

    # check
    assert rich["outcome"] == "rich"
    assert ordinary["outcome"] == "success"
    assert rich["earned"] > ordinary["earned"]


def test_being_driven_off_costs_damage_but_no_crew():
    # prepare
    player, boat = createFleetPlayer(boats.ROLE_PIRACY)
    raid = voyages.PIRACY_RAIDS[0]
    outlook = voyages.raidOutlook(boat, raid)
    crewBefore = list(boat["crew"])

    # call - land the roll in the driven-off band
    roll = outlook["rich"] + outlook["success"] + 0.001
    with patch("src.business.voyages.random.random", return_value=roll):
        summary = voyages.runRaid(player, boat, raid)

    # check
    assert summary["outcome"] == "driven_off"
    assert summary["earned"] == 0
    assert summary["damage"] > 0
    assert summary["crewLost"] is None
    assert boat["crew"] == crewBefore


def test_a_disaster_costs_a_named_villager_for_good():
    # prepare
    player, boat = createFleetPlayer(boats.ROLE_PIRACY)
    raid = voyages.PIRACY_RAIDS[0]
    stats = Stats()
    crewBefore = list(boat["crew"])

    # call - land the roll in the disaster band
    with patch("src.business.voyages.random.random", return_value=1.0):
        summary = voyages.runRaid(player, boat, raid, stats)

    # check - someone the player hired by name is gone from the boat AND the
    # roster; this is the cost that makes a raid a real decision
    assert summary["outcome"] == "disaster"
    assert summary["crewLost"] in crewBefore
    assert summary["crewLost"] not in boat["crew"]
    assert summary["crewLost"] not in player.hiredWorkers
    assert player.workers == len(crewBefore) - 1
    assert summary["damage"] >= voyages.DISASTER_DAMAGE[0]
    assert stats.crewLostToPiracy == 1


def test_a_disaster_with_only_unnamed_hands_still_costs_one():
    # prepare - a legacy crew with no names attached
    player = Player()
    boat = boats.addBoat(player, 2, boats.ROLE_PIRACY)
    player.workers = 2
    boat["hands"] = 2

    # call
    with patch("src.business.voyages.random.random", return_value=1.0):
        summary = voyages.runRaid(player, boat, voyages.PIRACY_RAIDS[0])

    # check
    assert summary["outcome"] == "disaster"
    assert summary["crewLost"] is None
    assert boat["hands"] == 1
    assert player.workers == 1


def test_a_disaster_can_leave_her_unable_to_sail():
    # prepare - a boat already knocked about
    player, boat = createFleetPlayer(boats.ROLE_PIRACY)
    boats.damageBoat(boat, 20)

    # call
    with patch("src.business.voyages.random.random", return_value=1.0):
        voyages.runRaid(player, boat, voyages.PIRACY_RAIDS[0])

    # check - piracy's cost outlasts the raid itself
    assert boat["damage"] >= boats.UNSEAWORTHY_DAMAGE
    assert boats.isSeaworthy(boat) is False
    assert voyages.canSail(boat)[0] is False


def test_runVoyage_dispatches_on_the_boat_role():
    # prepare
    for role in (boats.ROLE_TRANSPORT, boats.ROLE_HAULING, boats.ROLE_PIRACY):
        player, boat = createFleetPlayer(role)
        job = voyages.availableJobs(boat)[0]

        # call
        summary = voyages.runVoyage(player, boat, job, Stats())

        # check
        assert summary["role"] == role
        assert summary["boat"] == "Marauder"


def test_runVoyage_has_nothing_for_a_fishing_boat():
    # prepare
    player, boat = createFleetPlayer(boats.ROLE_FISHING)

    # check
    assert voyages.runVoyage(player, boat, {}, None) is None


def test_describeJob_shows_the_odds_for_a_raid():
    # prepare
    _, boat = createFleetPlayer(boats.ROLE_PIRACY)
    raid = voyages.PIRACY_RAIDS[0]

    # call
    line = voyages.describeJob(boat, raid)

    # check - the player sees what they're gambling on before they commit
    assert raid["name"] in line
    assert "% to take the prize" in line
    assert "risk of disaster" in line


def test_describeJob_shows_pay_for_honest_work():
    # prepare
    _, hauler = createFleetPlayer(boats.ROLE_HAULING)
    _, ferry = createFleetPlayer(boats.ROLE_TRANSPORT)

    # check
    haulLine = voyages.describeJob(hauler, voyages.availableJobs(hauler)[0])
    ferryLine = voyages.describeJob(ferry, voyages.availableJobs(ferry)[0])
    assert "rough seas" in haulLine
    assert "no risk" in ferryLine


def test_raids_pay_more_than_honest_work_at_the_same_tier():
    # prepare - the same hull and crew, one hauling and one raiding
    _, hauler = createFleetPlayer(boats.ROLE_HAULING, tier=3)
    _, pirate = createFleetPlayer(boats.ROLE_PIRACY, tier=3)
    contract = voyages.availableJobs(hauler)[-1]
    raid = voyages.availableJobs(pirate)[-1]

    # check - piracy has to out-earn the safe option, or the risk is pointless
    assert raid["loot"][0] > voyages.honestPay(hauler, contract)


def test_job_boards_scale_up_with_the_boat():
    # check - each rung of every board pays more and needs a bigger hull
    for board in (voyages.TRANSPORT_RUNS, voyages.HAULING_CONTRACTS):
        for smaller, bigger in zip(board, board[1:]):
            assert bigger["minTier"] > smaller["minTier"]
            assert bigger["basePay"] > smaller["basePay"]
            assert bigger["perCrew"] > smaller["perCrew"]
    for smaller, bigger in zip(voyages.PIRACY_RAIDS, voyages.PIRACY_RAIDS[1:]):
        assert bigger["minTier"] > smaller["minTier"]
        assert bigger["difficulty"] > smaller["difficulty"]
        assert bigger["loot"][0] > smaller["loot"][0]


def test_every_job_is_reachable_by_some_boat():
    for role in (boats.ROLE_HAULING, boats.ROLE_PIRACY, boats.ROLE_TRANSPORT):
        for job in voyages.jobsFor(role):
            assert 1 <= job["minTier"] <= len(business.BOAT_TIERS)


def test_unsailableReason_explains_a_fishing_boat():
    # prepare - a crewed fishing boat, which has no job board at all
    player = Player()
    boat = boats.addBoat(player, 2, boats.ROLE_FISHING)
    boats.hireWorker(player, "Marta Kell")

    # call
    ok, reason = voyages.canSail(boat)

    # check - not an error, just the wrong question to ask of her
    assert ok is False
    assert reason == "no_jobs"
    assert "earns her keep every morning" in voyages.unsailableReason(boat)


def test_unsailableReason_explains_a_boat_too_small_for_its_role():
    # prepare - a Rowboat dedicated to work that needs a bigger hull
    player = Player()
    boat = boats.addBoat(player, 1, boats.ROLE_PIRACY)
    boats.hireWorker(player, "Marta Kell")
    # the easiest raid is tier 1, so shift her to a role whose board starts higher
    boat["role"] = boats.ROLE_HAULING
    voyages.HAULING_CONTRACTS[0]["minTier"] = 2
    try:
        # call
        ok, reason = voyages.canSail(boat)

        # check
        assert ok is False
        assert reason == "no_jobs"
        assert "too small" in voyages.unsailableReason(boat)
    finally:
        voyages.HAULING_CONTRACTS[0]["minTier"] = 1


def test_unsailableReason_is_none_for_a_boat_ready_to_go():
    # prepare
    player, boat = createFleetPlayer(boats.ROLE_PIRACY)

    # check
    assert voyages.canSail(boat)[0] is True
    assert voyages.unsailableReason(boat) is None
