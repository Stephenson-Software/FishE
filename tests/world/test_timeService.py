from src.player.player import Player
from src.stats.stats import Stats
from src.world.timeService import TimeService


def createTimeService():
    player = Player()
    stats = Stats()
    return TimeService(player, stats)


def test_initialization():
    # call
    timeService = createTimeService()

    # check
    expected_day = 1
    expected_time = 8
    assert timeService.day == expected_day
    assert timeService.time == expected_time


def test_increaseTime():
    # prepare
    timeService = createTimeService()

    # call
    timeService.increaseTime()

    # check
    expected_day = 1
    expected_time = 9
    assert timeService.day == expected_day
    assert timeService.time == expected_time


def test_increaseTimeToNextDay():
    # prepare
    timeService = createTimeService()
    timeService.time = 7

    # call
    timeService.increaseTime()

    # check
    expected_day = 2
    expected_time = 8
    assert timeService.day == expected_day
    assert timeService.time == expected_time


def test_increaseDay():
    # prepare
    timeService = createTimeService()
    timeService.player.moneyInBank = 100
    timeService.stats.moneyMadeFromInterest = 0
    timeService.stats.totalMoneyMade = 100

    # call
    timeService.increaseDay()

    # check - interest is 2% of 100 = 2 (well under the per-day cap)
    expected_day = 2
    expected_time = 8
    assert timeService.day == expected_day
    assert timeService.time == expected_time
    assert timeService.player.moneyInBank == 102
    assert timeService.stats.moneyMadeFromInterest == 2
    assert timeService.stats.totalMoneyMade == 102


def test_increaseDay_interest_is_capped():
    # prepare - a large balance whose 2% would exceed the per-day cap
    from src.world.timeService import MAX_INTEREST_PER_DAY

    timeService = createTimeService()
    timeService.player.moneyInBank = 1000000
    timeService.stats.moneyMadeFromInterest = 0
    timeService.stats.totalMoneyMade = 0

    # call
    timeService.increaseDay()

    # check - interest is clamped to the cap, not 2% of the balance
    assert timeService.stats.moneyMadeFromInterest == MAX_INTEREST_PER_DAY
    assert timeService.player.moneyInBank == 1000000 + MAX_INTEREST_PER_DAY
    assert timeService.stats.totalMoneyMade == MAX_INTEREST_PER_DAY
