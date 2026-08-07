import math
import random

from business import boats
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
        return {"evicted": False, "report": []}

    def increaseDay(self):
        """Roll the clock to a new day and run every daily-tick system.

        Returns {"evicted": bool, "report": [str]}. The report is what the
        fleet did overnight (see boats.describeDay) - now that every role
        earns, and a pirate crew can come home a man short, the player has to
        be told rather than left to notice their roster changed."""
        self.time = 8
        self.day += 1
        self.weather = random.choice(WEATHER_OPTIONS)

        moneyToAdd = int(math.ceil(self.player.moneyInBank * INTEREST_RATE))
        moneyToAdd = min(moneyToAdd, MAX_INTEREST_PER_DAY)
        self.player.moneyInBank += moneyToAdd
        self.stats.moneyMadeFromInterest += moneyToAdd
        self.stats.totalMoneyMade += moneyToAdd

        # The fleet (if any) earns its keep and pays wages.
        fleetSummary = boats.runDailyProduction(self.player, self.stats)

        # Any investment properties (if owned) pay out their daily rental income.
        investments.runDailyIncome(self.player, self.stats)

        # A rented room (if any) charges its daily rent, evicting the player
        # back to Homeless if they can't cover it.
        rentSummary = housing.runDailyRent(self.player, self.stats)
        return {
            "evicted": rentSummary["evicted"],
            "report": boats.describeDay(fleetSummary),
        }


def dayReportLines(summary):
    """What the player has to be told about a day that just passed.

    Takes increaseDay()'s (or increaseTime()'s) return value and turns it into
    display lines: the fleet's overnight takings, then the eviction notice if
    rent went unpaid.

    Lives beside the producer because reading only "evicted" and dropping
    "report" is the mistake this is here to stop being possible - a player
    could sail a multi-day voyage and come home a crew member short, or
    homeless, without a line of text saying so. increaseTime() returns
    {"evicted": False, "report": []} on the hours that don't roll a day, so
    every caller can pass its return value straight in without first checking
    whether a day actually turned over; the result is simply empty."""
    lines = list(summary.get("report", []))
    if summary.get("evicted"):
        lines.append(housing.EVICTION_MESSAGE)
    return lines


def appendDayReport(prompt, summary, separator=" "):
    """Append dayReportLines() to the prompt the player is about to be shown.

    separator is the gap placed before each line. It defaults to one space,
    which is what a location uses when the line continues a sentence it just
    wrote ("You sleep until the next morning. ..."). FishE's game loop passes
    two, because there the day's news is being appended to whatever a
    completely different subsystem already put on the screen."""
    for line in dayReportLines(summary):
        prompt.text += separator + line
