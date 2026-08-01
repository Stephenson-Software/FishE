from unittest.mock import patch

from src.business import boats
from src.business import business
from src.npc import villagers
from src.player.player import Player
from src.stats.stats import Stats


def test_no_production_without_a_boat():
    # prepare - workers but no boat
    player = Player()
    boats.hireWorker(player)
    boats.hireWorker(player)
    boats.hireWorker(player)
    player.money = 1000

    # call
    summary = boats.runDailyProduction(player)

    # check - nothing happens until there's a boat
    assert summary["fishCaught"] == 0
    assert summary["wagesPaid"] == 0
    assert player.money == 1000
    assert player.fishCount == 0


def test_workers_catch_fish_and_draw_wages():
    # prepare - a boat and two workers, plenty of money
    player = Player()
    boats.addBoat(player, 1)
    boats.hireWorker(player)
    boats.hireWorker(player)
    player.money = 1000
    stats = Stats()

    # call
    summary = boats.runDailyProduction(player, stats)

    # check
    expectedFish = 2 * business.WORKER_FISH_PER_DAY
    expectedWages = 2 * business.WORKER_DAILY_WAGE
    assert summary["fishCaught"] == expectedFish
    assert summary["wagesPaid"] == expectedWages
    assert player.fishCount == expectedFish
    assert player.money == 1000 - expectedWages
    assert stats.totalFishCaught == expectedFish


def test_workers_catch_rolled_species_not_just_minnow():
    # prepare - a boat and one worker; force the rolled species to Bass
    player = Player()
    boats.addBoat(player, 1)
    boats.hireWorker(player)
    player.money = 1000

    # call - workers fish a rarity-rolled species, not a hard-coded one
    with patch.object(boats.fish, "rollFishType", return_value="Bass"):
        boats.runDailyProduction(player)

    # check - the catch landed as the rolled species
    assert player.fishByType.get("Bass") == business.WORKER_FISH_PER_DAY
    assert "Minnow" not in player.fishByType


def test_unaffordable_workers_quit():
    # prepare - 3 workers but only enough money for one day's wage of one worker
    player = Player()
    boats.addBoat(player, 1)
    boats.hireWorker(player)
    boats.hireWorker(player)
    boats.hireWorker(player)
    player.money = business.WORKER_DAILY_WAGE  # covers exactly one worker

    # call
    summary = boats.runDailyProduction(player)

    # check - the two unpayable workers quit; the remaining one is paid and fishes
    assert summary["quit"] == 2
    assert player.workers == 1
    assert summary["wagesPaid"] == business.WORKER_DAILY_WAGE
    assert summary["fishCaught"] == business.WORKER_FISH_PER_DAY
    assert player.money == 0


def test_all_workers_quit_when_broke():
    # prepare - a boat and workers but no money
    player = Player()
    boats.addBoat(player, 1)
    boats.hireWorker(player)
    boats.hireWorker(player)
    player.money = 0

    # call
    summary = boats.runDailyProduction(player)

    # check - everyone quits, nothing caught
    assert player.workers == 0
    assert summary["quit"] == 2
    assert summary["fishCaught"] == 0
    assert player.fishCount == 0


def test_higher_tier_boat_yields_more_fish_per_worker():
    # prepare - an upgraded boat (tier 2) with one worker
    player = Player()
    boats.addBoat(player, 2)
    boats.hireWorker(player)
    player.money = 1000
    stats = Stats()

    # call
    summary = boats.runDailyProduction(player, stats)

    # check - tier 2's fishPerDay beats the flat tier-1 constant
    tier2FishPerDay = business.tierInfo(2)["fishPerDay"]
    assert tier2FishPerDay > business.WORKER_FISH_PER_DAY
    assert summary["fishCaught"] == tier2FishPerDay
    assert stats.totalFishCaughtByCrew == tier2FishPerDay


def test_runDailyProduction_tracks_lifetime_business_stats():
    # prepare
    player = Player()
    boats.addBoat(player, 1)
    boats.hireWorker(player)
    boats.hireWorker(player)
    player.money = 1000
    stats = Stats()

    # call
    summary = boats.runDailyProduction(player, stats)

    # check - lifetime counters advance alongside the day's summary
    assert stats.totalFishCaughtByCrew == summary["fishCaught"]
    assert stats.totalWagesPaid == summary["wagesPaid"]
    assert stats.daysInBusiness == 1

    # a second day accumulates rather than resets
    boats.runDailyProduction(player, stats)
    assert stats.daysInBusiness == 2


def test_sellBoat_refunds_resale_value_and_removes_her_from_the_fleet():
    # prepare - a Trawler (tier 2) with two hands aboard
    player = Player()
    player.money = 0
    boat = boats.addBoat(player, 2)
    boats.hireWorker(player, "Marta Kell")
    boats.hireWorker(player, "Owen Brackish")
    resaleValue = business.tierInfo(2)["resaleValue"]

    # call
    value = boats.sellBoat(player, boat["id"])

    # check - refunded, and she's out of the fleet
    assert value == resaleValue
    assert player.money == resaleValue
    assert player.boats == []
    assert player.hasBoat is False
    assert player.boatTier == 0


def test_sellBoat_leaves_her_crew_on_the_payroll():
    # prepare
    player = Player()
    boat = boats.addBoat(player, 1)
    boats.hireWorker(player, "Marta Kell")

    # call
    boats.sellBoat(player, boat["id"])

    # check - the crew aren't fired along with the boat, they're just ashore
    # and still drawing wages until the player does something about it
    assert player.hiredWorkers == ["Marta Kell"]
    assert player.workers == 1
    assert boats.unassignedNames(player) == ["Marta Kell"]


def test_sellBoat_leaves_the_rest_of_the_fleet_alone():
    # prepare - two boats, one crewed
    player = Player()
    keeper = boats.addBoat(player, 2, boats.ROLE_PIRACY, "Marauder")
    spare = boats.addBoat(player, 1)
    boats.hireWorker(player, "Marta Kell")  # goes to the first boat with room

    # call
    boats.sellBoat(player, spare["id"])

    # check
    assert [boat["id"] for boat in player.boats] == [keeper["id"]]
    assert keeper["crew"] == ["Marta Kell"]


def test_sellBoat_with_an_unknown_id_changes_nothing():
    # prepare
    player = Player()
    boats.addBoat(player, 1)
    player.money = 0

    # call
    value = boats.sellBoat(player, 999)

    # check
    assert value is None
    assert player.money == 0
    assert len(player.boats) == 1


def test_hireWorker_records_the_villager_by_name():
    # prepare
    player = Player()
    boats.addBoat(player, 1)

    # call
    hired = boats.hireWorker(player, "Marta Kell")

    # check
    assert hired is True
    assert player.workers == 1
    assert player.hiredWorkers == ["Marta Kell"]


def test_hireWorker_without_a_name_adds_an_unnamed_hand():
    # prepare
    player = Player()
    boats.addBoat(player, 1)

    # call
    hired = boats.hireWorker(player)

    # check - the headcount grows without a roster entry
    assert hired is True
    assert player.workers == 1
    assert player.hiredWorkers == []


def test_hireWorker_requires_a_boat():
    # prepare
    player = Player()

    # call
    hired = boats.hireWorker(player, "Marta Kell")

    # check
    assert hired is False
    assert player.workers == 0
    assert player.hiredWorkers == []


def test_hireWorker_refuses_a_full_crew():
    # prepare - every berth on the Rowboat taken
    player = Player()
    boats.addBoat(player, 1)
    player.workers = business.tierInfo(1)["maxWorkers"]

    # call
    hired = boats.hireWorker(player, "Marta Kell")

    # check
    assert hired is False
    assert player.workers == business.tierInfo(1)["maxWorkers"]


def test_hireWorker_refuses_someone_already_aboard():
    # prepare
    player = Player()
    boats.addBoat(player, 1)
    boats.hireWorker(player, "Marta Kell")

    # call
    hired = boats.hireWorker(player, "Marta Kell")

    # check - nobody works two berths
    assert hired is False
    assert player.workers == 1
    assert player.hiredWorkers == ["Marta Kell"]


def test_dismissWorker_by_name():
    # prepare
    player = Player()
    boats.addBoat(player, 1)
    boats.hireWorker(player, "Marta Kell")
    boats.hireWorker(player, "Owen Brackish")

    # call
    dismissed = boats.dismissWorker(player, "Marta Kell")

    # check
    assert dismissed is True
    assert player.workers == 1
    assert player.hiredWorkers == ["Owen Brackish"]


def test_dismissWorker_without_a_name_drops_an_unnamed_hand_first():
    # prepare - a named villager alongside an unnamed hand from an older save
    player = Player()
    boats.addBoat(player, 1)
    boats.hireWorker(player)
    boats.hireWorker(player, "Marta Kell")

    # call
    dismissed = boats.dismissWorker(player)

    # check - the villager the player knows by name stays
    assert dismissed is True
    assert player.workers == 1
    assert player.hiredWorkers == ["Marta Kell"]


def test_dismissWorker_without_a_name_falls_back_to_a_named_hand():
    # prepare - the whole crew is named, so there's no unnamed hand to drop
    player = Player()
    boats.addBoat(player, 1)
    boats.hireWorker(player, "Marta Kell")

    # call
    dismissed = boats.dismissWorker(player)

    # check - the roster never outlasts the headcount
    assert dismissed is True
    assert player.workers == 0
    assert player.hiredWorkers == []


def test_dismissWorker_with_an_unknown_name_changes_nothing():
    # prepare
    player = Player()
    boats.addBoat(player, 1)
    boats.hireWorker(player, "Marta Kell")

    # call
    dismissed = boats.dismissWorker(player, "Nobody At All")

    # check
    assert dismissed is False
    assert player.workers == 1
    assert player.hiredWorkers == ["Marta Kell"]


def test_dismissWorker_with_no_crew():
    # prepare
    player = Player()
    boats.addBoat(player, 1)

    # call
    dismissed = boats.dismissWorker(player)

    # check
    assert dismissed is False
    assert player.workers == 0


def test_unpaid_workers_quit_by_name():
    # prepare - three named hands but only enough money for one day's wage
    player = Player()
    boats.addBoat(player, 1)
    player.money = business.WORKER_DAILY_WAGE
    boats.hireWorker(player, "Marta Kell")
    boats.hireWorker(player, "Owen Brackish")
    boats.hireWorker(player, "Piety Shaw")

    # call
    summary = boats.runDailyProduction(player)

    # check - the most recent hires walk, and the summary names them
    assert summary["quit"] == 2
    assert summary["quitNames"] == ["Piety Shaw", "Owen Brackish"]
    assert player.workers == 1
    assert player.hiredWorkers == ["Marta Kell"]


def test_paid_workers_stay_on_the_roster():
    # prepare
    player = Player()
    boats.addBoat(player, 1)
    player.money = 1000
    boats.hireWorker(player, "Marta Kell")

    # call
    summary = boats.runDailyProduction(player)

    # check
    assert summary["quit"] == 0
    assert summary["quitNames"] == []
    assert player.hiredWorkers == ["Marta Kell"]


def crewedFleet(roles=(boats.ROLE_FISHING,), tier=1, crewEach=1):
    """A player with one boat per role, each crewed from the shared roster."""
    player = Player()
    player.money = 10000
    for index, role in enumerate(roles):
        boats.addBoat(player, tier, role, "Boat %d" % (index + 1))
    # Hire, then place deliberately: hireWorker fills the first boat with a
    # free berth, so relying on it would put the whole roster on boat one.
    roster = iter(villagers.VILLAGERS)
    for boat in player.boats:
        for _ in range(crewEach):
            name = next(roster)["name"]
            boats.hireWorker(player, name)
            for other in player.boats:
                if name in other["crew"]:
                    other["crew"].remove(name)
            boats.assignCrew(player, boat["id"], name)
    return player


def test_hireWorker_puts_the_new_hand_straight_aboard():
    # prepare
    player = Player()
    boat = boats.addBoat(player, 1)

    # call
    boats.hireWorker(player, "Marta Kell")

    # check - hired and working, not left on the dock drawing wages
    assert player.hiredWorkers == ["Marta Kell"]
    assert boat["crew"] == ["Marta Kell"]
    assert boats.unassignedNames(player) == []


def test_hireWorker_fills_the_next_boat_once_the_first_is_full():
    # prepare - two Rowboats
    player = Player()
    first = boats.addBoat(player, 1)
    second = boats.addBoat(player, 1)
    berths = business.tierInfo(1)["maxWorkers"]

    # call - hire one more than the first boat holds
    for villager in villagers.VILLAGERS[: berths + 1]:
        boats.hireWorker(player, villager["name"])

    # check
    assert len(first["crew"]) == berths
    assert len(second["crew"]) == 1


def test_hire_capacity_is_the_whole_fleet_not_one_boat():
    # prepare
    player = Player()
    boats.addBoat(player, 1)
    boats.addBoat(player, 1)
    berths = business.tierInfo(1)["maxWorkers"] * 2

    # call
    hired = 0
    for villager in villagers.VILLAGERS:
        if boats.hireWorker(player, villager["name"]):
            hired += 1

    # check
    assert hired == min(berths, len(villagers.VILLAGERS))
    assert boats.totalCrewBerths(player) == berths


def test_only_fishing_boats_bring_in_a_catch():
    # prepare - one boat of every role, each with a hand aboard
    player = crewedFleet(roles=boats.ROLE_ORDER)

    # call
    summary = boats.runDailyProduction(player)

    # check - four hands are paid, but only the one on the fishing boat fishes
    assert summary["workers"] == 4
    assert summary["wagesPaid"] == 4 * business.WORKER_DAILY_WAGE
    assert summary["fishCaught"] == business.tierInfo(1)["fishPerDay"]


def test_wages_are_owed_on_idle_crew_too():
    # prepare - a hand hired, then taken off the boat
    player = crewedFleet()
    boats.unassignCrew(player, player.boats[0]["id"], player.boats[0]["crew"][0])
    startingMoney = player.money

    # check - they cost the same ashore as aboard; that's the pressure to use
    # them or let them go
    summary = boats.runDailyProduction(player)
    assert summary["wagesPaid"] == business.WORKER_DAILY_WAGE
    assert summary["fishCaught"] == 0
    assert player.money == startingMoney - business.WORKER_DAILY_WAGE


def test_two_fishing_boats_both_produce():
    # prepare - two fishing boats, one hand each
    player = crewedFleet(roles=(boats.ROLE_FISHING, boats.ROLE_FISHING))

    # call
    summary = boats.runDailyProduction(player)

    # check
    assert summary["fishCaught"] == 2 * business.tierInfo(1)["fishPerDay"]


def test_a_bigger_boat_makes_its_own_crew_worth_more():
    # prepare - the same single hand on a Rowboat and on a Fishing Fleet
    small = crewedFleet(tier=1)
    big = crewedFleet(tier=3)

    # check
    assert (
        boats.runDailyProduction(small)["fishCaught"]
        == business.tierInfo(1)["fishPerDay"]
    )
    assert (
        boats.runDailyProduction(big)["fishCaught"]
        == business.tierInfo(3)["fishPerDay"]
    )


def test_idle_crew_quit_before_working_crew():
    # prepare - two hands, one aboard and one ashore, and money for only one
    player = crewedFleet()
    boats.hireWorker(player, "Owen Brackish")
    boats.unassignCrew(player, player.boats[0]["id"], "Owen Brackish")
    player.money = business.WORKER_DAILY_WAGE

    # call
    summary = boats.runDailyProduction(player)

    # check - the one doing nothing is the one who walks
    assert summary["quitNames"] == ["Owen Brackish"]
    assert player.hiredWorkers == ["Marta Kell"]
    assert player.boats[0]["crew"] == ["Marta Kell"]


def test_assign_and_unassign_crew_between_boats():
    # prepare
    player = crewedFleet(roles=(boats.ROLE_FISHING, boats.ROLE_PIRACY))
    fisher, pirate = player.boats
    name = fisher["crew"][0]

    # call
    assert boats.unassignCrew(player, fisher["id"], name) is True
    assert boats.assignCrew(player, pirate["id"], name) is True

    # check
    assert name not in fisher["crew"]
    assert name in pirate["crew"]
    assert boats.unassignedNames(player) == []


def test_assignCrew_refuses_a_full_boat():
    # prepare - a Rowboat filled to its berths, plus one villager ashore
    player = Player()
    boat = boats.addBoat(player, 1)
    boats.addBoat(player, 1)  # somewhere for the extra hire to land
    berths = business.tierInfo(1)["maxWorkers"]
    for villager in villagers.VILLAGERS[: berths + 1]:
        boats.hireWorker(player, villager["name"])
    spare = player.boats[1]["crew"][0]
    boats.unassignCrew(player, player.boats[1]["id"], spare)

    # call
    assigned = boats.assignCrew(player, boat["id"], spare)

    # check
    assert assigned is False
    assert len(boat["crew"]) == berths


def test_assignCrew_refuses_someone_already_on_another_boat():
    # prepare
    player = crewedFleet(roles=(boats.ROLE_FISHING, boats.ROLE_PIRACY))
    name = player.boats[0]["crew"][0]

    # call
    assigned = boats.assignCrew(player, player.boats[1]["id"], name)

    # check - nobody works two berths at once
    assert assigned is False
    assert player.boats[0]["crew"] == [name]
    assert name not in player.boats[1]["crew"]


def test_assignCrew_refuses_someone_who_was_never_hired():
    # prepare
    player = Player()
    boat = boats.addBoat(player, 1)

    # call
    assigned = boats.assignCrew(player, boat["id"], "Nobody At All")

    # check
    assert assigned is False
    assert boat["crew"] == []


def test_setRole_redirects_a_boat():
    # prepare
    player = Player()
    boat = boats.addBoat(player, 1)

    # call
    assert boats.setRole(player, boat["id"], boats.ROLE_PIRACY) is True

    # check
    assert boat["role"] == boats.ROLE_PIRACY
    assert boats.boatsWithRole(player, boats.ROLE_PIRACY) == [boat]
    assert boats.boatsWithRole(player, boats.ROLE_FISHING) == []


def test_setRole_rejects_an_unknown_role():
    # prepare
    player = Player()
    boat = boats.addBoat(player, 1)

    # call
    assert boats.setRole(player, boat["id"], "smuggling") is False

    # check
    assert boat["role"] == boats.ROLE_FISHING


def test_damage_stops_a_boat_sailing_until_it_is_repaired():
    # prepare
    player = Player()
    boat = boats.addBoat(player, 1)
    player.money = 10000

    # call/check - a light knock still leaves her seaworthy
    boats.damageBoat(boat, boats.UNSEAWORTHY_DAMAGE - 1)
    assert boats.isSeaworthy(boat) is True

    # call/check - past the threshold she stays in port
    boats.damageBoat(boat, 1)
    assert boats.isSeaworthy(boat) is False

    # call/check - and repair puts her right, for money
    cost = boats.repairCost(boat)
    paid = boats.repairBoat(player, boat["id"])
    assert paid == cost
    assert boat["damage"] == 0
    assert boats.isSeaworthy(boat) is True


def test_damage_is_capped_at_a_total_wreck():
    # prepare
    player = Player()
    boat = boats.addBoat(player, 1)

    # call
    boats.damageBoat(boat, 500)

    # check
    assert boat["damage"] == boats.MAX_DAMAGE


def test_repair_refused_when_it_cannot_be_paid_for():
    # prepare
    player = Player()
    boat = boats.addBoat(player, 1)
    boats.damageBoat(boat, 40)
    player.money = 0

    # call
    paid = boats.repairBoat(player, boat["id"])

    # check - nothing spent, nothing fixed
    assert paid is None
    assert boat["damage"] == 40


def test_repair_of_a_sound_boat_costs_nothing_and_does_nothing():
    # prepare
    player = Player()
    boat = boats.addBoat(player, 1)
    player.money = 100

    # call
    assert boats.repairBoat(player, boat["id"]) is None

    # check
    assert player.money == 100


def test_releaseCrewMember_takes_them_off_the_boat_and_the_roster():
    # prepare
    player = crewedFleet()
    name = player.boats[0]["crew"][0]

    # call
    boats.releaseCrewMember(player, name)

    # check
    assert name not in player.hiredWorkers
    assert name not in player.boats[0]["crew"]
    assert player.workers == 0


def test_boat_ids_are_unique_within_the_fleet():
    # prepare - a fleet with a gap in the middle of it
    player = Player()
    first = boats.addBoat(player, 1)
    middle = boats.addBoat(player, 1)
    last = boats.addBoat(player, 1)
    boats.sellBoat(player, middle["id"])

    # call
    added = boats.addBoat(player, 1)

    # check - ids identify a boat unambiguously among the boats actually owned,
    # which is what every menu and lookup needs
    ids = [boat["id"] for boat in player.boats]
    assert len(ids) == len(set(ids))
    assert added["id"] not in (first["id"], last["id"])


def test_describeBoat_flags_a_boat_that_cannot_sail():
    # prepare
    player = Player()
    boat = boats.addBoat(player, 1, boats.ROLE_PIRACY, "Marauder")
    boats.hireWorker(player, "Marta Kell")
    boats.damageBoat(boat, boats.UNSEAWORTHY_DAMAGE)

    # call
    line = boats.describeBoat(boat)

    # check
    assert "Marauder" in line
    assert "Piracy" in line
    assert "CAN'T SAIL" in line


def test_describeBoat_flags_an_idle_boat():
    # prepare
    player = Player()
    boat = boats.addBoat(player, 1)

    # check
    assert "idle - no crew, earning nothing" in boats.describeBoat(boat)


def test_unnamed_legacy_hands_can_be_moved_between_boats():
    # prepare - a pre-roles crew: a headcount with no names attached
    player = Player()
    first = boats.addBoat(player, 1)
    second = boats.addBoat(player, 1)
    player.workers = 2
    first["hands"] = 2

    # call
    assert boats.unassignHand(player, first["id"]) is True
    assert boats.assignHand(player, second["id"]) is True

    # check
    assert first["hands"] == 1
    assert second["hands"] == 1
    assert boats.unassignedHands(player) == 0


def test_unassignedHands_counts_only_what_is_ashore():
    # prepare
    player = Player()
    boat = boats.addBoat(player, 1)
    player.workers = 3
    boat["hands"] = 1

    # check
    assert boats.unassignedHands(player) == 2


def test_assignHand_refuses_when_there_are_none_ashore():
    # prepare
    player = Player()
    boat = boats.addBoat(player, 1)

    # check
    assert boats.assignHand(player, boat["id"]) is False
    assert boats.unassignHand(player, boat["id"]) is False


def test_bestBoat_answers_for_the_fleet_and_for_one_role():
    # prepare
    player = Player()
    boats.addBoat(player, 1, boats.ROLE_FISHING)
    fleet = boats.addBoat(player, 3, boats.ROLE_PIRACY)
    trawler = boats.addBoat(player, 2, boats.ROLE_HAULING)

    # check
    assert boats.bestBoat(player) is fleet
    assert boats.bestBoat(player, boats.ROLE_HAULING) is trawler
    assert boats.bestBoat(player, boats.ROLE_TRANSPORT) is None
    assert boats.bestBoat(Player()) is None


def test_operations_on_an_unknown_boat_are_refused():
    # prepare
    player = Player()
    boats.hireWorker(player, "Marta Kell")

    # check - every lookup fails safely rather than raising
    assert boats.getBoat(player, 99) is None
    assert boats.removeBoat(player, 99) is None
    assert boats.assignCrew(player, 99, "Marta Kell") is False
    assert boats.unassignCrew(player, 99, "Marta Kell") is False
    assert boats.assignHand(player, 99) is False
    assert boats.unassignHand(player, 99) is False
    assert boats.setRole(player, 99, boats.ROLE_PIRACY) is False
    assert boats.repairBoat(player, 99) is None


def test_hireWorker_needs_a_boat_to_hire_onto():
    # prepare - no fleet at all
    player = Player()

    # check
    assert boats.hireWorker(player, "Marta Kell") is False
    assert player.workers == 0


def test_dismissing_the_last_unnamed_hand_trims_the_boats():
    # prepare - a pre-roles crew aboard
    player = Player()
    boat = boats.addBoat(player, 1)
    player.workers = 2
    boat["hands"] = 2

    # call
    assert boats.dismissWorker(player) is True

    # check - the headcount and what's actually aboard stay in step
    assert player.workers == 1
    assert boat["hands"] == 1


def roleFleet(role, tier=2, crew=3, money=10000):
    """A player with one boat of the given role, crewed and solvent."""
    player = Player()
    player.money = money
    boat = boats.addBoat(player, tier, role, "Test Boat")
    for villager in villagers.VILLAGERS[:crew]:
        boats.hireWorker(player, villager["name"])
    return player, boat


def test_hauling_earns_money_every_day():
    # prepare
    player, boat = roleFleet(boats.ROLE_HAULING)
    startingMoney = player.money

    # call
    summary = boats.runDailyProduction(player)

    # check - money in, no fish, nothing at risk
    expected = boats.dailyIncome(boat)
    assert expected > 0
    assert summary["earned"] == expected
    assert summary["fishCaught"] == 0
    assert boat["damage"] == 0
    assert player.money == startingMoney + expected - summary["wagesPaid"]


def test_transport_earns_less_than_hauling_on_the_same_boat():
    # prepare - identical hulls and crews, different roles
    _, hauler = roleFleet(boats.ROLE_HAULING)
    _, ferry = roleFleet(boats.ROLE_TRANSPORT)

    # check - transport is the safe floor, so it pays less
    assert boats.dailyIncome(ferry) < boats.dailyIncome(hauler)


def test_piracy_earns_the_most_of_the_money_roles():
    # prepare
    _, pirate = roleFleet(boats.ROLE_PIRACY)
    _, hauler = roleFleet(boats.ROLE_HAULING)

    # check - it has to out-earn honest work, or the risk buys nothing
    assert boats.dailyIncome(pirate) > boats.dailyIncome(hauler)


def test_daily_income_scales_with_crew_and_hull():
    # prepare
    _, small = roleFleet(boats.ROLE_HAULING, tier=1, crew=1)
    _, moreCrew = roleFleet(boats.ROLE_HAULING, tier=1, crew=4)
    _, biggerHull = roleFleet(boats.ROLE_HAULING, tier=3, crew=1)

    # check - both levers matter, which is what makes crew assignment a decision
    assert boats.dailyIncome(moreCrew) > boats.dailyIncome(small)
    assert boats.dailyIncome(biggerHull) > boats.dailyIncome(small)


def test_a_boat_with_no_crew_earns_nothing():
    # prepare
    player = Player()
    player.money = 1000
    boats.addBoat(player, 3, boats.ROLE_HAULING)
    boats.addBoat(player, 1, boats.ROLE_FISHING)
    boats.hireWorker(player, "Marta Kell")  # lands on the hauler

    # call - take her back off again
    boats.unassignCrew(player, player.boats[0]["id"], "Marta Kell")
    summary = boats.runDailyProduction(player)

    # check - wages still owed, nothing earned
    assert summary["earned"] == 0
    assert summary["fishCaught"] == 0
    assert summary["wagesPaid"] == business.WORKER_DAILY_WAGE


def test_a_boat_at_sea_earns_nothing_while_the_captain_has_her():
    # prepare
    player, boat = roleFleet(boats.ROLE_HAULING)
    boat["atSea"] = True

    # call
    summary = boats.runDailyProduction(player)

    # check - that's the cost of taking the helm
    assert boats.isAtSea(boat) is True
    assert summary["earned"] == 0


def test_a_quiet_day_of_piracy_pays_without_incident():
    # prepare
    player, boat = roleFleet(boats.ROLE_PIRACY)

    # call - no trouble roll
    with patch("src.business.boats.random.random", return_value=1.0):
        with patch("src.business.boats.random.randint", return_value=0):
            summary = boats.runDailyProduction(player)

    # check
    assert summary["earned"] == boats.dailyIncome(boat)
    assert summary["damaged"] == []
    assert summary["lostAtSea"] == []
    assert boat["damage"] == 0


def test_a_bad_day_of_piracy_marks_the_hull():
    # prepare
    player, boat = roleFleet(boats.ROLE_PIRACY)

    # call - trouble, but nobody lost (the fatality roll is the stricter one)
    rolls = iter([0.0, 0.99])
    with patch("src.business.boats.random.random", side_effect=lambda: next(rolls)):
        summary = boats.runDailyProduction(player)

    # check
    assert summary["damaged"]
    assert summary["damaged"][0][0] == "Test Boat"
    assert boat["damage"] > 0
    assert summary["lostAtSea"] == []


def test_piracy_can_cost_a_villager_and_always_reports_it():
    # prepare
    player, boat = roleFleet(boats.ROLE_PIRACY)
    crewBefore = list(boat["crew"])

    # call - trouble, and the fatality roll lands
    with patch("src.business.boats.random.random", return_value=0.0):
        summary = boats.runDailyProduction(player)

    # check - gone from the boat and the roster, and named in the report
    assert len(summary["lostAtSea"]) == 1
    boatName, lost = summary["lostAtSea"][0]
    assert lost in crewBefore
    assert lost not in player.hiredWorkers
    assert lost not in boat["crew"]
    report = boats.describeDay(summary)
    assert any(lost in line for line in report)


def test_a_mixed_fleet_earns_from_every_role_at_once():
    # prepare - one boat of each role, one hand each
    player = Player()
    player.money = 10000
    for index, role in enumerate(boats.ROLE_ORDER):
        boats.addBoat(player, 2, role, "Boat %d" % index)
    roster = iter(villagers.VILLAGERS)
    for boat in player.boats:
        name = next(roster)["name"]
        boats.hireWorker(player, name)
        for other in player.boats:
            if name in other["crew"]:
                other["crew"].remove(name)
        boats.assignCrew(player, boat["id"], name)

    # call - keep piracy quiet so the assertion is about income, not luck
    with patch("src.business.boats.random.random", return_value=1.0):
        with patch("src.business.boats.random.randint", return_value=0):
            summary = boats.runDailyProduction(player)

    # check - fish from the fishing boat, money from the other three
    assert summary["fishCaught"] == business.tierInfo(2)["fishPerDay"]
    assert summary["earned"] == sum(
        boats.dailyIncome(boat)
        for boat in player.boats
        if boat["role"] != boats.ROLE_FISHING
    )


def test_describeDay_is_empty_on_a_day_with_no_fleet():
    # prepare
    player = Player()

    # check - nothing to report rather than a screen of zeroes
    assert boats.describeDay(boats.runDailyProduction(player)) == []


def test_describeDay_mentions_the_catch_the_takings_and_the_walkouts():
    # prepare
    summary = {
        "workers": 2,
        "fishCaught": 40,
        "wagesPaid": 20,
        "quit": 1,
        "quitNames": ["Owen Brackish"],
        "earned": 320,
        "fishSeized": 6,
        "damaged": [("Marauder", 12)],
        "lostAtSea": [("Marauder", "Marta Kell")],
    }

    # call
    report = " ".join(boats.describeDay(summary))

    # check
    assert "40 fish" in report
    assert "$320" in report
    assert "6 fish" in report
    assert "Marauder took 12%" in report
    assert "Marta Kell was lost" in report
    assert "Owen Brackish walked off" in report


def test_describeBoat_leads_with_the_role_and_labels_the_hull():
    # prepare - the case that read as a stutter: a Fishing Fleet hull that is
    # also a fishing boat
    player = Player()
    boat = boats.addBoat(player, 3, boats.ROLE_FISHING, "The Guppy")
    boats.hireWorker(player, "Marta Kell")

    # call
    line = boats.describeBoat(boat)

    # check - the role is what the player is deciding about, so it comes
    # first, and the hull is labelled rather than sitting bare beside it
    assert line.startswith("The Guppy | Fishing | Fishing Fleet hull")


def test_describeBoat_shows_what_she_earns():
    # prepare - one boat of each kind of earner
    player = Player()
    fisher = boats.addBoat(player, 2, boats.ROLE_FISHING, "Netter")
    pirate = boats.addBoat(player, 2, boats.ROLE_PIRACY, "Marauder")
    boats.hireWorker(player, "Marta Kell")
    boats.hireWorker(player, "Owen Brackish")
    boats.unassignCrew(player, fisher["id"], "Owen Brackish")
    boats.assignCrew(player, pirate["id"], "Owen Brackish")

    # check - a player can tell a boat that pays her wages from one that doesn't
    assert "%d fish/day" % boats.dailyCatch(fisher) in boats.describeBoat(fisher)
    assert "$%d/day" % boats.dailyIncome(pirate) in boats.describeBoat(pirate)


def test_describeBoat_says_when_she_is_away():
    # prepare
    player = Player()
    boat = boats.addBoat(player, 2, boats.ROLE_PIRACY, "Marauder")
    boats.hireWorker(player, "Marta Kell")
    boat["atSea"] = True

    # check
    assert "AT SEA" in boats.describeBoat(boat)


def test_fleet_totals_ignore_boats_that_are_away():
    # prepare - two earners, one of them out with the captain
    player = Player()
    home = boats.addBoat(player, 2, boats.ROLE_HAULING, "Mule")
    away = boats.addBoat(player, 2, boats.ROLE_HAULING, "Gone")
    boats.hireWorker(player, "Marta Kell")
    boats.hireWorker(player, "Owen Brackish")
    boats.unassignCrew(player, home["id"], "Owen Brackish")
    boats.assignCrew(player, away["id"], "Owen Brackish")
    away["atSea"] = True

    # check - the headline figure matches what will actually arrive tomorrow
    assert boats.fleetDailyIncome(player) == boats.dailyIncome(home)
    assert boats.dailyPayroll(player) == 2 * business.WORKER_DAILY_WAGE


def test_needsAttention_is_quiet_when_the_fleet_is_fine():
    # prepare - a crewed, sound boat with nobody spare
    player = Player()
    boats.addBoat(player, 2, boats.ROLE_HAULING)
    boats.hireWorker(player, "Marta Kell")

    # check - a notice that fires when nothing is wrong stops being read
    assert boats.needsAttention(player) == []


def test_needsAttention_reports_a_boat_that_cannot_sail():
    # prepare
    player = Player()
    boat = boats.addBoat(player, 2, boats.ROLE_PIRACY, "Kipper")
    boats.hireWorker(player, "Marta Kell")
    boats.damageBoat(boat, boats.UNSEAWORTHY_DAMAGE)

    # check
    assert any(
        "Kipper too damaged" in notice for notice in boats.needsAttention(player)
    )


def test_needsAttention_reports_idle_boats_and_idle_hands():
    # prepare - a boat with nobody on her, and a hand ashore
    player = Player()
    crewed = boats.addBoat(player, 2, boats.ROLE_HAULING, "Mule")
    boats.addBoat(player, 2, boats.ROLE_HAULING, "Spare")
    boats.hireWorker(player, "Marta Kell")
    boats.hireWorker(player, "Owen Brackish")
    boats.unassignCrew(player, crewed["id"], "Owen Brackish")

    # call
    notices = " ".join(boats.needsAttention(player))

    # check - both kinds of waste are named
    assert "Spare sitting idle" in notices
    assert "1 hand ashore on full wages" in notices


def test_needsAttention_ignores_a_boat_the_captain_has_taken_out():
    # prepare - a boat away with the player is neither idle nor stuck. Her
    # crew list stays intact while she's out (startVoyage takes a copy), so
    # they aren't ashore either.
    player = Player()
    boat = boats.addBoat(player, 2, boats.ROLE_PIRACY)
    boats.hireWorker(player, "Marta Kell")
    boat["atSea"] = True
    boats.damageBoat(boat, boats.UNSEAWORTHY_DAMAGE)

    # check
    assert boats.needsAttention(player) == []


def test_describeDay_puts_the_wages_next_to_the_takings():
    # prepare
    summary = {
        "workers": 3,
        "fishCaught": 30,
        "wagesPaid": 30,
        "quit": 0,
        "quitNames": [],
        "earned": 129,
        "fishSeized": 0,
        "damaged": [],
        "lostAtSea": [],
        "plunder": 129,
        "raidDays": 1,
    }

    # call
    report = " ".join(boats.describeDay(summary))

    # check - one line the player can read as a day's profit or loss
    assert "brought in $129 and 30 fish, and paid $30 in wages" in report


def test_describeDay_says_where_to_repair_a_damaged_boat():
    # prepare
    summary = {
        "workers": 1,
        "fishCaught": 0,
        "wagesPaid": 10,
        "quit": 0,
        "quitNames": [],
        "earned": 40,
        "fishSeized": 0,
        "damaged": [("Kipper", 11)],
        "lostAtSea": [],
        "plunder": 40,
        "raidDays": 1,
    }

    # check - the report says what to do about it, not just what happened
    assert "Manage Fleet to repair her" in " ".join(boats.describeDay(summary))
