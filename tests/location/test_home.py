from src.location.enum.locationType import LocationType
from src.location import home
from src.player.player import Player
from src.prompt.prompt import Prompt
from src.stats.stats import Stats
from src.ui.userInterface import UserInterface
from src.world.timeService import TimeService
from src.achievements import achievements
from src.housing import housing
from src.progression import progression
from unittest.mock import MagicMock


def createHome(unlocked=True):
    currentPrompt = Prompt("What would you like to do?")
    player = Player()
    stats = Stats()
    if unlocked:
        # These tests are about what the home menu does, not about what a brand
        # new player can see of it (see src/progression); the staged reveal has
        # its own tests below.
        progression.unlockAll(stats)
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


def test_run_no_retire_option_before_goal_reached():
    # prepare - a fresh player has not earned the goal milestone
    homeInstance = createHome()
    homeInstance.userInterface.showOptions = MagicMock(return_value="5")

    # call
    nextLocation = homeInstance.run()

    # check - "5" is still Quit, and Retire is not offered at all
    optionsShown = homeInstance.userInterface.showOptions.call_args[0][1]
    assert "Retire" not in optionsShown
    assert optionsShown[-1] == "Quit"
    assert nextLocation == LocationType.NONE


def test_run_retire_option_appears_after_goal_reached():
    # prepare
    homeInstance = createHome()
    homeInstance.stats.earnedMilestones.append(achievements.GOAL_MILESTONE_NAME)
    homeInstance.userInterface.showOptions = MagicMock(return_value="5")
    homeInstance.retire = MagicMock()

    # call
    nextLocation = homeInstance.run()

    # check - Retire is offered right before Quit, and choosing it ends the run
    optionsShown = homeInstance.userInterface.showOptions.call_args[0][1]
    assert optionsShown[-2:] == ["Retire", "Quit"]
    homeInstance.retire.assert_called_once()
    assert nextLocation == LocationType.NONE


def test_run_quit_still_works_after_goal_reached():
    # prepare - Quit shifts to option "6" once Retire is offered
    homeInstance = createHome()
    homeInstance.stats.earnedMilestones.append(achievements.GOAL_MILESTONE_NAME)
    homeInstance.userInterface.showOptions = MagicMock(return_value="6")
    homeInstance.retire = MagicMock()

    # call
    nextLocation = homeInstance.run()

    # check
    homeInstance.retire.assert_not_called()
    assert nextLocation == LocationType.NONE


def test_retire_shows_summary_with_stats():
    # prepare
    homeInstance = createHome()
    homeInstance.userInterface.showDialogue = MagicMock()

    # call
    homeInstance.retire()

    # check - reuses the same stat lines displayStats() shows
    homeInstance.userInterface.showDialogue.assert_called_once()
    shownText = homeInstance.userInterface.showDialogue.call_args[0][0]
    assert "retire" in shownText.lower()
    assert "Total Fish Caught" in shownText
    assert "Milestones:" in shownText


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


def test_run_shows_only_sleeping_to_a_player_who_just_found_home():
    # prepare - the ledger and the housing ladder are revealed later (see
    # src/progression)
    homeInstance = createHome(unlocked=False)
    homeInstance.userInterface.showOptions = MagicMock(return_value="1")
    homeInstance.sleep = MagicMock()

    # call
    nextLocation = homeInstance.run()

    # check
    options = homeInstance.userInterface.showOptions.call_args[0][1]
    assert options == ["Sleep", "Go to Docks", "Quit"]
    assert nextLocation == LocationType.HOME
    homeInstance.sleep.assert_called_once()


def test_run_quit_still_works_on_the_short_menu():
    # prepare
    homeInstance = createHome(unlocked=False)
    homeInstance.userInterface.showOptions = MagicMock(return_value="3")

    # call
    nextLocation = homeInstance.run()

    # check
    assert nextLocation == LocationType.NONE


def test_run_reveals_the_ledger_and_the_housing_ladder_as_they_unlock():
    # prepare
    homeInstance = createHome(unlocked=False)
    homeInstance.userInterface.showOptions = MagicMock(return_value="1")
    homeInstance.sleep = MagicMock()

    for feature, label in (
        (progression.JOURNAL, "See Stats"),
        (progression.HOUSING, "Manage Home"),
    ):
        # call - before the unlock
        homeInstance.run()

        # check
        assert label not in homeInstance.userInterface.showOptions.call_args[0][1]

        # prepare/call - and after it
        homeInstance.stats.unlockedFeatures.append(feature)
        homeInstance.run()

        # check
        assert label in homeInstance.userInterface.showOptions.call_args[0][1]


def markedOptions(locationInstance):
    """{option label: reason} from the last showOptions call."""
    call = locationInstance.userInterface.showOptions.call_args
    options = call[0][1]
    reasons = call[0][2] if len(call[0]) > 2 else {}
    return {options[number - 1]: reason for number, reason in (reasons or {}).items()}


def chooseBack(descriptor, options, unavailableOptions=None):
    return str(len(options))  # Back is always the last entry


def test_manageHome_greys_out_a_move_the_player_cannot_pay_for():
    # prepare - renting with nothing saved. The rung up has to be bought
    # outright (renting has no resale value to put toward it), so it is out of
    # reach; moving back down to Homeless is free and stays available.
    homeInstance = createHome()
    homeInstance.player.homeTier = 1
    homeInstance.player.money = 0
    homeInstance.userInterface.showOptions = MagicMock(side_effect=chooseBack)

    # call
    homeInstance.manageHome()

    # check
    marked = markedOptions(homeInstance)
    assert set(marked.values()) == {"not enough money"}
    assert all(label.startswith("Move to") for label in marked)
    assert not any(label.startswith("Move down to") for label in marked)


def test_manageHome_leaves_a_move_down_available_when_broke():
    # prepare - moving down the ladder pays cash back rather than costing
    # money (see housing.moveHome), so it is never greyed out
    homeInstance = createHome()
    homeInstance.player.homeTier = len(housing.HOUSING_TIERS) - 1
    homeInstance.player.money = 0
    homeInstance.userInterface.showOptions = MagicMock(side_effect=chooseBack)

    # call
    homeInstance.manageHome()

    # check - only the top rung is occupied, so every offered move is downward
    marked = markedOptions(homeInstance)
    assert marked == {}


def test_manageHome_marks_nothing_when_every_move_is_affordable():
    # prepare - renting, with money for the rung above as well as the one below
    homeInstance = createHome()
    homeInstance.player.homeTier = 1
    homeInstance.player.money = 100000
    homeInstance.userInterface.showOptions = MagicMock(side_effect=chooseBack)

    # call
    homeInstance.manageHome()

    # check
    assert markedOptions(homeInstance) == {}


def test_sleep_reports_what_the_fleet_did_overnight():
    # Sleeping is the commonest way a day passes, so the overnight report has to
    # survive the shared helper this site now routes through.
    homeInstance = createHome()
    homeInstance.timeService.increaseDay = MagicMock(
        return_value={"evicted": False, "report": ["The Marauder landed 12 fish."]}
    )

    # call
    homeInstance.sleep()

    # check - the night's own message leads, the fleet's news follows
    assert homeInstance.currentPrompt.text.startswith(
        "You sleep until the next morning"
    )
    assert "The Marauder landed 12 fish." in homeInstance.currentPrompt.text


def test_displayStats_shows_total_money_made_to_the_cent():
    # prepare - an export multiplier leaves lifetime earnings fractional
    homeInstance = createHome()
    homeInstance.stats.totalMoneyMade = 748.8
    homeInstance.userInterface.showDialogue = MagicMock()

    # call
    homeInstance.displayStats()

    # check - the cents are kept, matching the $%.2f the status header shows
    shownText = homeInstance.userInterface.showDialogue.call_args[0][0]
    assert "Total Money Made: 748.80" in shownText


def test_displayStats_omits_the_fleet_and_export_blocks_for_a_fresh_player():
    # prepare
    homeInstance = createHome()
    homeInstance.userInterface.showDialogue = MagicMock()

    # call
    homeInstance.displayStats()

    # check - a player who has never owned a boat is not shown headings for
    # parts of the game they have not reached
    shownText = homeInstance.userInterface.showDialogue.call_args[0][0]
    assert "Fleet:" not in shownText
    assert "Exports:" not in shownText
    assert "Money Lost While Drunk" not in shownText


def test_displayStats_includes_the_fleet_block_once_the_boats_have_worked():
    # prepare
    homeInstance = createHome()
    homeInstance.stats.boatsOwned = 3
    homeInstance.stats.totalMoneyFromVoyages = 4200
    homeInstance.stats.totalHaulingContracts = 12
    homeInstance.stats.totalTransportRuns = 7
    homeInstance.stats.totalRaids = 4
    homeInstance.stats.totalPlunder = 5100
    homeInstance.stats.crewLostToPiracy = 2
    homeInstance.userInterface.showDialogue = MagicMock()

    # call
    homeInstance.displayStats()

    # check - every role the fleet worked is on the ledger
    shownText = homeInstance.userInterface.showDialogue.call_args[0][0]
    assert "Fleet:" in shownText
    assert "Boats Owned (lifetime): 3" in shownText
    assert "Money From Boat Work: 4200" in shownText
    assert "Freight Days Run: 12" in shownText
    assert "Passenger Runs: 7" in shownText
    assert "Days Spent Raiding: 4" in shownText
    assert "Plunder Taken: 5100" in shownText
    assert "Crew Lost at Sea: 2" in shownText


def test_displayStats_fleet_block_omits_the_roles_never_worked():
    # prepare - a fleet that only ever fished, so no role total but the boat
    # count has anything to say
    homeInstance = createHome()
    homeInstance.stats.boatsOwned = 1
    homeInstance.userInterface.showDialogue = MagicMock()

    # call
    homeInstance.displayStats()

    # check - the block appears, but a role the player never used is left out
    # rather than listed as a zero
    shownText = homeInstance.userInterface.showDialogue.call_args[0][0]
    assert "Boats Owned (lifetime): 1" in shownText
    assert "Days Spent Raiding" not in shownText
    assert "Freight Days Run" not in shownText
    assert "Voyages Foundered" not in shownText


def test_displayStats_keeps_the_fleet_record_after_every_boat_is_sold():
    # prepare - a lifetime of piracy, but nothing owned today
    homeInstance = createHome()
    homeInstance.player.boats = []
    homeInstance.stats.totalPlunder = 900
    homeInstance.userInterface.showDialogue = MagicMock()

    # call
    homeInstance.displayStats()

    # check - the career ledger is about the career, not the current fleet
    assert not homeInstance.player.hasBoat
    shownText = homeInstance.userInterface.showDialogue.call_args[0][0]
    assert "Plunder Taken: 900" in shownText


def test_displayStats_includes_captained_voyages_in_the_fleet_block():
    # prepare
    homeInstance = createHome()
    homeInstance.stats.totalVoyagesCaptained = 11
    homeInstance.stats.totalVoyagesFoundered = 2
    homeInstance.userInterface.showDialogue = MagicMock()

    # call
    homeInstance.displayStats()

    # check - progress toward the ten-voyage milestone is visible, not just
    # its unticked box
    shownText = homeInstance.userInterface.showDialogue.call_args[0][0]
    assert "Voyages Captained: 11" in shownText
    assert "Voyages Foundered: 2" in shownText


def test_displayStats_includes_the_export_block_once_fish_have_shipped():
    # prepare - a market multiplier leaves the gross fractional
    homeInstance = createHome()
    homeInstance.stats.totalFishExported = 1250
    homeInstance.stats.totalMoneyFromExports = 3612.5
    homeInstance.stats.totalShippingPaid = 275
    homeInstance.userInterface.showDialogue = MagicMock()

    # call
    homeInstance.displayStats()

    # check - the gross keeps its cents, the freight is shown beside it
    shownText = homeInstance.userInterface.showDialogue.call_args[0][0]
    assert "Exports:" in shownText
    assert "Fish Exported: 1250" in shownText
    assert "Money From Exports: 3612.50" in shownText
    assert "Freight Paid: 275" in shownText


def test_displayStats_includes_money_lost_while_drunk_when_nonzero():
    # prepare
    homeInstance = createHome()
    homeInstance.stats.moneyLostWhileDrunk = 65
    homeInstance.userInterface.showDialogue = MagicMock()

    # call
    homeInstance.displayStats()

    # check - it sits with the other night-at-the-tavern lines
    shownText = homeInstance.userInterface.showDialogue.call_args[0][0]
    assert "Money Lost While Drunk: 65" in shownText


def test_retire_summary_shows_the_fleet_and_export_record():
    # prepare - retire reuses the ledger, so the closing summary gets the
    # same blocks
    homeInstance = createHome()
    homeInstance.stats.totalPlunder = 5000
    homeInstance.stats.totalFishExported = 400
    homeInstance.userInterface.showDialogue = MagicMock()

    # call
    homeInstance.retire()

    # check
    shownText = homeInstance.userInterface.showDialogue.call_args[0][0]
    assert "Plunder Taken: 5000" in shownText
    assert "Fish Exported: 400" in shownText


def test_displayStats_keeps_the_wage_bill_beside_a_sold_off_fleets_takings():
    # prepare - a business that ran for a while and was then sold off entirely
    homeInstance = createHome()
    homeInstance.player.boats = []
    homeInstance.stats.daysInBusiness = 30
    homeInstance.stats.totalWagesPaid = 600
    homeInstance.stats.totalMoneyFromVoyages = 2400
    homeInstance.userInterface.showDialogue = MagicMock()

    # call
    homeInstance.displayStats()

    # check - the takings are not shown without the wages they were earned
    # against, which would flatter the fleet's record
    assert not homeInstance.player.hasBoat
    shownText = homeInstance.userInterface.showDialogue.call_args[0][0]
    assert "Money From Boat Work: 2400" in shownText
    assert "Wages Paid: 600" in shownText
    assert "Days in Business: 30" in shownText


def test_displayStats_omits_the_business_block_for_a_player_who_never_had_one():
    # prepare
    homeInstance = createHome()
    homeInstance.userInterface.showDialogue = MagicMock()

    # call
    homeInstance.displayStats()

    # check - nothing changes for a player who never bought a boat
    shownText = homeInstance.userInterface.showDialogue.call_args[0][0]
    assert "Days in Business" not in shownText
    assert "Wages Paid" not in shownText
