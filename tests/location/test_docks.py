from src.location.enum.locationType import LocationType
from src.location import docks
from src.player.player import Player
from src.prompt.prompt import Prompt
from src.stats.stats import Stats
from src.ui.userInterface import UserInterface
from src.world.timeService import TimeService
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

    with patch('src.location.docks.print'), \
         patch('src.location.docks.sys.stdout.flush'), \
         patch('src.location.docks.time.sleep'), \
         patch('src.location.docks.random.randint', return_value=3):

        docksInstance.timeService.increaseTime = MagicMock()

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

    with patch('src.location.docks.print'), \
         patch('src.location.docks.sys.stdout.flush'), \
         patch('src.location.docks.time.sleep'), \
         patch('src.location.docks.random.randint', return_value=3):

        docksInstance.timeService.increaseTime = MagicMock()

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

    with patch('src.location.docks.print'), \
         patch('src.location.docks.sys.stdout.flush'), \
         patch('src.location.docks.time.sleep'), \
         patch('src.location.docks.random.randint', return_value=5):

        docksInstance.timeService.increaseTime = MagicMock()

        # call
        docksInstance.fish()

        # check
        assert docksInstance.player.energy == 5  # Should be 25 - (2 * 10)
        assert (
            docksInstance.timeService.increaseTime.call_count == 2
        )  # Only fished for 2 hours due to energy limit


def test_fish_interactive_success():
    # Test that quick reactions result in successful catches
    docksInstance = createDocks()
    docksInstance.userInterface.lotsOfSpace = MagicMock()
    docksInstance.userInterface.divider = MagicMock()
    # Quick reaction => perfect-quality catch.
    docksInstance.userInterface.timedKeyPress = MagicMock(return_value=0.5)

    with patch('src.location.docks.print'), \
         patch('src.location.docks.sys.stdout.flush'), \
         patch('src.location.docks.time.sleep'), \
         patch('src.location.docks.random.randint', side_effect=[3, 6]):

        docksInstance.timeService.increaseTime = MagicMock()

        # call
        docksInstance.fish()

        # check - with 100% success rate, should get full catch
        assert docksInstance.player.fishCount >= 3  # Should get good catch with all successes
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
            docksInstance.timeService.increaseTime = MagicMock()
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
            docksInstance.timeService.increaseTime = MagicMock()
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
            docksInstance.timeService.increaseTime = MagicMock()
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
    # "1" = Buy a Boat; then in the post-purchase menu "2" = Back
    docksInstance.userInterface.showOptions = MagicMock(side_effect=["1", "2"])

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
    # "1" = Hire; then in the menu with a worker "3" = Back (Hire/Dismiss/Back)
    docksInstance.userInterface.showOptions = MagicMock(side_effect=["1", "3"])

    # call
    docksInstance.manageBusiness()

    # check
    assert docksInstance.player.workers == 1


def test_manageBusiness_dismiss_worker():
    # prepare - own a boat with two workers
    docksInstance = createDocks()
    docksInstance.player.hasBoat = True
    docksInstance.player.workers = 2
    # "2" = Dismiss (Hire/Dismiss/Back); then "3" = Back
    docksInstance.userInterface.showOptions = MagicMock(side_effect=["2", "3"])

    # call
    docksInstance.manageBusiness()

    # check
    assert docksInstance.player.workers == 1
