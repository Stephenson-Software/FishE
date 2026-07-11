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


def test_increaseTime_returns_not_evicted_without_a_day_rollover():
    # prepare
    timeService = createTimeService()

    # call
    summary = timeService.increaseTime()

    # check
    assert summary == {"evicted": False}


def test_increaseTime_surfaces_eviction_on_day_rollover():
    # prepare - renting but broke, one hour from the day rolling over
    timeService = createTimeService()
    timeService.time = 7
    timeService.player.homeTier = 1
    timeService.player.money = 0

    # call
    summary = timeService.increaseTime()

    # check
    assert summary == {"evicted": True}
    assert timeService.player.homeTier == 0


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


def test_increaseDay_runs_business_production():
    # prepare - a boat and one worker, no bank balance (isolate from interest)
    from src.business import business

    timeService = createTimeService()
    timeService.player.hasBoat = True
    timeService.player.workers = 1
    timeService.player.money = 1000
    timeService.player.moneyInBank = 0

    # call
    timeService.increaseDay()

    # check - the worker fished and was paid as part of the day rollover
    assert timeService.player.fishCount == business.WORKER_FISH_PER_DAY
    assert timeService.player.money == 1000 - business.WORKER_DAILY_WAGE


def test_increaseDay_runs_investment_property_income():
    # prepare - an owned rental property, no bank balance (isolate from interest)
    from src.investments import investments

    timeService = createTimeService()
    timeService.player.rentalProperties = [1]
    timeService.player.money = 100
    timeService.player.moneyInBank = 0

    # call
    timeService.increaseDay()

    # check - rental income was paid out as part of the day rollover
    expectedIncome = investments.typeInfo(1)["dailyIncome"]
    assert timeService.player.money == 100 + expectedIncome
    assert timeService.stats.totalRentalIncome == expectedIncome


def test_increaseDay_charges_rent_while_renting():
    # prepare - renting, no bank balance (isolate from interest)
    from src.housing import housing

    timeService = createTimeService()
    timeService.player.homeTier = 1
    timeService.player.money = 100
    timeService.player.moneyInBank = 0

    # call
    timeService.increaseDay()

    # check - rent was charged as part of the day rollover
    expectedRent = housing.tierInfo(1)["dailyRent"]
    assert timeService.player.money == 100 - expectedRent
    assert timeService.stats.totalRentPaid == expectedRent


def test_increaseDay_evicts_when_rent_is_unaffordable():
    # prepare - renting but broke
    timeService = createTimeService()
    timeService.player.homeTier = 1
    timeService.player.money = 0
    timeService.player.moneyInBank = 0

    # call
    timeService.increaseDay()

    # check - evicted back to homeless as part of the day rollover
    assert timeService.player.homeTier == 0
    assert timeService.player.money == 0
