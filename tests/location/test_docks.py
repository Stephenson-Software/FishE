from src.location.enum.locationType import LocationType
from src.location import docks
from src.player.player import Player
from src.prompt.prompt import Prompt
from src.stats.stats import Stats
from src.ui.userInterface import UserInterface
from src.world.timeService import TimeService
from src.business import business
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
    docksInstance.player.hasBoat = True

    # check
    response = docksInstance._businessDialogue()
    assert "hire a crew" in response


def test_npc_business_dialogue_staged_by_tier():
    # prepare - one crewed boat per tier
    responses = {}
    for tier in (1, 2, 3):
        docksInstance = createDocks()
        docksInstance.player.hasBoat = True
        docksInstance.player.boatTier = tier
        docksInstance.player.workers = 1
        responses[tier] = docksInstance._businessDialogue()

    # check - each tier gets distinct commentary
    assert len(set(responses.values())) == 3
    assert "Fishing Fleet" in responses[3] or "fleet" in responses[3].lower()


def test_npc_business_dialogue_mentions_business_name():
    # prepare
    docksInstance = createDocks()
    docksInstance.player.hasBoat = True
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
    docksInstance.player.hasBoat = True

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


def test_run_manage_business_action():
    # prepare
    docksInstance = createDocks()
    docksInstance.userInterface.showOptions = MagicMock(return_value="7")
    docksInstance.manageBusiness = MagicMock()

    # call
    nextLocation = docksInstance.run()

    # check
    assert nextLocation == LocationType.DOCKS
    docksInstance.manageBusiness.assert_called_once()


def test_manageBusiness_buy_boat():
    # prepare - enough money for a boat; buy it, then go Back
    from src.business import business

    docksInstance = createDocks()
    docksInstance.player.money = business.BOAT_PRICE + 50
    docksInstance.player.hasBoat = False
    # "1" = Buy a Boat; then in the post-purchase menu
    # (Hire/Sell the Boat/Upgrade/Rename/Back) "5" = Back
    docksInstance.userInterface.showOptions = MagicMock(side_effect=["1", "5"])

    # call
    docksInstance.manageBusiness()

    # check
    assert docksInstance.player.hasBoat is True
    assert docksInstance.player.money == 50


def test_manageBusiness_buy_boat_insufficient_funds():
    # prepare - can't afford a boat
    from src.business import business

    docksInstance = createDocks()
    docksInstance.player.money = business.BOAT_PRICE - 1
    docksInstance.player.hasBoat = False
    docksInstance.userInterface.showOptions = MagicMock(side_effect=["1", "2"])

    # call
    docksInstance.manageBusiness()

    # check - no boat, no money spent
    assert docksInstance.player.hasBoat is False
    assert docksInstance.player.money == business.BOAT_PRICE - 1


def test_manageBusiness_hire_worker():
    # prepare - own a boat, no crew yet
    docksInstance = createDocks()
    docksInstance.player.hasBoat = True
    docksInstance.player.workers = 0
    # "1" = Hire; "1" = the first villager on the roster; then in the menu with
    # a worker (Hire/Dismiss/Sell the Boat/Upgrade/Rename/Back) "6" = Back
    docksInstance.userInterface.showOptions = MagicMock(side_effect=["1", "1", "6"])

    # call
    docksInstance.manageBusiness()

    # check - the hire is a named villager, not an anonymous headcount bump
    assert docksInstance.player.workers == 1
    assert docksInstance.player.hiredWorkers == [villagers.VILLAGERS[0]["name"]]


def test_manageBusiness_hire_worker_back_hires_nobody():
    # prepare - own a boat, no crew yet
    docksInstance = createDocks()
    docksInstance.player.hasBoat = True
    docksInstance.player.workers = 0
    # "1" = Hire; then "Back" out of the villager list (one entry per villager,
    # plus Back); then "5" = Back out of the business menu, which still has no
    # Dismiss entry because nobody was hired
    backIndex = str(len(villagers.VILLAGERS) + 1)
    docksInstance.userInterface.showOptions = MagicMock(
        side_effect=["1", backIndex, "5"]
    )

    # call
    docksInstance.manageBusiness()

    # check
    assert docksInstance.player.workers == 0
    assert docksInstance.player.hiredWorkers == []


def test_manageBusiness_dismiss_named_worker():
    # prepare - own a boat crewed by two named villagers
    docksInstance = createDocks()
    docksInstance.player.hasBoat = True
    docksInstance.player.workers = 2
    docksInstance.player.hiredWorkers = ["Marta Kell", "Owen Brackish"]
    # "2" = Dismiss; "1" = Marta; then "6" = Back
    docksInstance.userInterface.showOptions = MagicMock(side_effect=["2", "1", "6"])

    # call
    docksInstance.manageBusiness()

    # check - the villager the player picked is the one who left
    assert docksInstance.player.workers == 1
    assert docksInstance.player.hiredWorkers == ["Owen Brackish"]


def test_manageBusiness_dismiss_unnamed_worker():
    # prepare - a legacy save's crew: a headcount with no names attached
    docksInstance = createDocks()
    docksInstance.player.hasBoat = True
    docksInstance.player.workers = 2
    # "2" = Dismiss; "1" = the unnamed deckhands entry; then "6" = Back
    docksInstance.userInterface.showOptions = MagicMock(side_effect=["2", "1", "6"])

    # call
    docksInstance.manageBusiness()

    # check
    assert docksInstance.player.workers == 1
    assert docksInstance.player.hiredWorkers == []


def test_manageBusiness_sell_boat():
    # prepare - own a Trawler (tier 2) with a worker
    from src.business import business

    docksInstance = createDocks()
    docksInstance.player.hasBoat = True
    docksInstance.player.boatTier = 2
    docksInstance.player.workers = 1
    docksInstance.player.money = 0
    resaleValue = business.tierInfo(2)["resaleValue"]
    # "3" = Sell the Boat (Hire/Dismiss/Sell the Boat/Upgrade/Rename/Back);
    # after selling, hasBoat is False so the menu shrinks to (Buy a Boat/Back)
    # and "2" = Back
    docksInstance.userInterface.showOptions = MagicMock(side_effect=["3", "2"])

    # call
    docksInstance.manageBusiness()

    # check - refunded, and boat/tier/crew all cleared
    assert docksInstance.player.hasBoat is False
    assert docksInstance.player.boatTier == 0
    assert docksInstance.player.workers == 0
    assert docksInstance.player.money == resaleValue


def test_manageBusiness_hire_worker_increments_lifetime_stat():
    # prepare - own a boat, no crew yet
    docksInstance = createDocks()
    docksInstance.player.hasBoat = True
    docksInstance.player.workers = 0
    docksInstance.userInterface.showOptions = MagicMock(side_effect=["1", "1", "6"])

    # call
    docksInstance.manageBusiness()

    # check - hiring is tracked as a lifetime business stat too
    assert docksInstance.stats.totalWorkersHired == 1


def test_manageBusiness_upgrade_boat():
    # prepare - own a Rowboat (tier 1), enough money to upgrade to a Trawler
    from src.business import business

    docksInstance = createDocks()
    docksInstance.player.hasBoat = True
    docksInstance.player.boatTier = 1
    trawler = business.tierInfo(2)
    docksInstance.player.money = trawler["cost"] + 50
    # 0 workers under tier-1 capacity, so the menu is
    # (Hire/Sell the Boat/Upgrade/Rename/Back): "3" = Upgrade, "5" = Back
    docksInstance.userInterface.showOptions = MagicMock(side_effect=["3", "5"])

    # call
    docksInstance.manageBusiness()

    # check
    assert docksInstance.player.boatTier == 2
    assert docksInstance.player.money == 50


def test_manageBusiness_upgrade_boat_insufficient_funds():
    # prepare - can't afford the next tier
    from src.business import business

    docksInstance = createDocks()
    docksInstance.player.hasBoat = True
    docksInstance.player.boatTier = 1
    docksInstance.player.money = business.tierInfo(2)["cost"] - 1
    # (Hire/Sell the Boat/Upgrade/Rename/Back): "3" = Upgrade, "5" = Back
    docksInstance.userInterface.showOptions = MagicMock(side_effect=["3", "5"])

    # call
    docksInstance.manageBusiness()

    # check - tier and money are unchanged
    assert docksInstance.player.boatTier == 1
    assert docksInstance.player.money == business.tierInfo(2)["cost"] - 1


def test_manageBusiness_upgrade_boat_unavailable_at_max_tier():
    # prepare - already at the highest boat tier
    from src.business import business

    docksInstance = createDocks()
    docksInstance.player.hasBoat = True
    docksInstance.player.boatTier = len(business.BOAT_TIERS)
    # No upgrade offered at max tier, so the menu is
    # (Hire/Sell the Boat/Rename/Back); "4" = Back
    docksInstance.userInterface.showOptions = MagicMock(side_effect=["4"])

    # call
    docksInstance.manageBusiness()

    # check - "Back" (option 3) exits cleanly; no upgrade option was ever shown
    options_shown = docksInstance.userInterface.showOptions.call_args[0][1]
    assert not any("Upgrade" in option for option in options_shown)


def test_manageBusiness_rename():
    # prepare - own a boat, no crew, rename then back
    docksInstance = createDocks()
    docksInstance.player.hasBoat = True
    docksInstance.player.boatTier = 1
    # (Hire/Sell the Boat/Upgrade/Rename/Back): "4" = Rename, "5" = Back
    docksInstance.userInterface.showOptions = MagicMock(side_effect=["4", "5"])
    docksInstance.userInterface.promptForText = MagicMock(
        return_value="  Salty Sea Co.  "
    )

    # call
    docksInstance.manageBusiness()

    # check - the name is trimmed
    assert docksInstance.player.businessName == "Salty Sea Co."


def test_manageBusiness_rename_blank_keeps_previous_name():
    # prepare
    docksInstance = createDocks()
    docksInstance.player.hasBoat = True
    docksInstance.player.boatTier = 1
    docksInstance.player.businessName = "Original Name"
    # (Hire/Sell the Boat/Upgrade/Rename/Back): "4" = Rename, "5" = Back
    docksInstance.userInterface.showOptions = MagicMock(side_effect=["4", "5"])
    docksInstance.userInterface.promptForText = MagicMock(return_value="   ")

    # call
    docksInstance.manageBusiness()

    # check - a blank entry doesn't clear the existing name
    assert docksInstance.player.businessName == "Original Name"


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
    docksInstance.player.hasBoat = True
    business.hireWorker(docksInstance.player, "Marta Kell")

    # call
    docksInstance.run()

    # check - the option is now on the docks menu
    assert (
        "Talk to Your Crew" in docksInstance.userInterface.showOptions.call_args[0][1]
    )


def test_run_talk_to_crew_action():
    # prepare
    docksInstance = createDocks()
    docksInstance.player.hasBoat = True
    business.hireWorker(docksInstance.player, "Marta Kell")
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
    docksInstance.player.hasBoat = True
    business.hireWorker(docksInstance.player, "Marta Kell")
    business.hireWorker(docksInstance.player, "Owen Brackish")
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
    docksInstance.player.hasBoat = True
    business.hireWorker(docksInstance.player, "Marta Kell")
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
    docksInstance.player.hasBoat = True
    business.hireWorker(docksInstance.player, "Marta Kell")

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
    docksInstance.player.hasBoat = True
    docksInstance.player.workers = 2
    business.hireWorker(docksInstance.player, "Marta Kell")

    # call
    response = docksInstance._crewDialogue()

    # check
    assert "Marta Kell" in response
    assert "2 hands" in response


def test_businessStatus_lists_the_crew_by_name():
    # prepare
    docksInstance = createDocks()
    docksInstance.player.hasBoat = True
    business.hireWorker(docksInstance.player, "Marta Kell")
    business.hireWorker(docksInstance.player, "Owen Brackish")

    # call
    status = docksInstance._businessStatus()

    # check
    assert "Aboard: Marta Kell and Owen Brackish." in status


def test_hireVillager_with_nobody_left_to_hire():
    # prepare - the whole roster is already aboard
    docksInstance = createDocks()
    docksInstance.player.hasBoat = True
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
    docksInstance.player.hasBoat = True
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
    docksInstance.player.hasBoat = True
    docksInstance.player.boatTier = 1
    docksInstance.player.workers = business.tierInfo(1)["maxWorkers"]
    docksInstance.userInterface.showOptions = MagicMock(return_value="1")

    # call
    docksInstance._hireVillager()

    # check - nobody is added past the boat's capacity
    assert docksInstance.player.workers == business.tierInfo(1)["maxWorkers"]
    assert docksInstance.player.hiredWorkers == []
    assert (
        docksInstance.currentPrompt.text == "There's no room aboard for another hand."
    )


def test_dismissWorker_back_dismisses_nobody():
    # prepare - one named hand aboard, so "2" is Back
    docksInstance = createDocks()
    docksInstance.player.hasBoat = True
    business.hireWorker(docksInstance.player, "Marta Kell")
    docksInstance.userInterface.showOptions = MagicMock(return_value="2")

    # call
    docksInstance._dismissWorker()

    # check
    assert docksInstance.player.workers == 1
    assert docksInstance.player.hiredWorkers == ["Marta Kell"]


def createExportingDocks(tier=2, money=1000, fishCount=100):
    """Docks with a boat big enough to export and a hold worth shipping."""
    docksInstance = createDocks()
    docksInstance.player.hasBoat = True
    docksInstance.player.boatTier = tier
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
    docksInstance.player.boatTier = 2

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
    business.hireWorker(docksInstance.player, "Marta Kell")
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
    docksInstance.player.hasBoat = True
    business.hireWorker(docksInstance.player, "Marta Kell")
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
