from src.location.enum.locationType import LocationType
from src.location import shop
from src.location import docks
from src.player.player import Player
from src.prompt.prompt import Prompt
from src.stats.stats import Stats
from src.ui.userInterface import UserInterface
from src.world.timeService import TimeService
from src.business import boats
from src.business import export
from src.progression import progression
from unittest.mock import MagicMock


def createShop(unlocked=True):
    currentPrompt = Prompt("What would you like to do?")
    player = Player()
    stats = Stats()
    if unlocked:
        # These tests are about what the shop does, not about what a brand new
        # player can see of it (see src/progression); the staged reveal has its
        # own tests below.
        progression.unlockAll(stats)
    timeService = TimeService(player, stats)
    userInterface = UserInterface(currentPrompt, timeService, player)
    return shop.Shop(userInterface, currentPrompt, player, stats, timeService)


def test_initialization():
    # call
    shopInstance = createShop()

    # check
    assert shopInstance.userInterface != None
    assert shopInstance.currentPrompt != None
    assert shopInstance.player != None
    assert shopInstance.stats != None
    assert shopInstance.timeService != None
    assert shopInstance.npc != None
    assert shopInstance.npc.name == "Gilbert the Shopkeeper"


def test_run_sell_fish_action():
    # prepare
    shopInstance = createShop()
    shopInstance.userInterface.showOptions = MagicMock(return_value="1")
    shopInstance.sellFish = MagicMock()

    # call
    nextLocation = shopInstance.run()

    # check
    assert nextLocation == LocationType.SHOP
    shopInstance.sellFish.assert_called_once()


def test_run_buy_better_bait_action():
    # prepare
    shopInstance = createShop()
    shopInstance.userInterface.showOptions = MagicMock(return_value="2")
    shopInstance.buyBetterBait = MagicMock()

    # call
    nextLocation = shopInstance.run()

    # check
    assert nextLocation == LocationType.SHOP
    shopInstance.buyBetterBait.assert_called_once()


def test_run_buy_better_rod_action():
    # prepare
    shopInstance = createShop()
    shopInstance.userInterface.showOptions = MagicMock(return_value="3")
    shopInstance.buyBetterRod = MagicMock()

    # call
    nextLocation = shopInstance.run()

    # check
    assert nextLocation == LocationType.SHOP
    shopInstance.buyBetterRod.assert_called_once()


def test_run_go_to_docks_action():
    # prepare
    shopInstance = createShop()
    shopInstance.userInterface.showOptions = MagicMock(return_value="5")

    # call
    nextLocation = shopInstance.run()

    # check
    assert nextLocation == LocationType.DOCKS


def test_run_talk_to_npc_action():
    # prepare
    shopInstance = createShop()
    shopInstance.userInterface.showOptions = MagicMock(return_value="4")
    shopInstance.talkToNPC = MagicMock()

    # call
    nextLocation = shopInstance.run()

    # check
    assert nextLocation == LocationType.SHOP
    shopInstance.talkToNPC.assert_called_once()


def test_talkToNPC():
    # prepare
    shopInstance = createShop()
    shopInstance.userInterface.showInteractiveDialogue = MagicMock()

    # call
    shopInstance.talkToNPC()

    # check
    shopInstance.userInterface.showInteractiveDialogue.assert_called_once()
    call_args = shopInstance.userInterface.showInteractiveDialogue.call_args[0][0]
    assert call_args.name == "Gilbert the Shopkeeper"
    assert len(call_args.get_dialogue_options()) > 0


def test_npc_crew_dialogue_no_business():
    # prepare - no boat
    shopInstance = createShop()

    # check
    assert "Can't say I have" in shopInstance._crewDialogue()


def test_npc_crew_dialogue_no_workers():
    # prepare - a boat but no crew hired
    shopInstance = createShop()
    boats.addBoat(shopInstance.player, 1)

    # check
    assert "Can't say I have" in shopInstance._crewDialogue()


def test_npc_crew_dialogue_reports_daily_catch():
    # prepare
    from src.business import business

    shopInstance = createShop()
    boat = boats.addBoat(shopInstance.player, 2)
    boat["hands"] = 3
    shopInstance.player.workers = 3

    # check - the reported total matches the fleet's actual daily catch
    expected = business.tierInfo(2)["fishPerDay"] * 3
    response = shopInstance._crewDialogue()
    assert str(expected) in response
    assert "That I have" in response


def test_npc_crew_dialogue_ignores_non_fishing_boats():
    # prepare - crew are aboard, but on a piracy boat, so they land no fish
    shopInstance = createShop()
    boat = boats.addBoat(shopInstance.player, 2, role=boats.ROLE_PIRACY)
    boat["hands"] = 3
    shopInstance.player.workers = 3

    # check - Gilbert reports the true (zero) catch, not the best hull's rate
    response = shopInstance._crewDialogue()
    assert "0 fish a day" in response


def test_sellFish():
    # prepare
    shopInstance = createShop()
    shopInstance.player.fishCount = 10

    # call
    shopInstance.sellFish()

    # check
    assert shopInstance.player.fishCount == 0
    assert shopInstance.player.money > 0
    assert shopInstance.stats.totalMoneyMade > 0


def test_sellFish_prices_by_species():
    # prepare - hold two marlin (a high-value species)
    from src.fish import fish

    shopInstance = createShop()
    shopInstance.player.money = 0
    shopInstance.player.addFish("Marlin", 2)
    marlin = fish.getFishType("Marlin")

    # call
    shopInstance.sellFish()

    # check - sale is within 2x the species value range; inventory cleared
    assert 2 * marlin["minValue"] <= shopInstance.player.money <= 2 * marlin["maxValue"]
    assert shopInstance.player.fishByType == {}
    assert shopInstance.player.fishCount == 0


def test_buyBetterBait():
    # prepare
    shopInstance = createShop()
    shopInstance.player.money = 100
    shopInstance.player.fishMultiplier = 1

    # call
    shopInstance.buyBetterBait()

    # check
    assert shopInstance.player.money == 50
    assert shopInstance.player.fishMultiplier == 2
    assert shopInstance.player.priceForBait > 0


def test_buyBetterBait_refused_at_cap():
    # prepare - multiplier already at the cap, with plenty of money
    from src.location.shop import MAX_FISH_MULTIPLIER

    shopInstance = createShop()
    shopInstance.player.money = 10000
    shopInstance.player.fishMultiplier = MAX_FISH_MULTIPLIER
    priceBefore = shopInstance.player.priceForBait

    # call
    shopInstance.buyBetterBait()

    # check - no purchase: multiplier, money, and price are unchanged
    assert shopInstance.player.fishMultiplier == MAX_FISH_MULTIPLIER
    assert shopInstance.player.money == 10000
    assert shopInstance.player.priceForBait == priceBefore
    assert (
        shopInstance.currentPrompt.text
        == "Your bait is already the best money can buy!"
    )


def test_buyBetterRod():
    # prepare
    from src.location.shop import rodUpgradeCost

    shopInstance = createShop()
    shopInstance.player.rodLevel = 1
    cost = rodUpgradeCost(1)
    shopInstance.player.money = cost + 100

    # call
    shopInstance.buyBetterRod()

    # check - rod level up and money reduced by the level-scaled cost
    assert shopInstance.player.rodLevel == 2
    assert shopInstance.player.money == 100
    assert shopInstance.currentPrompt.text == "You bought a better fishing rod!"


def test_buyBetterRod_refused_when_too_poor():
    # prepare
    from src.location.shop import rodUpgradeCost

    shopInstance = createShop()
    shopInstance.player.rodLevel = 1
    shopInstance.player.money = rodUpgradeCost(1) - 1

    # call
    shopInstance.buyBetterRod()

    # check - no change
    assert shopInstance.player.rodLevel == 1
    assert shopInstance.currentPrompt.text == "You don't have enough money!"


def test_buyBetterRod_refused_at_cap():
    # prepare
    from src.location.shop import MAX_ROD_LEVEL

    shopInstance = createShop()
    shopInstance.player.rodLevel = MAX_ROD_LEVEL
    shopInstance.player.money = 1000000

    # call
    shopInstance.buyBetterRod()

    # check - no purchase past the cap
    assert shopInstance.player.rodLevel == MAX_ROD_LEVEL
    assert shopInstance.player.money == 1000000
    assert (
        shopInstance.currentPrompt.text
        == "Your rod is already the finest in the village!"
    )


def test_sellFish_limited_by_shop_budget():
    # prepare - a haul worth far more than the shop's daily budget
    from src.location.shop import SHOP_DAILY_BUDGET

    shopInstance = createShop()
    shopInstance.player.money = 0
    # 100 Marlins ($15-25 each) >> the budget, so the shop can't buy them all
    shopInstance.player.addFish("Marlin", 100)

    # call
    shopInstance.sellFish()

    # check - the shop spent (about) its whole budget and some fish remain unsold
    assert shopInstance.player.money <= SHOP_DAILY_BUDGET
    assert (
        shopInstance.player.money > SHOP_DAILY_BUDGET - 25
    )  # within one fish of the cap
    assert shopInstance.money < 25  # budget nearly exhausted
    assert shopInstance.player.fishCount > 0  # leftovers carried over
    assert "out of money for today" in shopInstance.currentPrompt.text


def test_shop_budget_refills_next_day():
    # prepare - exhaust the shop's budget
    shopInstance = createShop()
    shopInstance.player.addFish("Marlin", 100)
    shopInstance.sellFish()
    assert shopInstance.money < 25  # drained

    # a new day begins
    shopInstance.timeService.day += 1

    # call - selling again first refills the budget for the new day
    leftover_before = shopInstance.player.fishCount
    shopInstance.sellFish()

    # check - more fish sold (budget refilled), inventory shrank further
    assert shopInstance.player.fishCount < leftover_before


def test_sellFish_no_fish_message():
    # prepare
    shopInstance = createShop()
    shopInstance.player.clearFish()

    # call
    shopInstance.sellFish()

    # check
    assert shopInstance.currentPrompt.text == "You have no fish to sell."


def test_gilbert_crew_customer_question_is_locked_until_someone_is_hired():
    # prepare
    shopInstance = createShop()

    # call
    questions = [
        option["question"] for option in shopInstance.npc.get_dialogue_options()
    ]

    # check
    assert "Do my crew shop here?" not in questions

    # prepare - hire a villager
    boats.addBoat(shopInstance.player, 1)
    boats.hireWorker(shopInstance.player, "Marta Kell")

    # call
    options = shopInstance.npc.get_dialogue_options()
    questions = [option["question"] for option in options]

    # check - Gilbert now recognises them across the counter
    assert "Do my crew shop here?" in questions
    index = questions.index("Do my crew shop here?")
    assert "Marta Kell" in shopInstance.npc.get_dialogue_response(index)


def test_gilbert_crew_customer_dialogue_names_a_whole_crew():
    # prepare
    shopInstance = createShop()
    boats.addBoat(shopInstance.player, 1)
    boats.hireWorker(shopInstance.player, "Marta Kell")
    boats.hireWorker(shopInstance.player, "Owen Brackish")

    # call
    response = shopInstance._crewCustomerDialogue()

    # check
    assert "Marta Kell and Owen Brackish" in response


def test_gilbert_budget_question_unlocks_with_a_boat_that_can_export():
    # prepare - a Rowboat can't reach the other villages
    shopInstance = createShop()
    boats.addBoat(shopInstance.player, 1)

    # call
    questions = [
        option["question"] for option in shopInstance.npc.get_dialogue_options()
    ]

    # check
    assert "Why can't you buy my whole catch?" not in questions

    # prepare - upgrade to a Trawler
    boats.addBoat(shopInstance.player, 2)

    # call
    options = shopInstance.npc.get_dialogue_options()
    questions = [option["question"] for option in options]

    # check - Gilbert explains his budget and points at the export markets
    assert "Why can't you buy my whole catch?" in questions
    index = questions.index("Why can't you buy my whole catch?")
    response = shopInstance.npc.get_dialogue_response(index)
    assert str(shop.SHOP_DAILY_BUDGET) in response
    for market in export.availableMarkets(shopInstance.player):
        assert market["name"] in response


def test_sellFish_leftover_advice_mentions_exporting_once_possible():
    # prepare - more fish than the shop's daily budget can cover, and a
    # Trawler to ship the rest with
    shopInstance = createShop()
    boats.addBoat(shopInstance.player, 2)
    shopInstance.player.addFish("Golden Koi", 100)

    # call
    shopInstance.sellFish()

    # check - the player is pointed somewhere useful, not just told to wait
    assert shopInstance.player.fishCount > 0
    assert "ship them out from the docks" in shopInstance.currentPrompt.text


def test_sellFish_leftover_advice_without_an_export_boat():
    # prepare - the same backlog but only a Rowboat
    shopInstance = createShop()
    boats.addBoat(shopInstance.player, 1)
    shopInstance.player.addFish("Golden Koi", 100)

    # call
    shopInstance.sellFish()

    # check - the original advice stands when there's nowhere else to sell
    assert shopInstance.player.fishCount > 0
    assert "Come back tomorrow for the rest." in shopInstance.currentPrompt.text
    assert "docks" not in shopInstance.currentPrompt.text


def test_run_shows_only_selling_to_a_player_who_just_found_the_shop():
    # prepare - the shop opens up the moment there are fish to sell, and
    # nothing on the walls has been revealed yet (see src/progression)
    shopInstance = createShop(unlocked=False)
    shopInstance.userInterface.showOptions = MagicMock(return_value="1")
    shopInstance.sellFish = MagicMock()

    # call
    nextLocation = shopInstance.run()

    # check
    options = shopInstance.userInterface.showOptions.call_args[0][1]
    assert options == ["Sell Fish", "Go to Docks"]
    assert nextLocation == LocationType.SHOP
    shopInstance.sellFish.assert_called_once()


def test_run_go_to_docks_is_always_the_last_entry():
    # prepare - the way back can't depend on what has been unlocked
    shopInstance = createShop(unlocked=False)
    shopInstance.userInterface.showOptions = MagicMock(return_value="2")

    # call
    nextLocation = shopInstance.run()

    # check
    assert nextLocation == LocationType.DOCKS


def test_run_reveals_the_gear_as_it_is_unlocked():
    # prepare
    shopInstance = createShop(unlocked=False)
    shopInstance.userInterface.showOptions = MagicMock(return_value="1")
    shopInstance.sellFish = MagicMock()

    for feature, label in (
        (progression.BAIT, "Buy Better Bait"),
        (progression.ROD, "Buy Better Rod"),
        (progression.TALK, "Talk to Gilbert the Shopkeeper"),
    ):
        # call - before the unlock
        shopInstance.run()

        # check
        options = shopInstance.userInterface.showOptions.call_args[0][1]
        assert not any(option.startswith(label) for option in options)

        # prepare/call - and after it
        shopInstance.stats.unlockedFeatures.append(feature)
        shopInstance.run()

        # check
        options = shopInstance.userInterface.showOptions.call_args[0][1]
        assert any(option.startswith(label) for option in options)


def test_run_buying_bait_fires_from_its_actual_position():
    # prepare - bait unlocked but the rod not, so "Buy Better Bait" is entry 2
    shopInstance = createShop(unlocked=False)
    shopInstance.stats.unlockedFeatures.append(progression.BAIT)
    shopInstance.userInterface.showOptions = MagicMock(return_value="2")
    shopInstance.buyBetterBait = MagicMock()

    # call
    nextLocation = shopInstance.run()

    # check
    assert nextLocation == LocationType.SHOP
    shopInstance.buyBetterBait.assert_called_once()


def test_gilbert_sell_pitch_quotes_the_actual_catalogue_range():
    # prepare
    shopInstance = createShop()
    cheapest, priciest = shop._cheapestAndPriciestFish()

    # call
    response = shopInstance._sellPitchDialogue()

    # check - the old flat $3-5 range is gone, replaced by the real bounds
    assert "$3 to $5" not in response
    assert "$%d" % cheapest["minValue"] in response
    assert cheapest["name"] in response
    assert "$%d" % priciest["maxValue"] in response
    assert priciest["name"] in response
    assert cheapest["name"] == "Minnow"
    assert priciest["name"] == "Golden Koi"


def test_gilbert_selling_tips_quotes_the_actual_catalogue_range():
    # prepare
    shopInstance = createShop()
    cheapest, priciest = shop._cheapestAndPriciestFish()

    # call
    response = shopInstance._sellingTipsDialogue()

    # check
    assert "between $3 and $5" not in response
    assert "$%d" % cheapest["minValue"] in response
    assert "$%d" % priciest["maxValue"] in response


def test_gilbert_fishing_explanation_quotes_the_base_reaction_window():
    # prepare - rod level 1 is the base window
    shopInstance = createShop()
    assert shopInstance.player.rodLevel == 1

    # call
    response = shopInstance._howFishingWorksDialogue()

    # check
    assert "within 2 seconds" not in response
    assert "%.1f seconds" % docks.REACTION_BASE_WINDOW in response


def test_gilbert_fishing_explanation_widens_with_rod_level():
    # prepare - a maxed-out rod widens the window well past the base 2.0s
    shopInstance = createShop()
    shopInstance.player.rodLevel = shop.MAX_ROD_LEVEL
    expectedWindow = docks.REACTION_BASE_WINDOW + (
        shop.MAX_ROD_LEVEL - 1
    ) * docks.ROD_WINDOW_STEP

    # call
    response = shopInstance._howFishingWorksDialogue()

    # check
    assert "%.1f seconds" % expectedWindow in response
    assert "%.1f seconds" % docks.REACTION_BASE_WINDOW not in response
