from src.location.enum.locationType import LocationType
from src.location import home
from src.player.player import Player
from src.prompt.prompt import Prompt
from src.stats.stats import Stats
from src.ui.userInterface import UserInterface
from src.world.timeService import TimeService
from src.achievements import achievements
from src.housing import housing
from unittest.mock import MagicMock


def createHome():
    currentPrompt = Prompt("What would you like to do?")
    player = Player()
    stats = Stats()
    timeService = TimeService(player, stats)
    userInterface = UserInterface(currentPrompt, timeService, player)
    return home.Home(userInterface, currentPrompt, player, stats, timeService)


def test_initialization():
    # call
    home = createHome()

    # check
    assert home.userInterface != None
    assert home.currentPrompt != None
    assert home.player != None
    assert home.stats != None
    assert home.timeService != None


def test_run_sleep_action():
    # prepare
    homeInstance = createHome()
    homeInstance.userInterface.showOptions = MagicMock(return_value="1")
    homeInstance.sleep = MagicMock()

    # call
    nextLocation = homeInstance.run()

    # check
    homeInstance.sleep.assert_called_once()
    assert nextLocation == LocationType.HOME


def test_run_see_stats_action():
    # prepare
    homeInstance = createHome()
    homeInstance.userInterface.showOptions = MagicMock(return_value="2")
    homeInstance.displayStats = MagicMock()

    # call
    nextLocation = homeInstance.run()

    # check
    homeInstance.displayStats.assert_called_once()
    assert nextLocation == LocationType.HOME


def test_run_manage_home_action():
    # prepare
    homeInstance = createHome()
    homeInstance.userInterface.showOptions = MagicMock(return_value="3")
    homeInstance.manageHome = MagicMock()

    # call
    nextLocation = homeInstance.run()

    # check
    homeInstance.manageHome.assert_called_once()
    assert nextLocation == LocationType.HOME


def test_run_go_to_docks_action():
    # prepare
    homeInstance = createHome()
    homeInstance.userInterface.showOptions = MagicMock(return_value="4")

    # call
    nextLocation = homeInstance.run()

    # check
    assert nextLocation == LocationType.DOCKS


def test_run_quit_action():
    # prepare
    homeInstance = createHome()
    homeInstance.userInterface.showOptions = MagicMock(return_value="5")

    # call
    nextLocation = homeInstance.run()

    # check
    assert nextLocation == LocationType.NONE


def test_sleep():
    # prepare
    homeInstance = createHome()
    homeInstance.timeService.increaseDay = MagicMock()
    homeInstance.player.energy = 50  # Set energy to something less than 100

    # call
    homeInstance.sleep()

    # check
    homeInstance.timeService.increaseDay.assert_called_once()
    assert (
        homeInstance.currentPrompt.text
        == "You sleep until the next morning. You feel refreshed!"
    )
    assert homeInstance.player.energy == 100  # Energy should be restored to full


def test_sleep_restores_energy():
    # prepare
    homeInstance = createHome()
    homeInstance.timeService.increaseDay = MagicMock()
    homeInstance.player.energy = 10  # Low energy

    # call
    homeInstance.sleep()

    # check
    assert homeInstance.player.energy == 100


def test_displayStats():
    # prepare
    homeInstance = createHome()
    homeInstance.userInterface.showDialogue = MagicMock()

    # call
    homeInstance.displayStats()

    # check - the stats screen is rendered through the active UI (so any front-end
    # can show it), and includes the stat lines and every milestone
    homeInstance.userInterface.showDialogue.assert_called_once()
    shownText = homeInstance.userInterface.showDialogue.call_args[0][0]
    assert "Total Fish Caught" in shownText
    assert "Milestones:" in shownText
    for milestone in achievements.MILESTONES:
        assert milestone["name"] in shownText


def test_displayStats_includes_home_block():
    # prepare
    homeInstance = createHome()
    homeInstance.userInterface.showDialogue = MagicMock()

    # call
    homeInstance.displayStats()

    # check - the home tier is always shown, even for a fresh player at the
    # base tier; a fresh player owns no investment properties, so that block
    # (and any rental-income line) is omitted
    shownText = homeInstance.userInterface.showDialogue.call_args[0][0]
    assert "Home: Driftwood Shack" in shownText
    assert "Investment Properties" not in shownText


def test_displayStats_includes_investment_block_when_owned():
    # prepare
    homeInstance = createHome()
    homeInstance.player.rentalProperties = [1, 1]
    homeInstance.stats.totalRentalIncome = 30
    homeInstance.userInterface.showDialogue = MagicMock()

    # call
    homeInstance.displayStats()

    # check
    shownText = homeInstance.userInterface.showDialogue.call_args[0][0]
    assert "Investment Properties: 2 owned" in shownText
    assert "Lifetime Rental Income: 30" in shownText


def test_manageHome_move_up_when_affordable():
    # prepare - a trade-up from the free tier 1 costs exactly tier 2's price
    # (tier 1 has no resale value)
    homeInstance = createHome()
    homeInstance.player.money = 10000
    netCost = housing.netCostToMove(homeInstance.player, 2)
    # tier 1 menu is (Move up/Back) = "1"; after moving, tier 2's menu is
    # (Move up/Move down/Back), so "3" backs out
    homeInstance.userInterface.showOptions = MagicMock(side_effect=["1", "3"])

    # call - move up, then back out
    homeInstance.manageHome()

    # check
    assert homeInstance.player.homeTier == 2
    assert homeInstance.player.money == 10000 - netCost
    assert homeInstance.stats.highestHomeTier == 2


def test_manageHome_move_up_when_unaffordable():
    # prepare
    homeInstance = createHome()
    homeInstance.player.money = 0
    # the failed move leaves the tier-1 menu (Move up/Back) unchanged, so "2"
    # backs out both times
    homeInstance.userInterface.showOptions = MagicMock(side_effect=["1", "2"])

    # call - attempt to move up (fails, loop continues), then back out
    homeInstance.manageHome()

    # check - no tier change, no money spent
    assert homeInstance.player.homeTier == 1
    assert homeInstance.player.money == 0


def test_manageHome_move_down_pays_cash_back():
    # prepare - own the Cozy Cottage (tier 2), move back down to the free
    # Driftwood Shack (tier 1)
    homeInstance = createHome()
    homeInstance.player.homeTier = 2
    homeInstance.player.money = 0
    homeInstance.stats.highestHomeTier = 2
    expectedRefund = -housing.netCostToMove(homeInstance.player, 1)
    # tier 2 menu is (Move up/Move down/Back) = "2" moves down; tier 1's menu
    # is (Move up/Back), so "2" backs out
    homeInstance.userInterface.showOptions = MagicMock(side_effect=["2", "2"])

    # call - move down, then back out
    homeInstance.manageHome()

    # check - cash back, and the lifetime "highest tier" stat doesn't regress
    assert homeInstance.player.homeTier == 1
    assert homeInstance.player.money == expectedRefund
    assert homeInstance.stats.highestHomeTier == 2


def test_manageHome_at_base_tier_has_no_move_down_option():
    # prepare - a fresh player at tier 1 has nothing to move down to
    homeInstance = createHome()
    homeInstance.userInterface.showOptions = MagicMock(return_value="2")

    # call - "Back" is the only other option besides "Move to a Cozy Cottage"
    homeInstance.manageHome()

    # check
    optionsShown = homeInstance.userInterface.showOptions.call_args[0][1]
    assert not any("down" in option.lower() for option in optionsShown)


def test_manageHome_at_top_tier_has_no_move_up_option():
    # prepare - already at the top tier
    homeInstance = createHome()
    homeInstance.player.homeTier = len(housing.HOUSING_TIERS)
    homeInstance.userInterface.showOptions = MagicMock(return_value="2")

    # call - "Move down" and "Back" are offered, but no "Move up"
    homeInstance.manageHome()

    # check
    optionsShown = homeInstance.userInterface.showOptions.call_args[0][1]
    assert not any("move to" in option.lower() for option in optionsShown)
    assert any("down" in option.lower() for option in optionsShown)
