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

    # check - the home tier and lifetime rental income are always shown, even
    # for a fresh player at the base tier
    shownText = homeInstance.userInterface.showDialogue.call_args[0][0]
    assert "Home: Driftwood Shack" in shownText
    assert "Lifetime Rental Income" in shownText


def test_manageHome_upgrade_when_affordable():
    # prepare
    homeInstance = createHome()
    homeInstance.player.money = 10000
    nextInfo = housing.tierInfo(2)
    homeInstance.userInterface.showOptions = MagicMock(side_effect=["1", "2"])

    # call - upgrade, then back out
    homeInstance.manageHome()

    # check
    assert homeInstance.player.homeTier == 2
    assert homeInstance.player.money == 10000 - nextInfo["cost"]
    assert homeInstance.stats.highestHomeTier == 2


def test_manageHome_upgrade_when_unaffordable():
    # prepare
    homeInstance = createHome()
    homeInstance.player.money = 0
    homeInstance.userInterface.showOptions = MagicMock(side_effect=["1", "2"])

    # call - attempt to upgrade (fails, loop continues), then back out
    homeInstance.manageHome()

    # check - no tier change, no money spent
    assert homeInstance.player.homeTier == 1
    assert homeInstance.player.money == 0


def test_manageHome_at_top_tier_has_no_upgrade_option():
    # prepare - already at the top tier
    homeInstance = createHome()
    homeInstance.player.homeTier = len(housing.HOUSING_TIERS)
    homeInstance.userInterface.showOptions = MagicMock(return_value="1")

    # call - the only option offered is "Back"
    homeInstance.manageHome()

    # check
    optionsShown = homeInstance.userInterface.showOptions.call_args[0][1]
    assert optionsShown == ["Back"]
