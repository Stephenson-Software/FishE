import math
import random

from business import business
from housing import housing
from investments import investments


# Daily bank interest is deliberately modest and capped so that saving is a
# minor convenience rather than a way to bypass fishing entirely: sleeping is
# free and unlimited, so any large/uncapped compounding rate lets the player
# ignore the core loop and grow money exponentially by repeatedly sleeping.
INTEREST_RATE = 0.02
MAX_INTEREST_PER_DAY = 50

# Weather rolls fresh each day (see increaseDay) so it stays unpredictable in
# a way the fully-known time-of-day windows aren't - see Docks.getWeatherModifier
# for how each option affects the day's catch.
WEATHER_OPTIONS = ["clear", "rainy", "stormy"]


# @author Daniel McCoy Stephenson
class TimeService:
    def __init__(self, player, stats):
        self.player = player
        self.stats = stats

        self.day = 1
        self.time = 8
        self.weather = "clear"

    def increaseTime(self):
        """Advance the clock by an hour. Returns {"evicted": bool} so callers
        can tell the player if a day rolled over during this call and they
        lost a rented room - since any action can advance time, this is the
        only reliable place to catch that regardless of what triggered it."""
        self.time += 1

        if self.time > 23:
            self.time = 0

        if self.time == 8:
            return self.increaseDay()
        return {"evicted": False}

    def increaseDay(self):
        """Roll the clock to a new day and run every daily-tick system.
        Returns {"evicted": bool} - see housing.runDailyRent."""
        self.time = 8
        self.day += 1
        self.weather = random.choice(WEATHER_OPTIONS)

        moneyToAdd = int(math.ceil(self.player.moneyInBank * INTEREST_RATE))
        moneyToAdd = min(moneyToAdd, MAX_INTEREST_PER_DAY)
        self.player.moneyInBank += moneyToAdd
        self.stats.moneyMadeFromInterest += moneyToAdd
        self.stats.totalMoneyMade += moneyToAdd

        # The fishing business (if any) produces its daily catch and pays wages.
        business.runDailyProduction(self.player, self.stats)

        # Any investment properties (if owned) pay out their daily rental income.
        investments.runDailyIncome(self.player, self.stats)

        # A rented room (if any) charges its daily rent, evicting the player
        # back to Homeless if they can't cover it.
        rentSummary = housing.runDailyRent(self.player, self.stats)
        return {"evicted": rentSummary["evicted"]}
