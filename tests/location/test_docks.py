from src.location.enum.locationType import LocationType
from src.location import docks
from src.player.player import Player
from src.prompt.prompt import Prompt
from src.stats.stats import Stats
from src.ui.userInterface import UserInterface
from src.world.timeService import TimeService
from src.housing import housing
from unittest.mock import MagicMock, patch


def createDocks():
    currentPrompt = Prompt("What would you like to do?")
    player = Player()
    stats = Stats()
    timeService = TimeService(player, stats)
    userInterface = UserInterface(currentPrompt, timeService, player)
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
    docksInstance.userInterface.lotsOfSpace = MagicMock()
    docksInstance.userInterface.divider = MagicMock()
    # The active UI captures and times the reaction; mock a quick (perfect) one.
    docksInstance.userInterface.timedKeyPress = MagicMock(return_value=0.5)

    with patch("src.location.docks.print"), patch(
        "src.location.docks.sys.stdout.flush"
    ), patch("src.location.docks.time.sleep"), patch(
        "src.location.docks.random.randint", return_value=3
    ):
        docksInstance.timeService.increaseTime = MagicMock(
            return_value={"evicted": False}
        )

        # call
        docksInstance.fish()

        # check
        docksInstance.userInterface.lotsOfSpace.assert_called_once()
        docksInstance.userInterface.divider.assert_called_once()
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

    with patch("src.location.docks.print"), patch(
        "src.location.docks.sys.stdout.flush"
    ), patch("src.location.docks.time.sleep"), patch(
        "src.location.docks.random.randint", return_value=3
    ):
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

    with patch("src.location.docks.print"), patch(
        "src.location.docks.sys.stdout.flush"
    ), patch("src.location.docks.time.sleep"), patch(
        "src.location.docks.random.randint", return_value=5
    ):
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

    with patch("src.location.docks.print"), patch(
        "src.location.docks.sys.stdout.flush"
    ), patch("src.location.docks.time.sleep"), patch(
        "src.location.docks.random.randint", side_effect=[3, 6]
    ):
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

    with patch("src.location.docks.print"), patch(
        "src.location.docks.sys.stdout.flush"
    ), patch("src.location.docks.time.sleep"), patch(
        "src.location.docks.random.randint", side_effect=[3, 6]
    ):
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

        with patch("src.location.docks.print"), patch(
            "src.location.docks.sys.stdout.flush"
        ), patch("src.location.docks.time.sleep"), patch(
            "src.location.docks.random.randint", side_effect=[3, 10]
        ):
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
        with patch("src.location.docks.print"), patch(
            "src.location.docks.sys.stdout.flush"
        ), patch("src.location.docks.time.sleep"), patch(
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

    with patch("src.location.docks.print"), patch(
        "src.location.docks.sys.stdout.flush"
    ), patch("src.location.docks.time.sleep"), patch(
        "src.location.docks.random.randint", side_effect=[3, 6]
    ):
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
        with patch("src.location.docks.print"), patch(
            "src.location.docks.sys.stdout.flush"
        ), patch("src.location.docks.time.sleep"), patch(
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
        with patch("src.location.docks.print"), patch(
            "src.location.docks.sys.stdout.flush"
        ), patch("src.location.docks.time.sleep"), patch(
            "src.location.docks.random.randint", side_effect=[5, 10]
        ):
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
    # "1" = Hire; then in the menu with a worker
    # (Hire/Dismiss/Sell the Boat/Upgrade/Rename/Back) "6" = Back
    docksInstance.userInterface.showOptions = MagicMock(side_effect=["1", "6"])

    # call
    docksInstance.manageBusiness()

    # check
    assert docksInstance.player.workers == 1


def test_manageBusiness_dismiss_worker():
    # prepare - own a boat with two workers
    docksInstance = createDocks()
    docksInstance.player.hasBoat = True
    docksInstance.player.workers = 2
    # "2" = Dismiss (Hire/Dismiss/Sell the Boat/Upgrade/Rename/Back); then "6" = Back
    docksInstance.userInterface.showOptions = MagicMock(side_effect=["2", "6"])

    # call
    docksInstance.manageBusiness()

    # check
    assert docksInstance.player.workers == 1


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
    docksInstance.userInterface.showOptions = MagicMock(side_effect=["1", "6"])

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
