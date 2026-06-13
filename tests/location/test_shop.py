from src.location.enum.locationType import LocationType
from src.location import shop
from src.player.player import Player
from src.prompt.prompt import Prompt
from src.stats.stats import Stats
from src.ui.userInterface import UserInterface
from src.world.timeService import TimeService
from unittest.mock import MagicMock


def createShop():
    currentPrompt = Prompt("What would you like to do?")
    player = Player()
    stats = Stats()
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
    assert shopInstance.currentPrompt.text == "Your bait is already the best money can buy!"


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
    assert shopInstance.currentPrompt.text == "Your rod is already the finest in the village!"


def test_sellFish_limited_by_shop_budget():
    # prepare - a haul worth far more than the shop's daily budget
    from src.fish import fish
    from src.location.shop import SHOP_DAILY_BUDGET

    shopInstance = createShop()
    shopInstance.player.money = 0
    # 100 Marlins ($15-25 each) >> the budget, so the shop can't buy them all
    shopInstance.player.addFish("Marlin", 100)

    # call
    shopInstance.sellFish()

    # check - the shop spent (about) its whole budget and some fish remain unsold
    assert shopInstance.player.money <= SHOP_DAILY_BUDGET
    assert shopInstance.player.money > SHOP_DAILY_BUDGET - 25  # within one fish of the cap
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
