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


def test_run_go_to_docks_action():
    # prepare
    shopInstance = createShop()
    shopInstance.userInterface.showOptions = MagicMock(return_value="4")

    # call
    nextLocation = shopInstance.run()

    # check
    assert nextLocation == LocationType.DOCKS


def test_run_talk_to_npc_action():
    # prepare
    shopInstance = createShop()
    shopInstance.userInterface.showOptions = MagicMock(return_value="3")
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


def test_buyBetterBait_adds_money_to_shop_total():
    # prepare
    shopInstance = createShop()
    shopInstance.player.money = 100
    shopInstance.player.fishMultiplier = 1
    shopInstance.stats.totalMoneyMade = 0

    # call
    shopInstance.buyBetterBait()

    # check
    assert shopInstance.stats.totalMoneyMade == 50
