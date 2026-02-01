from src.location.enum.locationType import LocationType
from src.location import bank
from src.player.player import Player
from src.prompt.prompt import Prompt
from src.stats.stats import Stats
from src.ui.userInterface import UserInterface
from src.world.timeService import TimeService
from unittest.mock import MagicMock


def createBank():
    currentPrompt = Prompt("What would you like to do?")
    player = Player()
    stats = Stats()
    timeService = TimeService(player, stats)
    userInterface = UserInterface(currentPrompt, timeService, player)
    return bank.Bank(userInterface, currentPrompt, player, stats, timeService)


def test_initialization():
    # call
    bankInstance = createBank()

    # check
    assert bankInstance.userInterface != None
    assert bankInstance.currentPrompt != None
    assert bankInstance.player != None
    assert bankInstance.stats != None
    assert bankInstance.timeService != None
    assert bankInstance.npc != None
    assert bankInstance.npc.name == "Margaret the Teller"


def test_run_make_deposit_success():
    # prepare
    bankInstance = createBank()
    bankInstance.userInterface.showOptions = MagicMock(return_value="1")
    bankInstance.player.money = 100
    bankInstance.deposit = MagicMock()

    # call
    nextLocation = bankInstance.run()

    # check
    bankInstance.deposit.assert_called_once()
    assert nextLocation == LocationType.BANK


def test_run_make_deposit_failure_no_money():
    # prepare
    bankInstance = createBank()
    bankInstance.userInterface.showOptions = MagicMock(return_value="1")
    bankInstance.player.money = 0
    bankInstance.deposit = MagicMock()

    # call
    nextLocation = bankInstance.run()

    # check
    bankInstance.deposit.assert_not_called()
    assert nextLocation == LocationType.BANK


def test_run_make_withdrawal_success():
    # prepare
    bankInstance = createBank()
    bankInstance.userInterface.showOptions = MagicMock(return_value="2")
    bankInstance.player.moneyInBank = 100
    bankInstance.withdraw = MagicMock()

    # call
    nextLocation = bankInstance.run()

    # check
    bankInstance.withdraw.assert_called_once()
    assert nextLocation == LocationType.BANK


def test_run_make_withdrawal_failure_no_money():
    # prepare
    bankInstance = createBank()
    bankInstance.userInterface.showOptions = MagicMock(return_value="2")
    bankInstance.player.moneyInBank = 0
    bankInstance.withdraw = MagicMock()

    # call
    nextLocation = bankInstance.run()

    # check
    bankInstance.withdraw.assert_not_called()
    assert nextLocation == LocationType.BANK


def test_run_go_to_docks_action():
    # prepare
    bankInstance = createBank()
    bankInstance.userInterface.showOptions = MagicMock(return_value="4")

    # call
    nextLocation = bankInstance.run()

    # check
    assert nextLocation == LocationType.DOCKS


def test_run_talk_to_npc_action():
    # prepare
    bankInstance = createBank()
    bankInstance.userInterface.showOptions = MagicMock(return_value="3")
    bankInstance.talkToNPC = MagicMock()

    # call
    nextLocation = bankInstance.run()

    # check
    assert nextLocation == LocationType.BANK
    bankInstance.talkToNPC.assert_called_once()


def test_talkToNPC():
    # prepare
    bankInstance = createBank()
    
    # check
    assert bankInstance.npc.name == "Margaret the Teller"
    assert len(bankInstance.npc.backstory) > 0


def test_deposit_success():
    # prepare
    bankInstance = createBank()
    bankInstance.userInterface.lotsOfSpace = MagicMock()
    bankInstance.userInterface.divider = MagicMock()
    bankInstance.player.money = 100
    bankInstance.player.moneyInBank = 0
    bank.print = MagicMock()
    bank.input = MagicMock(return_value="10")

    # call
    bankInstance.deposit()

    # check
    bank.print.assert_called_once()
    assert bankInstance.player.moneyInBank == 10
    assert bankInstance.player.money == 90


def test_deposit_failure_not_enough_money():
    # prepare
    bankInstance = createBank()
    bankInstance.userInterface.lotsOfSpace = MagicMock()
    bankInstance.userInterface.divider = MagicMock()
    bankInstance.player.money = 5
    bankInstance.player.moneyInBank = 0
    bank.print = MagicMock()
    bank.input = MagicMock(return_value="10")

    # call
    bankInstance.deposit()

    # check
    bank.print.assert_called_once()
    assert bankInstance.player.moneyInBank == 0
    assert bankInstance.player.money == 5


def test_withdraw_success():
    # prepare
    bankInstance = createBank()
    bankInstance.userInterface.lotsOfSpace = MagicMock()
    bankInstance.userInterface.divider = MagicMock()
    bankInstance.player.moneyInBank = 100
    bankInstance.player.money = 0
    bank.print = MagicMock()
    bank.input = MagicMock(return_value="10")

    # call
    bankInstance.withdraw()

    # check
    bank.print.assert_called_once()
    assert bankInstance.player.moneyInBank == 90
    assert bankInstance.player.money == 10


def test_withdraw_failure_not_enough_money():
    # prepare
    bankInstance = createBank()
    bankInstance.userInterface.lotsOfSpace = MagicMock()
    bankInstance.userInterface.divider = MagicMock()
    bankInstance.player.moneyInBank = 5
    bankInstance.player.money = 0
    bank.print = MagicMock()
    bank.input = MagicMock(return_value="10")

    # call
    bankInstance.withdraw()

    # check
    bank.print.assert_called_once()
    assert bankInstance.player.moneyInBank == 5
    assert bankInstance.player.money == 0


def test_deposit_with_decimal():
    # prepare
    bankInstance = createBank()
    bankInstance.userInterface.lotsOfSpace = MagicMock()
    bankInstance.userInterface.divider = MagicMock()
    bankInstance.player.money = 100.50
    bankInstance.player.moneyInBank = 0
    bank.print = MagicMock()
    bank.input = MagicMock(return_value="10.25")

    # call
    bankInstance.deposit()

    # check
    bank.print.assert_called_once()
    assert bankInstance.player.moneyInBank == 10.25
    assert bankInstance.player.money == 90.25


def test_withdraw_with_decimal():
    # prepare
    bankInstance = createBank()
    bankInstance.userInterface.lotsOfSpace = MagicMock()
    bankInstance.userInterface.divider = MagicMock()
    bankInstance.player.moneyInBank = 100.75
    bankInstance.player.money = 0
    bank.print = MagicMock()
    bank.input = MagicMock(return_value="10.50")

    # call
    bankInstance.withdraw()

    # check
    bank.print.assert_called_once()
    assert bankInstance.player.moneyInBank == 90.25
    assert bankInstance.player.money == 10.50
