from unittest.mock import patch

from src.business import adventures
from src.business import boats
from src.npc import villagers
from src.player.player import Player
from src.stats.stats import Stats


def createVoyage(role=None, tier=2, crew=None, plan=1, supplies=None, damage=0):
    """A player, a crewed boat, and a voyage already under way."""
    player = Player()
    player.money = 5000
    boat = boats.addBoat(player, tier, role or boats.ROLE_PIRACY, "Marauder")
    for name in crew or ["Marta Kell", "Owen Brackish"]:
        boats.hireWorker(player, name)
    if damage:
        boats.damageBoat(boat, damage)
    chosen = adventures.VOYAGE_PLANS[plan]
    if supplies is None:
        supplies = adventures.recommendedSupplies(boat, chosen)
    return player, boat, adventures.startVoyage(boat, chosen, supplies)


def test_plans_get_longer_richer_and_less_forgiving():
    for shorter, longer in zip(adventures.VOYAGE_PLANS, adventures.VOYAGE_PLANS[1:]):
        assert longer["legs"] > shorter["legs"]
        assert longer["rewardMultiplier"] > shorter["rewardMultiplier"]


def test_recommended_supplies_feed_everyone_for_the_whole_voyage():
    # prepare
    player, boat, _ = createVoyage(crew=["Marta Kell", "Owen Brackish", "Piety Shaw"])
    plan = adventures.VOYAGE_PLANS[2]

    # check
    assert adventures.recommendedSupplies(boat, plan) == 3 * plan["legs"]


def test_starting_a_voyage_takes_the_boat_out_of_the_fleet_economy():
    # prepare
    player, boat, voyage = createVoyage()

    # check - she earns nothing at home while the player has her
    assert boats.isAtSea(boat) is True
    assert boats.runDailyProduction(player)["earned"] == 0


def test_a_damaged_boat_starts_the_voyage_already_hurt():
    # prepare - sail out on a boat that was never repaired
    player, boat, voyage = createVoyage(damage=30)

    # check - that's the player's choice to make, and it carries
    assert voyage["hull"] == boats.MAX_DAMAGE - 30


def test_specialists_aboard_unlock_choices_nobody_else_offers():
    # prepare - the same event, with and without the weather-reader aboard
    _, _, without = createVoyage(crew=["Marta Kell", "Owen Brackish"])
    _, _, with_iris = createVoyage(crew=["Marta Kell", "Iris Dunmore"])
    squall = next(event for event in adventures.EVENTS if event["id"] == "squall")

    # call
    plain = [c["text"] for c in adventures.offeredChoices(without, squall)]
    gated = [c["text"] for c in adventures.offeredChoices(with_iris, squall)]

    # check - who you brought shows up on screen, by name
    assert len(gated) == len(plain) + 1
    assert any("Iris Dunmore" in text for text in gated)
    assert not any("Iris Dunmore" in text for text in plain)


def test_specialistAboard_finds_only_who_is_actually_on_this_boat():
    # prepare
    _, _, voyage = createVoyage(crew=["Iris Dunmore"])

    # check
    assert adventures.specialistAboard(voyage, "reading the weather") == "Iris Dunmore"
    assert adventures.specialistAboard(voyage, "patching the hull") is None


def test_events_are_filtered_to_the_boat_role():
    # check - a fishing voyage never meets a patrol cutter, and a raid never
    # frets about its passengers
    fishing = {event["id"] for event in adventures.eventsFor(boats.ROLE_FISHING)}
    piracy = {event["id"] for event in adventures.eventsFor(boats.ROLE_PIRACY)}
    assert "good_grounds" in fishing
    assert "patrol" not in fishing
    assert "patrol" in piracy
    assert "good_grounds" not in piracy


def test_every_event_offers_something_to_a_crew_with_no_specialists():
    # prepare - a crew with no roster specialties that any event asks for
    _, _, voyage = createVoyage(crew=["Halvard Stoke"])

    # check - no event can ever leave the player with an empty menu
    for event in adventures.EVENTS:
        if voyage["role"] not in event["roles"]:
            continue
        assert adventures.offeredChoices(voyage, event)


def test_every_choice_returns_narration():
    # prepare - a crew carrying every specialty the events ask for
    crew = [v["name"] for v in villagers.VILLAGERS[:8]]
    for role in boats.ROLE_ORDER:
        _, _, voyage = createVoyage(role=role, tier=3, crew=crew)
        for event in adventures.eventsFor(role):
            for choice in adventures.offeredChoices(voyage, event):
                text = adventures.resolveChoice(voyage, choice)
                assert isinstance(text, str) and text


def test_a_leg_eats_supplies():
    # prepare
    _, _, voyage = createVoyage()
    before = voyage["supplies"]

    # call
    adventures.advanceLeg(voyage)

    # check
    assert voyage["supplies"] == before - adventures.crewAboard(voyage)
    assert voyage["leg"] == 1


def test_running_out_of_supplies_starves_the_crew():
    # prepare - sailed out on nothing
    _, _, voyage = createVoyage(supplies=0)

    # call - force the starvation roll
    with patch("src.business.adventures.random.random", return_value=0.0):
        notes = adventures.advanceLeg(voyage)

    # check - the player is told, and it costs a hand
    assert any("nothing left to eat" in note for note in notes)
    assert adventures.crewAboard(voyage) == 1


def test_a_voyage_ends_when_the_last_leg_is_sailed():
    # prepare
    _, _, voyage = createVoyage(plan=0)

    # call
    for _ in range(voyage["legs"]):
        assert adventures.isOver(voyage) is False
        adventures.advanceLeg(voyage)

    # check
    assert adventures.isOver(voyage) is True
    assert voyage["status"] == "home"


def test_a_hull_reaching_zero_founders_the_voyage():
    # prepare
    _, _, voyage = createVoyage()

    # call
    adventures.damage(voyage, voyage["hull"])

    # check
    assert voyage["status"] == "foundering"
    assert adventures.isOver(voyage) is True


def test_losing_the_whole_crew_founders_the_voyage():
    # prepare
    _, _, voyage = createVoyage(crew=["Marta Kell"])

    # call
    adventures.loseCrew(voyage)
    notes = adventures.advanceLeg(voyage)

    # check
    assert voyage["status"] == "foundering"
    assert any("nobody left" in note for note in notes)


def test_every_leg_earns_something_for_its_role():
    # prepare - a money role and the fishing role
    _, _, raider = createVoyage(role=boats.ROLE_PIRACY)
    _, _, fisher = createVoyage(role=boats.ROLE_FISHING)

    # call
    adventures.advanceLeg(raider)
    adventures.advanceLeg(fisher)

    # check - piracy pays in coin, fishing pays in fish
    assert raider["money"] > 0
    assert fisher["fish"] > 0
    assert fisher["money"] == 0


def test_a_longer_plan_is_worth_more_per_leg():
    # prepare - the same boat and crew, near water and far
    _, _, near = createVoyage(plan=0)
    _, _, far = createVoyage(plan=2)

    # call
    adventures.advanceLeg(near)
    adventures.advanceLeg(far)

    # check
    assert far["money"] > near["money"]


def test_finishing_a_voyage_pays_out_and_brings_her_home():
    # prepare
    player, boat, voyage = createVoyage()
    adventures.gain(voyage, money=1200, fishCount=30)
    voyage["status"] = "home"
    moneyBefore = player.money
    stats = Stats()

    # call
    summary = adventures.finishVoyage(player, voyage, stats)

    # check
    assert summary["foundered"] is False
    assert summary["money"] == 1200
    assert summary["fish"] == 30
    assert player.money == moneyBefore + 1200
    assert player.fishCount == 30
    assert boats.isAtSea(boat) is False
    assert stats.totalVoyagesCaptained == 1


def test_a_foundering_voyage_loses_the_hold_but_not_the_boat():
    # prepare - a rich hold and a hull that gave out
    player, boat, voyage = createVoyage()
    adventures.gain(voyage, money=3000, fishCount=200)
    voyage["status"] = "foundering"
    moneyBefore = player.money
    stats = Stats()

    # call
    summary = adventures.finishVoyage(player, voyage, stats)

    # check - everything aboard is gone, but she's still in the fleet
    assert summary["foundered"] is True
    assert summary["money"] == 0
    assert player.money == moneyBefore
    assert player.fishCount == 0
    assert boat in player.boats
    assert boat["damage"] > boats.UNSEAWORTHY_DAMAGE
    assert stats.totalVoyagesFoundered == 1


def test_hull_damage_taken_at_sea_follows_the_boat_home():
    # prepare
    player, boat, voyage = createVoyage()
    adventures.damage(voyage, 40)
    voyage["status"] = "home"

    # call
    adventures.finishVoyage(player, voyage)

    # check
    assert boat["damage"] == 40


def test_crew_lost_at_sea_are_off_the_roster_for_good():
    # prepare
    player, boat, voyage = createVoyage(crew=["Marta Kell", "Owen Brackish"])
    lost = adventures.loseCrew(voyage, "Owen Brackish")
    voyage["status"] = "home"

    # call
    summary = adventures.finishVoyage(player, voyage)

    # check
    assert lost == "Owen Brackish"
    assert summary["crewLost"] == ["Owen Brackish"]
    assert "Owen Brackish" not in player.hiredWorkers
    assert "Owen Brackish" not in boat["crew"]
    assert player.workers == 1


def test_unnamed_hands_lost_at_sea_are_taken_off_the_headcount():
    # prepare - a pre-roles crew with no names
    player = Player()
    player.money = 1000
    boat = boats.addBoat(player, 2, boats.ROLE_HAULING, "Mule")
    player.workers = 2
    boat["hands"] = 2
    voyage = adventures.startVoyage(boat, adventures.VOYAGE_PLANS[0], 20)

    # call
    assert adventures.loseCrew(voyage) is None
    voyage["status"] = "home"
    adventures.finishVoyage(player, voyage)

    # check
    assert boat["hands"] == 1
    assert player.workers == 1


def test_a_captained_voyage_beats_leaving_her_to_the_crew():
    # prepare - the same boat, one day passive versus one leg captained
    player, boat, voyage = createVoyage(role=boats.ROLE_PIRACY, tier=3, plan=2)
    boat["atSea"] = False
    passivePerDay = boats.dailyIncome(boat)
    boat["atSea"] = True

    # call
    adventures.advanceLeg(voyage)

    # check - taking the helm is what makes real money; that's the whole point
    assert voyage["money"] > passivePerDay


def test_every_outcome_branch_is_reachable():
    # prepare - a crew carrying every specialty, on a boat that can meet every
    # event, with the dice forced to both extremes in turn
    crew = [v["name"] for v in villagers.VILLAGERS[:9]]
    for lucky in (0.0, 0.99):
        for role in boats.ROLE_ORDER:
            _, _, voyage = createVoyage(role=role, tier=3, crew=crew, plan=2)
            with patch("src.business.adventures.random.random", return_value=lucky):
                for event in adventures.eventsFor(role):
                    for choice in adventures.offeredChoices(voyage, event):
                        # a voyage can founder mid-sweep; keep her afloat so
                        # every branch gets exercised rather than short-cutting
                        voyage["hull"] = boats.MAX_DAMAGE
                        voyage["status"] = "sailing"
                        voyage["crew"] = list(crew)
                        assert adventures.resolveChoice(voyage, choice)


def test_addSupplies_and_repair_are_bounded_sensibly():
    # prepare
    _, _, voyage = createVoyage()
    adventures.damage(voyage, 30)

    # call
    adventures.repair(voyage, 500)
    adventures.addSupplies(voyage, 5)

    # check - a repair at sea can't take her past sound
    assert voyage["hull"] == boats.MAX_DAMAGE


def test_useSupplies_never_goes_negative():
    # prepare
    _, _, voyage = createVoyage(supplies=3)

    # call
    adventures.useSupplies(voyage, 99)

    # check
    assert voyage["supplies"] == 0


def test_loseCrew_with_nobody_left_returns_nothing():
    # prepare
    _, _, voyage = createVoyage(crew=["Marta Kell"])
    adventures.loseCrew(voyage)

    # check - the engine doesn't fall over trying to kill an empty boat
    assert adventures.loseCrew(voyage) is None
    assert adventures.crewAboard(voyage) == 0


def test_planFor_reads_the_table():
    assert adventures.planFor(0) is adventures.VOYAGE_PLANS[0]
    assert adventures.supplyCost(5) == 5 * adventures.SUPPLY_COST


def test_estimateVoyage_turns_the_multiplier_into_money():
    # prepare - the same boat against every plan
    _, boat, _ = createVoyage(role=boats.ROLE_PIRACY, tier=3)
    boat["atSea"] = False

    # call
    estimates = [
        adventures.estimateVoyage(boat, plan)[0] for plan in adventures.VOYAGE_PLANS
    ]

    # check - a longer voyage is worth more in coin, not just in multiplier,
    # which is what the plan menu shows the player
    assert estimates == sorted(estimates)
    assert estimates[0] > 0


def test_estimateVoyage_answers_in_fish_for_a_fishing_boat():
    # prepare
    _, boat, _ = createVoyage(role=boats.ROLE_FISHING, tier=2)

    # call
    money, catch = adventures.estimateVoyage(boat, adventures.VOYAGE_PLANS[1])

    # check
    assert money == 0
    assert catch > 0


def test_estimateVoyage_is_the_floor_not_a_promise():
    # prepare - a voyage sailed with every event choice taken
    player, boat, voyage = createVoyage(role=boats.ROLE_PIRACY, tier=3, plan=1)
    estimated, _ = adventures.estimateVoyage(boat, voyage["plan"])

    # call - sail it with no event income at all
    for _ in range(voyage["legs"]):
        adventures.advanceLeg(voyage)

    # check - the legs alone make the estimate; events only ever add to it
    assert voyage["money"] == estimated


def test_legsSupplied_counts_whole_days_of_food():
    # prepare - three hands eat three a day
    _, boat, _ = createVoyage(crew=["Marta Kell", "Owen Brackish", "Piety Shaw"])

    # check
    assert adventures.legsSupplied(boat, 9) == 3
    assert adventures.legsSupplied(boat, 10) == 3
    assert adventures.legsSupplied(boat, 0) == 0


def test_legsSupplied_with_nobody_aboard():
    # prepare - an empty boat eats nothing, and mustn't divide by zero
    player = Player()
    boat = boats.addBoat(player, 1, boats.ROLE_HAULING)

    # check
    assert adventures.legsSupplied(boat, 10) == 0


def test_turning_back_ends_the_voyage_and_keeps_the_hold():
    # prepare - a voyage with something already aboard
    player, boat, voyage = createVoyage()
    adventures.gain(voyage, money=800, fishCount=20)

    # call
    adventures.turnBack(voyage)
    summary = adventures.finishVoyage(player, voyage)

    # check - cutting your losses keeps them; only foundering forfeits the hold
    assert adventures.isOver(voyage) is True
    assert summary["turnedBack"] is True
    assert summary["foundered"] is False
    assert summary["money"] == 800
    assert summary["fish"] == 20


def test_a_voyage_that_ran_its_course_is_not_marked_as_broken_off():
    # prepare
    player, boat, voyage = createVoyage(plan=0)

    # call
    for _ in range(voyage["legs"]):
        adventures.advanceLeg(voyage)
    summary = adventures.finishVoyage(player, voyage)

    # check
    assert summary["turnedBack"] is False
