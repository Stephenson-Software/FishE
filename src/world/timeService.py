import math

from business import business
from investments import investments


# Daily bank interest is deliberately modest and capped so that saving is a
# minor convenience rather than a way to bypass fishing entirely: sleeping is
# free and unlimited, so any large/uncapped compounding rate lets the player
# ignore the core loop and grow money exponentially by repeatedly sleeping.
INTEREST_RATE = 0.02
MAX_INTEREST_PER_DAY = 50


# @author Daniel McCoy Stephenson
class TimeService:
    def __init__(self, player, stats):
        self.player = player
        self.stats = stats

        self.day = 1
        self.time = 8

    def increaseTime(self):
        self.time += 1

        if self.time > 23:
            self.time = 0

        if self.time == 8:
            self.increaseDay()

    def increaseDay(self):
        self.time = 8
        self.day += 1

        moneyToAdd = int(math.ceil(self.player.moneyInBank * INTEREST_RATE))
        moneyToAdd = min(moneyToAdd, MAX_INTEREST_PER_DAY)
        self.player.moneyInBank += moneyToAdd
        self.stats.moneyMadeFromInterest += moneyToAdd
        self.stats.totalMoneyMade += moneyToAdd

        # The fishing business (if any) produces its daily catch and pays wages.
        business.runDailyProduction(self.player, self.stats)

        # Any investment properties (if owned) pay out their daily rental income.
        investments.runDailyIncome(self.player, self.stats)
