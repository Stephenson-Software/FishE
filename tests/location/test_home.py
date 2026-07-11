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


def test_homeDescriptor_reflects_housing_status():
    # prepare
    homeInstance = createHome()

    # check - homeless, renting, and owned each get distinct flavor text
    assert "nowhere to stay" in homeInstance._homeDescriptor()

    homeInstance.player.homeTier = 1
    assert "rented room" in homeInstance._homeDescriptor()

    homeInstance.player.homeTier = 2
    assert "at home" in homeInstance._homeDescriptor()


def test_sleep_restores_energy_to_current_tiers_cap():
    # prepare - a fresh (homeless) player has a low energy cap
    homeInstance = createHome()
    homeInstance.timeService.increaseDay = MagicMock(return_value={"evicted": False})
    homeInstance.player.energy = 10

    # call
    homeInstance.sleep()

    # check
    homeInstance.timeService.increaseDay.assert_called_once()
    assert (
        homeInstance.currentPrompt.text
        == "You sleep until the next morning. You feel refreshed!"
    )
    assert homeInstance.player.energy == housing.tierInfo(0)["maxEnergy"]


def test_sleep_restores_energy_to_a_higher_owned_cap():
    # prepare - owning a nicer home raises the cap slept up to
    homeInstance = createHome()
    homeInstance.timeService.increaseDay = MagicMock(return_value={"evicted": False})
    homeInstance.player.homeTier = 3
    homeInstance.player.energy = 10

    # call
    homeInstance.sleep()

    # check
    assert homeInstance.player.energy == housing.tierInfo(3)["maxEnergy"]


def test_sleep_mentions_eviction_when_it_happens():
    # prepare
    homeInstance = createHome()
    homeInstance.timeService.increaseDay = MagicMock(return_value={"evicted": True})

    # call
    homeInstance.sleep()

    # check - the player is told, not just silently moved back to Homeless
    assert housing.EVICTION_MESSAGE in homeInstance.currentPrompt.text


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

    # check - the home rung is always shown, even for a fresh (homeless)
    # player; a fresh player owns no investment properties and has paid no
    # rent, so those lines are omitted
    shownText = homeInstance.userInterface.showDialogue.call_args[0][0]
    assert "Home: Homeless" in shownText
    assert "Investment Properties" not in shownText
    assert "Lifetime Rent Paid" not in shownText


def test_displayStats_includes_rent_paid_when_nonzero():
    # prepare
    homeInstance = createHome()
    homeInstance.stats.totalRentPaid = 40
    homeInstance.userInterface.showDialogue = MagicMock()

    # call
    homeInstance.displayStats()

    # check
    shownText = homeInstance.userInterface.showDialogue.call_args[0][0]
    assert "Lifetime Rent Paid: 40" in shownText


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


def test_manageHome_rented_room_option_discloses_daily_rent():
    # prepare - a homeless player deciding whether to move in
    homeInstance = createHome()
    homeInstance.userInterface.showOptions = MagicMock(return_value="2")

    # call
    homeInstance.manageHome()

    # check - the recurring cost is visible before committing, not just
    # "free" (which would be misleading on its own)
    optionsShown = homeInstance.userInterface.showOptions.call_args[0][1]
    rentedRoomOption = next(o for o in optionsShown if "Rented Room" in o)
    assert "free" in rentedRoomOption
    assert "$%d/day" % housing.tierInfo(1)["dailyRent"] in rentedRoomOption


def test_manageHome_downgrade_cashback_label_is_explicit():
    # prepare
    homeInstance = createHome()
    homeInstance.player.homeTier = 2
    homeInstance.userInterface.showOptions = MagicMock(return_value="3")

    # call
    homeInstance.manageHome()

    # check - "get $X back" rather than an easy-to-miss bare "+$X"
    optionsShown = homeInstance.userInterface.showOptions.call_args[0][1]
    downOption = next(o for o in optionsShown if "down" in o.lower())
    assert "back" in downOption


def test_manageHome_move_up_from_homeless_to_renting_is_free():
    # prepare
    homeInstance = createHome()
    startingMoney = homeInstance.player.money
    # homeless menu is (Move up/Back) = "1" moves up; renting's menu is
    # (Move up/Move down/Back), so "3" backs out
    homeInstance.userInterface.showOptions = MagicMock(side_effect=["1", "3"])

    # call - move up, then back out
    homeInstance.manageHome()

    # check
    assert homeInstance.player.homeTier == 1
    assert homeInstance.player.money == startingMoney
    assert homeInstance.stats.highestHomeTier == 1


def test_manageHome_move_up_from_renting_when_affordable():
    # prepare
    homeInstance = createHome()
    homeInstance.player.homeTier = 1
    homeInstance.player.money = 10000
    netCost = housing.netCostToMove(homeInstance.player, 2)
    # renting's menu is (Move up/Move down/Back) = "1" moves up; the owned
    # tier's menu is the same shape, so "3" backs out
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
    homeInstance.player.homeTier = 1
    homeInstance.player.money = 0
    # the failed move leaves the renting menu (Move up/Move down/Back)
    # unchanged, so "3" backs out both times
    homeInstance.userInterface.showOptions = MagicMock(side_effect=["1", "3"])

    # call - attempt to move up (fails, loop continues), then back out
    homeInstance.manageHome()

    # check - no tier change, no money spent
    assert homeInstance.player.homeTier == 1
    assert homeInstance.player.money == 0


def test_manageHome_move_down_from_owned_pays_cash_back():
    # prepare - own the cheapest tier, move back down to renting
    homeInstance = createHome()
    homeInstance.player.homeTier = 2
    homeInstance.player.money = 0
    homeInstance.stats.highestHomeTier = 2
    expectedRefund = -housing.netCostToMove(homeInstance.player, 1)
    # owned tier's menu is (Move up/Move down/Back) = "2" moves down;
    # renting's menu is the same shape, so "3" backs out
    homeInstance.userInterface.showOptions = MagicMock(side_effect=["2", "3"])

    # call - move down, then back out
    homeInstance.manageHome()

    # check - cash back, and the lifetime "highest tier" stat doesn't regress
    assert homeInstance.player.homeTier == 1
    assert homeInstance.player.money == expectedRefund
    assert homeInstance.stats.highestHomeTier == 2


def test_manageHome_move_down_from_renting_to_homeless_is_free():
    # prepare
    homeInstance = createHome()
    homeInstance.player.homeTier = 1
    homeInstance.player.money = 0
    # renting's menu is (Move up/Move down/Back) = "2" moves down; homeless
    # menu is (Move up/Back), so "2" backs out
    homeInstance.userInterface.showOptions = MagicMock(side_effect=["2", "2"])

    # call - move down, then back out
    homeInstance.manageHome()

    # check
    assert homeInstance.player.homeTier == 0
    assert homeInstance.player.money == 0


def test_manageHome_homeless_has_no_move_down_option():
    # prepare - a fresh (homeless) player has nothing to move down to
    homeInstance = createHome()
    homeInstance.userInterface.showOptions = MagicMock(return_value="2")

    # call - "Back" is the only other option besides "Move to Rented Room"
    homeInstance.manageHome()

    # check
    optionsShown = homeInstance.userInterface.showOptions.call_args[0][1]
    assert not any("down" in option.lower() for option in optionsShown)


def test_manageHome_at_top_tier_has_no_move_up_option():
    # prepare - already at the top tier
    homeInstance = createHome()
    homeInstance.player.homeTier = len(housing.HOUSING_TIERS) - 1
    homeInstance.userInterface.showOptions = MagicMock(return_value="2")

    # call - "Move down" and "Back" are offered, but no "Move up"
    homeInstance.manageHome()

    # check
    optionsShown = homeInstance.userInterface.showOptions.call_args[0][1]
    assert not any("move to" in option.lower() for option in optionsShown)
    assert any("down" in option.lower() for option in optionsShown)
