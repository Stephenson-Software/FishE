from src.business import business
from src.business import boats
from src.npc import villagers
from src.player.player import Player


def createEmployedPlayer(name="Marta Kell", tier=1):
    player = Player()
    boats.addBoat(player, tier)
    player.money = 1000
    # hireWorker auto-berths on the first boat with room.
    boats.hireWorker(player, name)
    return player


def test_roster_covers_the_largest_crew():
    # check - every berth on the biggest boat can be filled with a named
    # villager, so the player never runs out of people to hire
    maxWorkers = max(tier["maxWorkers"] for tier in business.BOAT_TIERS)
    assert len(villagers.VILLAGERS) >= maxWorkers


def test_roster_entries_are_complete_and_unique():
    # check - hiring and dialogue both read these fields by name
    names = [villager["name"] for villager in villagers.VILLAGERS]
    assert len(names) == len(set(names))
    for villager in villagers.VILLAGERS:
        assert villager["name"]
        assert villager["blurb"]
        assert villager["specialty"]
        assert villager["backstory"]


def test_getVillager():
    # call
    found = villagers.getVillager(villagers.VILLAGERS[0]["name"])

    # check
    assert found is villagers.VILLAGERS[0]
    assert villagers.getVillager("Nobody At All") is None


def test_availableVillagers_excludes_the_hired():
    # prepare
    player = createEmployedPlayer()

    # call
    available = villagers.availableVillagers(player)

    # check
    assert len(available) == len(villagers.VILLAGERS) - 1
    assert all(villager["name"] != "Marta Kell" for villager in available)


def test_joinNames():
    # check - read back the way a person would say it out loud
    assert villagers.joinNames([]) == ""
    assert villagers.joinNames(["A"]) == "A"
    assert villagers.joinNames(["A", "B"]) == "A and B"
    assert villagers.joinNames(["A", "B", "C"]) == "A, B and C"


def test_createCrewNPC_uses_the_roster_entry():
    # prepare
    player = createEmployedPlayer()

    # call
    npc = villagers.createCrewNPC(player, "Marta Kell")

    # check
    assert npc.name == "Marta Kell"
    assert npc.backstory == villagers.getVillager("Marta Kell")["backstory"]


def test_createCrewNPC_work_dialogue_reflects_the_boat():
    # prepare - the same hand on a Rowboat and on a Fishing Fleet
    rowboatPlayer = createEmployedPlayer(tier=1)
    fleetPlayer = createEmployedPlayer(tier=3)

    # call - question 2 is "How's the work going?"
    rowboatAnswer = villagers.createCrewNPC(rowboatPlayer, "Marta Kell")
    fleetAnswer = villagers.createCrewNPC(fleetPlayer, "Marta Kell")

    # check - the answer quotes the tier's own fish-per-day figure
    assert "%d fish a day" % business.tierInfo(1)[
        "fishPerDay"
    ] in rowboatAnswer.get_dialogue_response(1)
    assert "%d fish a day" % business.tierInfo(3)[
        "fishPerDay"
    ] in fleetAnswer.get_dialogue_response(1)
    assert "mending nets" in rowboatAnswer.get_dialogue_response(1)


def test_createCrewNPC_work_dialogue_is_honest_off_a_fishing_boat():
    # prepare - the only boat is a piracy boat, so hiring berths her there
    player = Player()
    boats.addBoat(player, 2, role=boats.ROLE_PIRACY)
    player.money = 1000
    boats.hireWorker(player, "Marta Kell")

    # call - question 2 is "How's the work going?"
    npc = villagers.createCrewNPC(player, "Marta Kell")
    response = npc.get_dialogue_response(1)

    # check - no fish figure is quoted; the role's own summary is
    assert "fish a day" not in response
    assert boats.ROLES[boats.ROLE_PIRACY]["summary"] in response


def test_createCrewNPC_work_dialogue_handles_an_unassigned_hand():
    # prepare - hired, then pulled off her boat with nowhere else to work
    player = Player()
    boat = boats.addBoat(player, 1)
    player.money = 1000
    boats.hireWorker(player, "Marta Kell")
    boats.unassignCrew(player, boat["id"], "Marta Kell")

    # call
    npc = villagers.createCrewNPC(player, "Marta Kell")
    response = npc.get_dialogue_response(1)

    # check
    assert "Not assigned to a boat" in response


def test_createCrewNPC_wage_dialogue_warns_when_payroll_is_short():
    # prepare - a crew of three with less than a day's payroll on hand
    player = createEmployedPlayer()
    boats.hireWorker(player, "Owen Brackish")
    boats.hireWorker(player, "Piety Shaw")
    player.money = 5
    npc = villagers.createCrewNPC(player, "Marta Kell")

    # call - question 4 is "Are the wages treating you right?"
    response = npc.get_dialogue_response(3)

    # check
    assert "$%d a day" % (3 * business.WORKER_DAILY_WAGE) in response


def test_createCrewNPC_wage_dialogue_is_content_when_payroll_is_covered():
    # prepare
    player = createEmployedPlayer()
    npc = villagers.createCrewNPC(player, "Marta Kell")

    # call
    response = npc.get_dialogue_response(3)

    # check
    assert "No complaints" in response


def test_createCrewNPC_hides_locked_questions():
    # prepare - a lone hand on a Rowboat with an unnamed business
    player = createEmployedPlayer(tier=1)
    npc = villagers.createCrewNPC(player, "Marta Kell")

    # call
    questions = [option["question"] for option in npc.get_dialogue_options()]

    # check - the crowded/name/fleet questions have nothing to be about yet
    assert "Getting crowded out there, isn't it?" not in questions
    assert "What do you make of the name?" not in questions
    assert "Ever think about your own boat someday?" not in questions


def test_createCrewNPC_unlocks_the_crowded_question_when_full():
    # prepare - fill every berth on the Rowboat
    player = createEmployedPlayer(tier=1)
    for villager in villagers.availableVillagers(player)[
        : business.tierInfo(1)["maxWorkers"] - 1
    ]:
        boats.hireWorker(player, villager["name"])
    npc = villagers.createCrewNPC(player, "Marta Kell")

    # call
    questions = [option["question"] for option in npc.get_dialogue_options()]

    # check
    assert "Getting crowded out there, isn't it?" in questions


def test_createCrewNPC_unlocks_the_name_question_once_named():
    # prepare
    player = createEmployedPlayer()
    player.businessName = "Kell & Co."
    npc = villagers.createCrewNPC(player, "Marta Kell")

    # call
    options = npc.get_dialogue_options()
    questions = [option["question"] for option in options]
    index = questions.index("What do you make of the name?")

    # check - the response quotes the name the player actually chose
    assert "Kell & Co." in npc.get_dialogue_response(index)


def test_createCrewNPC_unlocks_the_ambition_question_on_a_fleet():
    # prepare
    player = createEmployedPlayer(tier=len(business.BOAT_TIERS))
    npc = villagers.createCrewNPC(player, "Marta Kell")

    # call
    questions = [option["question"] for option in npc.get_dialogue_options()]

    # check
    assert "Ever think about your own boat someday?" in questions


def test_createCrewNPC_falls_back_for_an_unnamed_legacy_hand():
    # prepare - a name that isn't on the roster, as an old save's crew would be
    player = Player()
    boats.addBoat(player, 1)
    player.money = 100
    player.workers = 1

    # call
    npc = villagers.createCrewNPC(player, "Some Old Hand")

    # check - they still hold a conversation rather than blowing up
    assert npc.name == "Some Old Hand"
    assert npc.backstory
    assert npc.get_dialogue_response(0) == npc.backstory


def test_createCrewNPC_boat_dialogue_is_staged_by_tier():
    # prepare - the same hand on each boat in the ladder
    responses = {}
    for tier in (1, 2, 3):
        player = createEmployedPlayer(tier=tier)
        npc = villagers.createCrewNPC(player, "Marta Kell")
        # question 3 is "How's the boat treating you?"
        responses[tier] = npc.get_dialogue_response(2)

    # check - each tier gets its own line, naming that tier's boat
    assert len(set(responses.values())) == 3
    for tier, response in responses.items():
        assert business.tierInfo(tier)["name"] in response


def test_createCrewNPC_crowded_response_quotes_the_berth_count():
    # prepare - fill every berth on the Rowboat
    player = createEmployedPlayer(tier=1)
    for villager in villagers.availableVillagers(player)[
        : business.tierInfo(1)["maxWorkers"] - 1
    ]:
        boats.hireWorker(player, villager["name"])
    npc = villagers.createCrewNPC(player, "Marta Kell")
    questions = [option["question"] for option in npc.get_dialogue_options()]

    # call
    index = questions.index("Getting crowded out there, isn't it?")
    response = npc.get_dialogue_response(index)

    # check
    assert "All %d berths" % business.tierInfo(1)["maxWorkers"] in response


def test_createCrewNPC_ambition_response_mentions_the_business():
    # prepare
    player = createEmployedPlayer(tier=len(business.BOAT_TIERS))
    player.businessName = "Kell & Co."
    npc = villagers.createCrewNPC(player, "Marta Kell")
    questions = [option["question"] for option in npc.get_dialogue_options()]

    # call
    index = questions.index("Ever think about your own boat someday?")

    # check
    assert "Kell & Co." in npc.get_dialogue_response(index)
