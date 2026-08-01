from src.location.enum.locationType import LocationType
from src.location import docks
from src.player.player import Player
from src.prompt.prompt import Prompt
from src.stats.stats import Stats
from src.ui.userInterface import UserInterface
from src.world.timeService import TimeService
from src.business import business
from src.business import adventures
from src.business import boats
from src.business import export
from src.housing import housing
from src.npc import villagers
from unittest.mock import MagicMock, patch


def createDocks():
    currentPrompt = Prompt("What would you like to do?")
    player = Player()
    stats = Stats()
    timeService = TimeService(player, stats)
    userInterface = UserInterface(currentPrompt, timeService, player)
    # fish() opens with a one-second "Fishing..." pause on the real front-end;
    # stub it so the tests neither print to the console nor wait it out.
    userInterface.showBusy = MagicMock()
    return docks.Docks(userInterface, currentPrompt, player, stats, timeService)


def test_initialization():
    # call
    docksInstance = createDocks()

    # check
    assert docksInstance.userInterface != None
    assert docksInstance.currentPrompt != None
    assert docksInstance.player != None
    assert docksInstance.stats != None
    assert docksInstance.timeService != None
    assert docksInstance.npc != None
    assert docksInstance.npc.name == "Sam the Dock Worker"


def test_run_fish_action():
    # prepare
    docksInstance = createDocks()
    docksInstance.userInterface.showOptions = MagicMock(return_value="1")
    docksInstance.fish = MagicMock()

    # call
    nextLocation = docksInstance.run()

    # check
    docksInstance.fish.assert_called_once()
    assert nextLocation == LocationType.DOCKS


def test_run_go_home_action():
    # prepare
    docksInstance = createDocks()
    docksInstance.userInterface.showOptions = MagicMock(return_value="3")

    # call
    nextLocation = docksInstance.run()

    # check
    assert nextLocation == LocationType.HOME


def test_run_talk_to_npc_action():
    # prepare
    docksInstance = createDocks()
    docksInstance.userInterface.showOptions = MagicMock(return_value="2")
    docksInstance.talkToNPC = MagicMock()

    # call
    nextLocation = docksInstance.run()

    # check
    assert nextLocation == LocationType.DOCKS
    docksInstance.talkToNPC.assert_called_once()


def test_talkToNPC():
    # prepare
    docksInstance = createDocks()
    docksInstance.userInterface.showInteractiveDialogue = MagicMock()

    # call
    docksInstance.talkToNPC()

    # check
    docksInstance.userInterface.showInteractiveDialogue.assert_called_once()
    call_args = docksInstance.userInterface.showInteractiveDialogue.call_args[0][0]
    assert call_args.name == "Sam the Dock Worker"
    assert len(call_args.get_dialogue_options()) > 0


def test_npc_business_dialogue_staged_by_boat_ownership():
    # prepare - no boat yet
    docksInstance = createDocks()

    # check
    response = docksInstance._businessDialogue()
    assert "No boat yet" in response


def test_npc_business_dialogue_staged_by_empty_crew():
    # prepare - a boat but no crew hired yet
    docksInstance = createDocks()
    boats.addBoat(docksInstance.player, 1)

    # check
    response = docksInstance._businessDialogue()
    assert "hire a crew" in response


def test_npc_business_dialogue_staged_by_tier():
    # prepare - one crewed boat per tier
    responses = {}
    for tier in (1, 2, 3):
        docksInstance = createDocks()
        boats.addBoat(docksInstance.player, tier)
        docksInstance.player.workers = 1
        responses[tier] = docksInstance._businessDialogue()

    # check - each tier gets distinct commentary
    assert len(set(responses.values())) == 3
    assert "Fishing Fleet" in responses[3] or "fleet" in responses[3].lower()


def test_npc_business_dialogue_mentions_business_name():
    # prepare
    docksInstance = createDocks()
    boats.addBoat(docksInstance.player, 1)
    docksInstance.player.workers = 1
    docksInstance.player.businessName = "Salty Dawn Fisheries"

    # check
    assert "Salty Dawn Fisheries" in docksInstance._businessDialogue()


def test_npc_dialogue_response_reflects_business_via_callable():
    # prepare - the NPC's dialogue option resolves through the live callable,
    # not a value frozen at construction time
    docksInstance = createDocks()
    optionIndex = next(
        i
        for i, option in enumerate(docksInstance.npc.get_dialogue_options())
        if option["question"] == "How's my fishing business doing?"
    )
    before = docksInstance.npc.get_dialogue_response(optionIndex)

    # call - buy a boat, then ask again
    boats.addBoat(docksInstance.player, 1)

    # check
    after = docksInstance.npc.get_dialogue_response(optionIndex)
    assert before != after
    assert "No boat yet" in before
    assert "hire a crew" in after


def test_run_go_to_shop_action():
    # prepare
    docksInstance = createDocks()
    docksInstance.userInterface.showOptions = MagicMock(return_value="4")

    # call
    nextLocation = docksInstance.run()

    # check
    assert nextLocation == LocationType.SHOP


def test_run_go_to_tavern_action():
    # prepare
    docksInstance = createDocks()
    docksInstance.userInterface.showOptions = MagicMock(return_value="5")

    # call
    nextLocation = docksInstance.run()

    # check
    assert nextLocation == LocationType.TAVERN


def test_run_go_to_bank_action():
    # prepare
    docksInstance = createDocks()
    docksInstance.userInterface.showOptions = MagicMock(return_value="6")

    # call
    nextLocation = docksInstance.run()

    # check
    assert nextLocation == LocationType.BANK


def test_fish():
    # prepare
    docksInstance = createDocks()
    # The active UI captures and times the reaction; mock a quick (perfect) one.
    docksInstance.userInterface.timedKeyPress = MagicMock(return_value=0.5)

    with patch("src.location.docks.random.randint", return_value=3):
        docksInstance.timeService.increaseTime = MagicMock(
            return_value={"evicted": False}
        )

        # call
        docksInstance.fish()

        # check - the trip announces itself through the front-end, so every UI
        # shows it rather than only the console seeing a print()
        docksInstance.userInterface.showBusy.assert_called_once()
        assert "Fishing" in docksInstance.userInterface.showBusy.call_args[0][0]
        # Player should catch fish based on success rate
        assert docksInstance.player.fishCount >= 1
        assert docksInstance.stats.totalFishCaught >= 1


def test_run_fish_action_low_energy():
    # prepare
    docksInstance = createDocks()
    docksInstance.player.energy = 5  # Too low to fish
    docksInstance.userInterface.showOptions = MagicMock(return_value="1")

    # call
    nextLocation = docksInstance.run()

    # check
    assert nextLocation == LocationType.DOCKS
    assert (
        docksInstance.currentPrompt.text
        == "You're too tired to fish! Go home and sleep."
    )


def test_fish_consumes_energy():
    # prepare
    docksInstance = createDocks()
    docksInstance.player.energy = 100
    docksInstance.userInterface.lotsOfSpace = MagicMock()
    docksInstance.userInterface.divider = MagicMock()
    docksInstance.userInterface.timedKeyPress = MagicMock(return_value=0.5)

    with patch("src.location.docks.random.randint", return_value=3):
        docksInstance.timeService.increaseTime = MagicMock(
            return_value={"evicted": False}
        )

        # call
        docksInstance.fish()

        # check
        assert docksInstance.player.energy == 100 - (
            3 * 10
        )  # Should lose 30 energy (3 hours * 10 per hour)


def test_fish_with_limited_energy():
    # prepare
    docksInstance = createDocks()
    docksInstance.player.energy = 25  # Only enough for 2 hours
    docksInstance.userInterface.lotsOfSpace = MagicMock()
    docksInstance.userInterface.divider = MagicMock()
    docksInstance.userInterface.timedKeyPress = MagicMock(return_value=0.5)

    with patch("src.location.docks.random.randint", return_value=5):
        docksInstance.timeService.increaseTime = MagicMock(
            return_value={"evicted": False}
        )

        # call
        docksInstance.fish()

        # check
        assert docksInstance.player.energy == 5  # Should be 25 - (2 * 10)
        assert (
            docksInstance.timeService.increaseTime.call_count == 2
        )  # Only fished for 2 hours due to energy limit


def test_fish_mentions_eviction_when_a_day_rolls_over_mid_trip():
    # A multi-hour trip can cross a day boundary invisibly; make sure that's
    # still reported in the trip's own message rather than going unnoticed.
    docksInstance = createDocks()
    docksInstance.userInterface.lotsOfSpace = MagicMock()
    docksInstance.userInterface.divider = MagicMock()
    docksInstance.userInterface.timedKeyPress = MagicMock(return_value=0.5)

    with patch("src.location.docks.random.randint", side_effect=[3, 6]):
        # the day rolls over (and evicts) partway through the trip
        docksInstance.timeService.increaseTime = MagicMock(
            side_effect=[
                {"evicted": False},
                {"evicted": True},
                {"evicted": False},
            ]
        )

        # call
        docksInstance.fish()

        # check
        assert housing.EVICTION_MESSAGE in docksInstance.currentPrompt.text


def test_fish_interactive_success():
    # Test that quick reactions result in successful catches
    docksInstance = createDocks()
    docksInstance.userInterface.lotsOfSpace = MagicMock()
    docksInstance.userInterface.divider = MagicMock()
    # Quick reaction => perfect-quality catch.
    docksInstance.userInterface.timedKeyPress = MagicMock(return_value=0.5)

    with patch("src.location.docks.random.randint", side_effect=[3, 6]):
        docksInstance.timeService.increaseTime = MagicMock(
            return_value={"evicted": False}
        )

        # call
        docksInstance.fish()

        # check - with 100% success rate, should get full catch
        assert (
            docksInstance.player.fishCount >= 3
        )  # Should get good catch with all successes
        assert docksInstance.stats.totalFishCaught >= 3


def test_fish_slow_reaction_yields_fewer_than_fast():
    # A slow reaction lands the lowest-quality tier; a fast one lands the best.
    # With identical rolls, slow should yield fewer fish (but still at least 1).
    def make_docks():
        d = createDocks()
        d.userInterface.lotsOfSpace = MagicMock()
        d.userInterface.divider = MagicMock()
        return d

    def fish_with_reaction(reactionTime):
        docksInstance = make_docks()
        docksInstance.userInterface.timedKeyPress = MagicMock(return_value=reactionTime)

        with patch("src.location.docks.random.randint", side_effect=[3, 10]):
            docksInstance.timeService.increaseTime = MagicMock(
                return_value={"evicted": False}
            )
            docksInstance.fish()
        return docksInstance.player.fishCount

    slow = fish_with_reaction(3.0)  # beyond the 2.0s window => poorest tier
    fast = fish_with_reaction(0.5)  # within half the window => perfect tier

    # check - a poor reaction still lands at least one fish, but fewer than a perfect one
    assert slow >= 1
    assert slow < fast


def test_getTimeOfDayModifier_windows():
    # prepare
    docksInstance = createDocks()

    # check - dawn and dusk boost the catch, midday suppresses it, else neutral
    dawnFactor, dawnLabel = docksInstance.getTimeOfDayModifier(6)
    duskFactor, duskLabel = docksInstance.getTimeOfDayModifier(18)
    middayFactor, middayLabel = docksInstance.getTimeOfDayModifier(12)
    nightFactor, nightLabel = docksInstance.getTimeOfDayModifier(2)

    assert dawnFactor > 1.0 and dawnLabel
    assert duskFactor > 1.0 and duskLabel
    assert middayFactor < 1.0 and middayLabel
    assert nightFactor == 1.0 and nightLabel == ""


def test_getWeatherModifier_options():
    # prepare
    docksInstance = createDocks()

    # check - rain boosts the catch, storms suppress it, clear is neutral
    rainyFactor, rainyLabel = docksInstance.getWeatherModifier("rainy")
    stormyFactor, stormyLabel = docksInstance.getWeatherModifier("stormy")
    clearFactor, clearLabel = docksInstance.getWeatherModifier("clear")

    assert rainyFactor > 1.0 and rainyLabel
    assert stormyFactor < 1.0 and stormyLabel
    assert clearFactor == 1.0 and clearLabel == ""


def test_fish_applies_weather_modifier():
    # prepare - fish in a storm (penalty) vs rain (bonus) with identical rolls
    def make_docks_in(weather):
        d = createDocks()
        d.userInterface.lotsOfSpace = MagicMock()
        d.userInterface.divider = MagicMock()
        d.timeService.weather = weather
        return d

    results = {}
    for weather in ("stormy", "rainy"):
        docksInstance = make_docks_in(weather)
        docksInstance.userInterface.timedKeyPress = MagicMock(return_value=0.5)
        with patch(
            "src.location.docks.random.randint", side_effect=[5, 10]
        ):  # 5 hours, baseFish 10
            docksInstance.timeService.increaseTime = MagicMock(
                return_value={"evicted": False}
            )
            docksInstance.fish()
        results[weather] = docksInstance.player.fishCount

    # check - the storm penalty yields fewer fish than the rain bonus
    assert results["stormy"] < results["rainy"]


def test_fish_mentions_weather_label():
    # prepare
    docksInstance = createDocks()
    docksInstance.userInterface.lotsOfSpace = MagicMock()
    docksInstance.userInterface.divider = MagicMock()
    docksInstance.userInterface.timedKeyPress = MagicMock(return_value=0.5)
    docksInstance.timeService.weather = "rainy"

    with patch("src.location.docks.random.randint", side_effect=[3, 6]):
        docksInstance.timeService.increaseTime = MagicMock(
            return_value={"evicted": False}
        )

        # call
        docksInstance.fish()

    # check
    assert "rain" in docksInstance.currentPrompt.text.lower()


def test_run_descriptor_mentions_current_weather():
    # prepare
    docksInstance = createDocks()
    docksInstance.timeService.weather = "stormy"
    docksInstance.userInterface.showOptions = MagicMock(return_value="3")

    # call
    docksInstance.run()

    # check
    descriptor = docksInstance.userInterface.showOptions.call_args[0][0]
    assert "Storm" in descriptor


def test_fish_applies_time_of_day_modifier():
    # prepare - fish at midday (penalty) vs dawn (bonus) with identical rolls
    def make_docks_at(hour):
        d = createDocks()
        d.userInterface.lotsOfSpace = MagicMock()
        d.userInterface.divider = MagicMock()
        d.timeService.time = hour
        return d

    results = {}
    for label, hour in (("midday", 12), ("dawn", 6)):
        docksInstance = make_docks_at(hour)
        docksInstance.userInterface.timedKeyPress = MagicMock(return_value=0.5)
        with patch(
            "src.location.docks.random.randint", side_effect=[5, 10]
        ):  # 5 hours, baseFish 10
            docksInstance.timeService.increaseTime = MagicMock(
                return_value={"evicted": False}
            )
            docksInstance.fish()
        results[label] = docksInstance.player.fishCount

    # check - the midday penalty yields fewer fish than the dawn bonus
    assert results["midday"] < results["dawn"]


def test_fish_higher_rod_widens_reaction_window():
    # prepare - a 2.5s reaction is "too slow" at rod level 1 (2.0s window) but
    # within the window at a high rod level, so it should catch more fish.
    def make_docks_with_rod(rodLevel):
        d = createDocks()
        d.userInterface.lotsOfSpace = MagicMock()
        d.userInterface.divider = MagicMock()
        d.player.rodLevel = rodLevel
        return d

    results = {}
    for label, rod in (("lowRod", 1), ("highRod", 5)):
        docksInstance = make_docks_with_rod(rod)
        # A 2.5s reaction is too slow at rod level 1 but within a high rod's window.
        docksInstance.userInterface.timedKeyPress = MagicMock(return_value=2.5)
        with patch("src.location.docks.random.randint", side_effect=[5, 10]):
            docksInstance.timeService.increaseTime = MagicMock(
                return_value={"evicted": False}
            )
            docksInstance.fish()
        results[label] = docksInstance.player.fishCount

    # check - the wider window of the better rod lands more catches
    assert results["highRod"] > results["lowRod"]


def test_run_manage_fleet_action():
    # prepare
    docksInstance = createDocks()
    docksInstance.userInterface.showOptions = MagicMock(return_value="7")
    docksInstance.manageFleet = MagicMock()

    # call
    nextLocation = docksInstance.run()

    # check
    assert nextLocation == LocationType.DOCKS
    docksInstance.manageFleet.assert_called_once()


def fleetMenu(docksInstance):
    """The option labels manageFleet last showed, so a test can assert on what
    the player was actually offered rather than on a hardcoded position."""
    return docksInstance.userInterface.showOptions.call_args[0][1]


def fleetChooser(*wanted):
    """A showOptions stand-in that drives a menu by label instead of position.

    Each argument is a prefix of the option to pick from whatever menu is
    showing next; once they run out it picks Back (always the last entry). The
    fleet menus grow and shrink with game state, so choosing by label keeps
    these tests from breaking every time an option is added."""
    remaining = list(wanted)

    def choose(descriptor, options):
        if remaining:
            prefix = remaining.pop(0)
            for index, option in enumerate(options, start=1):
                if option.startswith(prefix):
                    return str(index)
        return str(len(options))

    return choose


def test_manageFleet_buy_boat():
    # prepare - no fleet, money for a Rowboat; "1" = Buy, "" = keep the default
    # name, then Back
    docksInstance = createDocks()
    docksInstance.player.money = business.tierInfo(1)["cost"]
    docksInstance.userInterface.showOptions = MagicMock(
        side_effect=fleetChooser("Buy a")
    )
    docksInstance.userInterface.promptForText = MagicMock(return_value="")

    # call
    docksInstance.manageFleet()

    # check - one boat in the fleet, fishing by default, and it cost money
    assert len(docksInstance.player.boats) == 1
    assert docksInstance.player.boats[0]["role"] == boats.ROLE_FISHING
    assert docksInstance.player.money == 0
    assert docksInstance.stats.boatsOwned == 1


def test_manageFleet_buy_boat_names_her():
    # prepare
    docksInstance = createDocks()
    docksInstance.player.money = business.tierInfo(1)["cost"]
    docksInstance.userInterface.showOptions = MagicMock(
        side_effect=fleetChooser("Buy a")
    )
    docksInstance.userInterface.promptForText = MagicMock(return_value="Marauder")

    # call
    docksInstance.manageFleet()

    # check
    assert docksInstance.player.boats[0]["name"] == "Marauder"


def test_manageFleet_buy_boat_insufficient_funds():
    # prepare
    docksInstance = createDocks()
    docksInstance.player.money = 0

    # call - the action directly, since leaving the fleet menu resets the prompt
    docksInstance._buyBoat()

    # check - no boat, and the message says what it costs and what they have
    assert docksInstance.player.boats == []
    assert "$%d" % business.tierInfo(1)["cost"] in docksInstance.currentPrompt.text
    assert "$0.00" in docksInstance.currentPrompt.text


def test_manageFleet_hire_puts_the_villager_straight_to_work():
    # prepare - a boat with berths free; "2" = Hire, "1" = first villager
    docksInstance = createDocks()
    boats.addBoat(docksInstance.player, 1)
    docksInstance.userInterface.showOptions = MagicMock(
        side_effect=fleetChooser("Hire a Villager", villagers.VILLAGERS[0]["name"])
    )

    # call
    docksInstance.manageFleet()

    # check - hired onto the roster AND aboard, so they actually earn
    name = villagers.VILLAGERS[0]["name"]
    assert docksInstance.player.hiredWorkers == [name]
    assert docksInstance.player.boats[0]["crew"] == [name]
    assert docksInstance.stats.totalWorkersHired == 1


def test_manageFleet_hire_capacity_is_the_whole_fleet():
    # prepare - two Rowboats, so the cap is both boats' berths together
    docksInstance = createDocks()
    boats.addBoat(docksInstance.player, 1)
    boats.addBoat(docksInstance.player, 1)
    berths = business.tierInfo(1)["maxWorkers"] * 2
    for villager in villagers.VILLAGERS[:berths]:
        assert boats.hireWorker(docksInstance.player, villager["name"]) is True

    # check - full at the fleet's capacity, not one boat's
    assert docksInstance.player.workers == berths
    assert boats.hireWorker(docksInstance.player, "Bastian Roe") is False


def test_manageFleet_dismiss_named_worker():
    # prepare - two villagers aboard; "3" = Dismiss, "1" = the first of them
    docksInstance = createDocks()
    boats.addBoat(docksInstance.player, 1)
    boats.hireWorker(docksInstance.player, "Marta Kell")
    boats.hireWorker(docksInstance.player, "Owen Brackish")
    docksInstance.userInterface.showOptions = MagicMock(
        side_effect=fleetChooser("Dismiss a Worker", "Marta Kell")
    )

    # call
    docksInstance.manageFleet()

    # check - gone from the roster and off the boat
    assert docksInstance.player.hiredWorkers == ["Owen Brackish"]
    assert docksInstance.player.boats[0]["crew"] == ["Owen Brackish"]
    assert docksInstance.player.workers == 1


def test_manageFleet_assign_crew_between_boats():
    # prepare - a hand on the first boat, and a second boat with room
    docksInstance = createDocks()
    first = boats.addBoat(docksInstance.player, 1, name="Salty Dawn")
    second = boats.addBoat(docksInstance.player, 1, boats.ROLE_PIRACY, "Marauder")
    boats.hireWorker(docksInstance.player, "Marta Kell")
    assert first["crew"] == ["Marta Kell"]

    # call - Assign (4) -> Salty Dawn (1) -> take Marta off (1) -> Back (2)
    docksInstance.userInterface.showOptions = MagicMock(
        side_effect=fleetChooser("Assign Crew", "Salty Dawn", "Take Marta Kell off")
    )
    docksInstance.manageFleet()

    # check - she's ashore, still hired, and available for the other boat
    assert first["crew"] == []
    assert second["crew"] == []
    assert boats.unassignedNames(docksInstance.player) == ["Marta Kell"]


def test_manageFleet_change_role():
    # prepare - one fishing boat; "4" = Change a Boat's Role with no crew hired
    docksInstance = createDocks()
    boats.addBoat(docksInstance.player, 2)
    docksInstance.userInterface.showOptions = MagicMock(
        side_effect=fleetChooser("Change a Boat's Role", "Unnamed", "Piracy")
    )

    # call
    docksInstance.manageFleet()

    # check - dedicated to piracy, which is third in ROLE_ORDER
    assert docksInstance.player.boats[0]["role"] == boats.ROLE_PIRACY


def test_manageFleet_sell_boat_returns_her_crew_to_the_payroll():
    # prepare - a Trawler with a hand aboard
    docksInstance = createDocks()
    boats.addBoat(docksInstance.player, 2)
    boats.hireWorker(docksInstance.player, "Marta Kell")
    docksInstance.player.money = 0
    docksInstance.userInterface.showOptions = MagicMock(
        side_effect=fleetChooser("Unnamed")
    )

    # call
    docksInstance._sellBoat()

    # check - paid out, boat gone, crew ashore but still hired and warned about
    assert docksInstance.player.money == business.tierInfo(2)["resaleValue"]
    assert docksInstance.player.boats == []
    assert docksInstance.player.hiredWorkers == ["Marta Kell"]
    assert "still on the payroll" in docksInstance.currentPrompt.text


def test_manageFleet_upgrade_boat():
    # prepare - a Rowboat and enough for a Trawler
    docksInstance = createDocks()
    boats.addBoat(docksInstance.player, 1)
    docksInstance.player.money = business.tierInfo(2)["cost"]
    docksInstance.userInterface.showOptions = MagicMock(
        side_effect=fleetChooser("Upgrade a Boat", "Unnamed")
    )

    # call
    docksInstance.manageFleet()

    # check
    assert docksInstance.player.boats[0]["tier"] == 2
    assert docksInstance.player.money == 0


def test_manageFleet_upgrade_boat_insufficient_funds():
    # prepare
    docksInstance = createDocks()
    boats.addBoat(docksInstance.player, 1)
    docksInstance.player.money = 0
    docksInstance.userInterface.showOptions = MagicMock(
        side_effect=fleetChooser("Upgrade a Boat", "Unnamed")
    )

    # call
    docksInstance.manageFleet()

    # check
    assert docksInstance.player.boats[0]["tier"] == 1


def test_manageFleet_upgrade_unavailable_at_max_tier():
    # prepare - every boat already at the top of the ladder
    docksInstance = createDocks()
    boats.addBoat(docksInstance.player, len(business.BOAT_TIERS))
    docksInstance.userInterface.showOptions = MagicMock(side_effect=fleetChooser())

    # call - the menu is rendered once, then Back
    docksInstance.manageFleet()

    # check
    assert "Upgrade a Boat" not in fleetMenu(docksInstance)


def test_manageFleet_repair_only_offered_when_something_is_damaged():
    # prepare - a sound fleet
    docksInstance = createDocks()
    boat = boats.addBoat(docksInstance.player, 1)
    docksInstance.userInterface.showOptions = MagicMock(side_effect=fleetChooser())
    docksInstance.manageFleet()

    # check
    assert "Repair a Boat" not in fleetMenu(docksInstance)

    # prepare - knock her about
    boats.damageBoat(boat, 40)
    docksInstance.userInterface.showOptions = MagicMock(side_effect=fleetChooser())
    docksInstance.manageFleet()

    # check
    assert "Repair a Boat" in fleetMenu(docksInstance)


def test_manageFleet_repair_boat():
    # prepare - a damaged boat and the money to fix her
    docksInstance = createDocks()
    boat = boats.addBoat(docksInstance.player, 1)
    boats.damageBoat(boat, 40)
    cost = boats.repairCost(boat)
    docksInstance.player.money = cost
    docksInstance.userInterface.showOptions = MagicMock(
        side_effect=fleetChooser("Repair a Boat", "Unnamed")
    )

    # call
    docksInstance.manageFleet()

    # check
    assert boat["damage"] == 0
    assert docksInstance.player.money == 0


def test_manageFleet_repair_refused_when_too_poor():
    # prepare
    docksInstance = createDocks()
    boat = boats.addBoat(docksInstance.player, 1)
    boats.damageBoat(boat, 40)
    docksInstance.player.money = 1
    docksInstance.userInterface.showOptions = MagicMock(
        side_effect=fleetChooser("Unnamed")
    )

    # call
    docksInstance._repairBoat()

    # check - still damaged, and told what it would cost
    assert boat["damage"] == 40
    assert "$%d" % boats.repairCost(boat) in docksInstance.currentPrompt.text


def test_manageFleet_rename_business():
    # prepare
    docksInstance = createDocks()
    boats.addBoat(docksInstance.player, 1)
    docksInstance.userInterface.showOptions = MagicMock(
        side_effect=fleetChooser("Rename Business")
    )
    docksInstance.userInterface.promptForText = MagicMock(
        return_value="Salty Dawn Fisheries"
    )

    # call
    docksInstance.manageFleet()

    # check
    assert docksInstance.player.businessName == "Salty Dawn Fisheries"


def test_manageFleet_rename_business_blank_keeps_previous_name():
    # prepare
    docksInstance = createDocks()
    boats.addBoat(docksInstance.player, 1)
    docksInstance.player.businessName = "Salty Dawn Fisheries"
    docksInstance.userInterface.showOptions = MagicMock(
        side_effect=fleetChooser("Rename Business")
    )
    docksInstance.userInterface.promptForText = MagicMock(return_value="   ")

    # call
    docksInstance.manageFleet()

    # check
    assert docksInstance.player.businessName == "Salty Dawn Fisheries"


def test_manageFleet_rename_boat():
    # prepare
    docksInstance = createDocks()
    boats.addBoat(docksInstance.player, 1)
    docksInstance.userInterface.showOptions = MagicMock(
        side_effect=fleetChooser("Rename a Boat", "Unnamed")
    )
    docksInstance.userInterface.promptForText = MagicMock(return_value="Marauder")

    # call
    docksInstance.manageFleet()

    # check
    assert docksInstance.player.boats[0]["name"] == "Marauder"


def test_run_talk_to_crew_option_appears_once_hired():
    # prepare - no crew yet
    docksInstance = createDocks()
    docksInstance.userInterface.showOptions = MagicMock(return_value="1")
    docksInstance.player.energy = 0

    # call
    docksInstance.run()

    # check - nobody to talk to, so the option is absent
    assert (
        "Talk to Your Crew"
        not in docksInstance.userInterface.showOptions.call_args[0][1]
    )

    # prepare - hire someone
    boats.addBoat(docksInstance.player, 1)
    boats.hireWorker(docksInstance.player, "Marta Kell")

    # call
    docksInstance.run()

    # check - the option is now on the docks menu
    assert (
        "Talk to Your Crew" in docksInstance.userInterface.showOptions.call_args[0][1]
    )


def test_run_talk_to_crew_action():
    # prepare
    docksInstance = createDocks()
    boats.addBoat(docksInstance.player, 1)
    boats.hireWorker(docksInstance.player, "Marta Kell")
    docksInstance.userInterface.showOptions = MagicMock(return_value="8")
    docksInstance.talkToCrew = MagicMock()

    # call
    result = docksInstance.run()

    # check
    docksInstance.talkToCrew.assert_called_once()
    assert result == LocationType.DOCKS


def test_talkToCrew_opens_the_chosen_crew_member():
    # prepare - two hands aboard; pick the second, then back out
    docksInstance = createDocks()
    boats.addBoat(docksInstance.player, 1)
    boats.hireWorker(docksInstance.player, "Marta Kell")
    boats.hireWorker(docksInstance.player, "Owen Brackish")
    docksInstance.userInterface.showOptions = MagicMock(side_effect=["2", "3"])
    docksInstance.userInterface.showInteractiveDialogue = MagicMock()

    # call
    docksInstance.talkToCrew()

    # check
    docksInstance.userInterface.showInteractiveDialogue.assert_called_once()
    npc = docksInstance.userInterface.showInteractiveDialogue.call_args[0][0]
    assert npc.name == "Owen Brackish"
    assert docksInstance.currentPrompt.text == "What would you like to do?"


def test_talkToCrew_back_talks_to_nobody():
    # prepare - one hand aboard, so "2" is Back
    docksInstance = createDocks()
    boats.addBoat(docksInstance.player, 1)
    boats.hireWorker(docksInstance.player, "Marta Kell")
    docksInstance.userInterface.showOptions = MagicMock(return_value="2")
    docksInstance.userInterface.showInteractiveDialogue = MagicMock()

    # call
    docksInstance.talkToCrew()

    # check
    docksInstance.userInterface.showInteractiveDialogue.assert_not_called()


def test_sam_crew_question_is_locked_until_someone_is_hired():
    # prepare
    docksInstance = createDocks()

    # call
    questions = [
        option["question"] for option in docksInstance.npc.get_dialogue_options()
    ]

    # check
    assert "What do you make of the crew I hired?" not in questions

    # prepare - hire a villager
    boats.addBoat(docksInstance.player, 1)
    boats.hireWorker(docksInstance.player, "Marta Kell")

    # call
    options = docksInstance.npc.get_dialogue_options()
    questions = [option["question"] for option in options]

    # check - Sam now has something to say, and names the hand and their work
    assert "What do you make of the crew I hired?" in questions
    index = questions.index("What do you make of the crew I hired?")
    response = docksInstance.npc.get_dialogue_response(index)
    assert "Marta Kell" in response
    assert villagers.getVillager("Marta Kell")["specialty"] in response


def test_sam_crew_question_mentions_unnamed_hands():
    # prepare - one named villager plus two hands from a legacy save
    docksInstance = createDocks()
    boats.addBoat(docksInstance.player, 1)
    docksInstance.player.workers = 2
    boats.hireWorker(docksInstance.player, "Marta Kell")

    # call
    response = docksInstance._crewDialogue()

    # check
    assert "Marta Kell" in response
    assert "2 hands" in response


def test_fleetStatus_lists_every_boat_and_who_is_on_her():
    # prepare
    docksInstance = createDocks()
    boats.addBoat(docksInstance.player, 1)
    boats.hireWorker(docksInstance.player, "Marta Kell")
    boats.hireWorker(docksInstance.player, "Owen Brackish")

    # call
    status = docksInstance._fleetStatus()

    # check - the boat, her role, and her crew are all on the screen
    assert "Fishing" in status
    assert "crew 2/" in status
    assert "Marta Kell" in docksInstance.player.boats[0]["crew"]
    assert "Owen Brackish" in docksInstance.player.boats[0]["crew"]


def test_hireVillager_with_nobody_left_to_hire():
    # prepare - the whole roster is already aboard
    docksInstance = createDocks()
    boats.addBoat(docksInstance.player, 1)
    docksInstance.player.hiredWorkers = [v["name"] for v in villagers.VILLAGERS]
    docksInstance.player.workers = len(villagers.VILLAGERS)
    docksInstance.userInterface.showOptions = MagicMock()

    # call
    docksInstance._hireVillager()

    # check - the player is told why, rather than shown an empty menu
    docksInstance.userInterface.showOptions.assert_not_called()
    assert "looking for a berth" in docksInstance.currentPrompt.text


def test_sam_crew_dialogue_handles_a_name_off_the_roster():
    # prepare - a crew member whose name isn't in the villager roster, as a
    # hand carried over from an older save could be
    docksInstance = createDocks()
    boats.addBoat(docksInstance.player, 1)
    docksInstance.player.workers = 1
    docksInstance.player.hiredWorkers = ["Some Old Hand"]

    # call
    response = docksInstance._crewDialogue()

    # check - they're still named, just without a specialty to describe
    assert "Some Old Hand" in response


def test_hireVillager_refuses_when_every_berth_is_taken():
    # prepare - a legacy save whose unnamed hands fill the Rowboat, so the
    # roster still has names free but the boat has no room
    docksInstance = createDocks()
    boats.addBoat(docksInstance.player, 1)
    docksInstance.player.workers = business.tierInfo(1)["maxWorkers"]
    docksInstance.userInterface.showOptions = MagicMock(return_value="1")

    # call
    docksInstance._hireVillager()

    # check - nobody is added past the boat's capacity
    assert docksInstance.player.workers == business.tierInfo(1)["maxWorkers"]
    assert docksInstance.player.hiredWorkers == []
    assert "no free berth in the fleet" in docksInstance.currentPrompt.text


def test_dismissWorker_back_dismisses_nobody():
    # prepare - one named hand aboard, so "2" is Back
    docksInstance = createDocks()
    boats.addBoat(docksInstance.player, 1)
    boats.hireWorker(docksInstance.player, "Marta Kell")
    docksInstance.userInterface.showOptions = MagicMock(return_value="2")

    # call
    docksInstance._dismissWorker()

    # check
    assert docksInstance.player.workers == 1
    assert docksInstance.player.hiredWorkers == ["Marta Kell"]


def createExportingDocks(tier=2, money=1000, fishCount=100):
    """Docks with a boat big enough to export and a hold worth shipping."""
    docksInstance = createDocks()
    boats.addBoat(docksInstance.player, tier)
    docksInstance.player.money = money
    if fishCount:
        docksInstance.player.addFish("Bass", fishCount)
    return docksInstance


def test_run_export_option_appears_only_with_a_big_enough_boat():
    # prepare - a Rowboat, which can't make the crossing
    docksInstance = createExportingDocks(tier=1)
    docksInstance.userInterface.showOptions = MagicMock(return_value="3")

    # call
    docksInstance.run()

    # check
    options = docksInstance.userInterface.showOptions.call_args[0][1]
    assert "Export Fish to Other Villages" not in options

    # prepare - upgrade to a Trawler
    boats.addBoat(docksInstance.player, 2)

    # call
    docksInstance.run()

    # check
    options = docksInstance.userInterface.showOptions.call_args[0][1]
    assert "Export Fish to Other Villages" in options


def test_run_export_action():
    # prepare - the export entry is last, after Manage Boat & Crew
    docksInstance = createExportingDocks()
    docksInstance.userInterface.showOptions = MagicMock(return_value="8")
    docksInstance.exportFish = MagicMock()

    # call
    result = docksInstance.run()

    # check
    docksInstance.exportFish.assert_called_once()
    assert result == LocationType.DOCKS


def test_run_menu_positions_hold_when_both_extras_are_present():
    # prepare - a crew to talk to *and* a boat that can export, so both
    # conditional entries are on the menu at once
    docksInstance = createExportingDocks()
    boats.hireWorker(docksInstance.player, "Marta Kell")
    docksInstance.userInterface.showOptions = MagicMock(return_value="9")
    docksInstance.exportFish = MagicMock()
    docksInstance.talkToCrew = MagicMock()

    # call
    docksInstance.run()

    # check - export sits after the crew entry, and each action still lines up
    # with its own option rather than the one beside it
    options = docksInstance.userInterface.showOptions.call_args[0][1]
    assert options[7] == "Talk to Your Crew"
    assert options[8] == "Export Fish to Other Villages"
    docksInstance.exportFish.assert_called_once()
    docksInstance.talkToCrew.assert_not_called()


def test_run_crew_action_still_fires_without_the_export_entry():
    # prepare - a crew but only a Rowboat, so "8" must still mean the crew
    docksInstance = createDocks()
    boats.addBoat(docksInstance.player, 1)
    boats.hireWorker(docksInstance.player, "Marta Kell")
    docksInstance.userInterface.showOptions = MagicMock(return_value="8")
    docksInstance.talkToCrew = MagicMock()

    # call
    docksInstance.run()

    # check
    docksInstance.talkToCrew.assert_called_once()


def test_exportFish_ships_to_the_chosen_market():
    # prepare - pick the first market
    docksInstance = createExportingDocks()
    docksInstance.userInterface.showOptions = MagicMock(return_value="1")
    startingDay = docksInstance.timeService.day

    # call
    docksInstance.exportFish()

    # check - the hold sold and the round trip cost a day
    market = export.EXPORT_MARKETS[0]
    assert docksInstance.player.fishCount == 0
    assert docksInstance.timeService.day == startingDay + 1
    assert docksInstance.stats.totalFishExported == 100
    assert market["name"] in docksInstance.currentPrompt.text


def test_exportFish_reports_fish_left_in_the_hold():
    # prepare - more fish than a Trawler can carry in one run
    capacity = business.tierInfo(2)["exportCapacity"]
    docksInstance = createExportingDocks(fishCount=capacity + 40)
    docksInstance.userInterface.showOptions = MagicMock(return_value="1")

    # call
    docksInstance.exportFish()

    # check
    assert docksInstance.player.fishCount == 40
    assert "40 fish are still in the hold" in docksInstance.currentPrompt.text


def test_exportFish_back_ships_nothing():
    # prepare - "Back" is the entry after the reachable markets
    docksInstance = createExportingDocks()
    backIndex = str(len(export.availableMarkets(docksInstance.player)) + 1)
    docksInstance.userInterface.showOptions = MagicMock(return_value=backIndex)
    startingDay = docksInstance.timeService.day

    # call
    docksInstance.exportFish()

    # check - no fish sold, no day lost
    assert docksInstance.player.fishCount == 100
    assert docksInstance.timeService.day == startingDay
    assert docksInstance.currentPrompt.text == "What would you like to do?"


def test_exportFish_stays_open_when_the_freight_is_unaffordable():
    # prepare - choose the pricier market with no money, then back out
    docksInstance = createExportingDocks(money=0)
    backIndex = str(len(export.availableMarkets(docksInstance.player)) + 1)
    docksInstance.userInterface.showOptions = MagicMock(side_effect=["2", backIndex])
    startingDay = docksInstance.timeService.day

    # call
    docksInstance.exportFish()

    # check - the player is told what went wrong and gets another choice
    assert docksInstance.player.fishCount == 100
    assert docksInstance.timeService.day == startingDay
    assert docksInstance.userInterface.showOptions.call_count == 2


def test_exportRefusal_explains_unaffordable_freight():
    # prepare
    docksInstance = createExportingDocks(money=5)
    market = export.EXPORT_MARKETS[1]

    # call
    docksInstance._runExport(market)

    # check - names the cost, the shortfall, and a way out
    text = docksInstance.currentPrompt.text
    assert market["name"] in text
    assert "$%d" % market["shippingCost"] in text
    assert "$5.00" in text
    assert "shop" in text


def test_exportRefusal_explains_an_empty_hold():
    # prepare
    docksInstance = createExportingDocks(fishCount=0)

    # call
    docksInstance._runExport(export.EXPORT_MARKETS[0])

    # check
    assert "no fish to ship" in docksInstance.currentPrompt.text


def test_exportRefusal_explains_a_boat_that_is_too_small():
    # prepare - a Trawler aimed at the tier 3 market
    docksInstance = createExportingDocks(tier=2)
    farMarket = next(m for m in export.EXPORT_MARKETS if m["minBoatTier"] == 3)

    # call
    docksInstance._runExport(farMarket)

    # check - says which boat would be needed
    text = docksInstance.currentPrompt.text
    assert farMarket["name"] in text
    assert business.tierInfo(farMarket["minBoatTier"])["name"] in text


def test_exportStatus_describes_the_load():
    # prepare - more fish than the hold takes
    capacity = business.tierInfo(2)["exportCapacity"]
    docksInstance = createExportingDocks(fishCount=capacity + 10)

    # call
    status = docksInstance._exportStatus()

    # check
    assert "can carry %d fish per run" % capacity in status
    assert "leaving 10 for the next run" in status


def test_exportStatus_when_the_hold_is_empty():
    # prepare
    docksInstance = createExportingDocks(fishCount=0)

    # call
    status = docksInstance._exportStatus()

    # check
    assert "hold is empty" in status


def test_marketOption_shows_a_loss_as_a_loss():
    # prepare - one cheap fish against the priciest freight
    docksInstance = createExportingDocks(tier=3, fishCount=0)
    docksInstance.player.addFish("Minnow", 1)
    farMarket = max(export.EXPORT_MARKETS, key=lambda m: m["shippingCost"])

    # call
    line = docksInstance._marketOption(
        farMarket, export.buildCargo(docksInstance.player)
    )

    # check - reads as a loss rather than a negative "clear" figure
    assert "loss on this load" in line
    assert "$-" not in line


def test_exportFish_reports_an_eviction_from_the_day_that_passed():
    # prepare - renting, but broke enough that the day's rent can't be paid
    docksInstance = createExportingDocks()
    docksInstance.player.homeTier = 1

    def evictOnNewDay():
        docksInstance.player.homeTier = 0
        return {"evicted": True}

    docksInstance.timeService.increaseDay = MagicMock(side_effect=evictOnNewDay)
    docksInstance.userInterface.showOptions = MagicMock(return_value="1")

    # call
    docksInstance.exportFish()

    # check - the trip report mentions what happened while the player was away
    assert housing.EVICTION_MESSAGE in docksInstance.currentPrompt.text


def createSailingDocks(role=None, tier=3, crew=2, damage=0, money=5000):
    """Docks with a crewed boat the player could take the helm of."""
    import src.business.boats as _boats

    docksInstance = createDocks()
    docksInstance.player.money = money
    boat = boats.addBoat(
        docksInstance.player, tier, role or _boats.ROLE_PIRACY, "Marauder"
    )
    for villager in villagers.VILLAGERS[:crew]:
        boats.hireWorker(docksInstance.player, villager["name"])
    if damage:
        boats.damageBoat(boat, damage)
    return docksInstance, boat


def voyageChooser(*wanted):
    """Drive the voyage menus by label prefix, then Back. Same idea as
    fleetChooser - the screens grow, the tests shouldn't care."""
    remaining = list(wanted)

    def choose(descriptor, options):
        if remaining:
            prefix = remaining.pop(0)
            for index, option in enumerate(options, start=1):
                if option.startswith(prefix):
                    return str(index)
        return str(len(options))

    return choose


def test_run_take_the_helm_appears_only_with_a_boat_that_can_sail():
    # prepare - a boat with nobody aboard can't be taken out
    docksInstance = createDocks()
    boats.addBoat(docksInstance.player, 2, boats.ROLE_PIRACY)
    docksInstance.userInterface.showOptions = MagicMock(return_value="3")
    docksInstance.run()

    # check
    assert (
        "Take the Helm" not in docksInstance.userInterface.showOptions.call_args[0][1]
    )

    # prepare - crew her
    boats.hireWorker(docksInstance.player, "Marta Kell")
    docksInstance.run()

    # check
    assert "Take the Helm" in docksInstance.userInterface.showOptions.call_args[0][1]


def test_run_take_the_helm_action():
    # prepare - find the entry by label, since crew/export entries also appear
    docksInstance, _ = createSailingDocks()
    docksInstance.userInterface.showOptions = MagicMock(return_value="1")
    docksInstance.fish = MagicMock()
    docksInstance.run()
    menu = docksInstance.userInterface.showOptions.call_args[0][1]

    docksInstance.userInterface.showOptions = MagicMock(
        return_value=str(menu.index("Take the Helm") + 1)
    )
    docksInstance.takeTheHelm = MagicMock()

    # call
    result = docksInstance.run()

    # check
    docksInstance.takeTheHelm.assert_called_once()
    assert result == LocationType.DOCKS


def test_readyToSail_excludes_wrecks_crewless_boats_and_boats_already_out():
    # prepare - one of each problem, plus one that's fine
    docksInstance, ready = createSailingDocks()
    crewless = boats.addBoat(docksInstance.player, 2, boats.ROLE_HAULING, "Empty")
    wrecked = boats.addBoat(docksInstance.player, 2, boats.ROLE_HAULING, "Leaky Sue")
    away = boats.addBoat(docksInstance.player, 2, boats.ROLE_HAULING, "Gone")
    boats.hireWorker(docksInstance.player, "Piety Shaw")
    boats.hireWorker(docksInstance.player, "Nell Tarrow")
    boats.unassignCrew(docksInstance.player, ready["id"], "Piety Shaw")
    boats.assignCrew(docksInstance.player, wrecked["id"], "Piety Shaw")
    boats.unassignCrew(docksInstance.player, ready["id"], "Nell Tarrow")
    boats.assignCrew(docksInstance.player, away["id"], "Nell Tarrow")
    boats.damageBoat(wrecked, boats.UNSEAWORTHY_DAMAGE)
    away["atSea"] = True

    # call
    sailable = docksInstance.readyToSail()

    # check
    assert ready in sailable
    for boat in (crewless, wrecked, away):
        assert boat not in sailable
        assert docksInstance._cannotSailReason(boat)


def test_takeTheHelm_back_sails_nobody():
    # prepare
    docksInstance, boat = createSailingDocks()
    docksInstance.userInterface.showOptions = MagicMock(side_effect=voyageChooser())
    startingDay = docksInstance.timeService.day

    # call
    docksInstance.takeTheHelm()

    # check
    assert boats.isAtSea(boat) is False
    assert docksInstance.timeService.day == startingDay


def test_a_voyage_sails_every_leg_costs_days_and_comes_home():
    # prepare - the shortest plan, full stores. Both dice are pinned: randint
    # to 0 so nothing damages the hull, and random high so the starvation roll
    # never lands - events that eat stores can otherwise empty a full load and
    # starve a small crew to nothing on the last leg, which founders her (see
    # the foundering test below).
    docksInstance, boat = createSailingDocks()
    plan = adventures.VOYAGE_PLANS[0]
    docksInstance.userInterface.showOptions = MagicMock(
        side_effect=voyageChooser("Marauder", "A short run", "Full stores")
    )
    docksInstance.userInterface.showDialogue = MagicMock()
    startingDay = docksInstance.timeService.day

    # call
    with patch("src.business.adventures.random.randint", return_value=0):
        with patch("src.business.adventures.random.random", return_value=0.99):
            docksInstance.takeTheHelm()

    # check - a day per leg, and she's back in the fleet
    assert docksInstance.timeService.day == startingDay + plan["legs"]
    assert boats.isAtSea(boat) is False
    assert docksInstance.stats.totalVoyagesCaptained == 1
    assert docksInstance.stats.totalVoyagesFoundered == 0
    # every leg showed its outcome, plus the homecoming
    assert docksInstance.userInterface.showDialogue.call_count == plan["legs"] + 1


def test_a_voyage_that_founders_ends_early():
    # prepare - a boat one knock from the bottom, and every event doing real
    # damage
    docksInstance, boat = createSailingDocks(damage=boats.MAX_DAMAGE - 5)
    boat["damage"] = boats.MAX_DAMAGE - 5  # damaged but still just seaworthy
    boats.repairBoat(docksInstance.player, boat["id"])
    boats.damageBoat(boat, boats.UNSEAWORTHY_DAMAGE - 1)
    plan = adventures.VOYAGE_PLANS[2]
    docksInstance.userInterface.showOptions = MagicMock(
        side_effect=voyageChooser("Marauder", "The far water", "Full stores")
    )
    docksInstance.userInterface.showDialogue = MagicMock()
    startingDay = docksInstance.timeService.day

    # call - every damage roll at its worst
    with patch("src.business.adventures.random.randint", return_value=99):
        with patch("src.business.adventures.random.random", return_value=0.0):
            docksInstance.takeTheHelm()

    # check - she came home early with nothing, but she came home
    assert docksInstance.timeService.day < startingDay + plan["legs"]
    assert docksInstance.stats.totalVoyagesFoundered == 1
    assert boat in docksInstance.player.boats
    assert boats.isAtSea(boat) is False
    assert boat["damage"] > boats.UNSEAWORTHY_DAMAGE


def test_a_voyage_pays_out_what_it_brought_home():
    # prepare - both dice pinned so the voyage runs its full length; the
    # payout is then the legs' own earnings
    docksInstance, boat = createSailingDocks(role=boats.ROLE_PIRACY)
    docksInstance.userInterface.showOptions = MagicMock(
        side_effect=voyageChooser("Marauder", "A short run", "Full stores")
    )
    docksInstance.userInterface.showDialogue = MagicMock()

    # call
    with patch("src.business.adventures.random.randint", return_value=0):
        with patch("src.business.adventures.random.random", return_value=0.99):
            docksInstance.takeTheHelm()

    # check
    assert docksInstance.stats.totalMoneyFromVoyages > 0
    assert docksInstance.stats.totalVoyagesCaptained == 1


def test_provisioning_is_refused_when_the_stores_cannot_be_paid_for():
    # prepare - no money for even half rations
    docksInstance, boat = createSailingDocks(money=1)
    docksInstance.userInterface.showOptions = MagicMock(
        side_effect=voyageChooser("Marauder", "A short run", "Full stores")
    )

    # call
    docksInstance.takeTheHelm()

    # check - she never left, and the message says what it would cost
    assert boats.isAtSea(boat) is False
    assert "stores" in docksInstance.currentPrompt.text
    assert "$1.00" in docksInstance.currentPrompt.text


def test_voyageReport_reads_as_a_homecoming():
    # prepare
    docksInstance, _ = createSailingDocks()

    # call
    report = docksInstance._voyageReport(
        {
            "boat": "Marauder",
            "foundered": False,
            "legsSailed": 7,
            "legs": 7,
            "money": 2600,
            "fish": 40,
            "crewLost": [],
            "hullDamage": 26,
        }
    )

    # check
    assert "Marauder comes home" in report
    assert "$2600" in report
    assert "40 fish" in report
    assert "all hands accounted for" in report


def test_voyageReport_reads_as_a_disaster_when_she_founders():
    # prepare
    docksInstance, _ = createSailingDocks()

    # call
    report = docksInstance._voyageReport(
        {
            "boat": "Marauder",
            "foundered": True,
            "legsSailed": 3,
            "legs": 11,
            "money": 0,
            "fish": 0,
            "crewLost": ["Owen Brackish"],
            "hullDamage": 92,
        }
    )

    # check - the cargo is gone, the crew member is named, the boat is still hers
    assert "hull gives" in report
    assert "lost overboard" in report
    assert "Owen Brackish did not come back" in report


def test_exportCapacity_prefers_a_hauling_boat():
    # prepare - the same hull, fishing then hauling
    docksInstance = createDocks()
    boat = boats.addBoat(docksInstance.player, 2, boats.ROLE_FISHING)
    asFishing = export.exportCapacity(docksInstance.player)

    # call
    boats.setRole(docksInstance.player, boat["id"], boats.ROLE_HAULING)

    # check - the cargo fit-out is the passive half of dedicating her to hauling
    assert export.exportCapacity(docksInstance.player) > asFishing
