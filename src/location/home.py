from location.enum.locationType import LocationType
from player.player import Player
from prompt.prompt import Prompt
from world.timeService import TimeService
from stats.stats import Stats
from ui.userInterface import UserInterface
from achievements import achievements
from housing import housing


# @author Daniel McCoy Stephenson
class Home:
    def __init__(
        self,
        userInterface: UserInterface,
        currentPrompt: Prompt,
        player: Player,
        stats: Stats,
        timeService: TimeService,
    ):
        self.userInterface = userInterface
        self.currentPrompt = currentPrompt
        self.player = player
        self.stats = stats
        self.timeService = timeService

    def run(self):
        retireAvailable = (
            achievements.GOAL_MILESTONE_NAME in self.stats.earnedMilestones
        )
        li = ["Sleep", "See Stats", "Manage Home", "Go to Docks"]
        if retireAvailable:
            li.append("Retire")
        li.append("Quit")
        self.input = self.userInterface.showOptions(self._homeDescriptor(), li)

        if self.input == "1":
            self.sleep()
            return LocationType.HOME
        elif self.input == "2":
            self.displayStats()
            self.currentPrompt.text = "What would you like to do?"
            return LocationType.HOME
        elif self.input == "3":
            self.manageHome()
            return LocationType.HOME
        elif self.input == "4":
            self.currentPrompt.text = "What would you like to do?"
            return LocationType.DOCKS
        elif retireAvailable and self.input == "5":
            self.retire()
            return LocationType.NONE
        elif self.input == str(len(li)):
            return LocationType.NONE

    def _homeDescriptor(self):
        status = housing.tierInfo(housing.currentTier(self.player))["status"]
        if status == "homeless":
            return "You have nowhere to stay tonight."
        if status == "renting":
            return "You sit in your rented room, polishing one of your prized fishing poles."
        return "You sit at home, polishing one of your prized fishing poles."

    def sleep(self):
        summary = self.timeService.increaseDay()
        self.player.energy = housing.maxEnergy(self.player)  # Restore full energy
        self.currentPrompt.text = (
            "You sleep until the next morning. You feel refreshed!"
        )
        if summary["evicted"]:
            self.currentPrompt.text += " " + housing.EVICTION_MESSAGE

    def _moveCostLabel(self, netCost):
        if netCost > 0:
            return "$%d net" % netCost
        if netCost < 0:
            return "get $%d back" % -netCost
        return "free"

    def _availableMoves(self):
        """(targetTier, targetInfo, netCost) for each adjacent rung the
        player can move to (up and/or down), computed once so
        _housingStatus() and manageHome() don't each redo the same lookups
        on every render."""
        tier = housing.currentTier(self.player)
        moves = []
        if tier < len(housing.HOUSING_TIERS) - 1:
            moves.append((tier + 1, housing.tierInfo(tier + 1)))
        if tier > 0:
            moves.append((tier - 1, housing.tierInfo(tier - 1)))
        return [
            (targetTier, info, housing.netCostToMove(self.player, targetTier))
            for targetTier, info in moves
        ]

    def _moveLabel(self, currentTier, targetTier, info, netCost):
        # Disclose a recurring rent obligation up front, not just after the
        # player has already moved in and checked the status screen again.
        costLabel = self._moveCostLabel(netCost)
        if info["status"] == "renting":
            costLabel += ", then $%d/day rent" % info["dailyRent"]
        verb = "Move to" if targetTier > currentTier else "Move down to"
        return "%s %s (%s)" % (verb, info["name"], costLabel)

    def _housingStatus(self):
        tier = housing.currentTier(self.player)
        info = housing.tierInfo(tier)
        if info["status"] == "homeless":
            lines = [
                "Homeless. Energy cap: %d. No rent to pay, but no comfort "
                "either." % info["maxEnergy"]
            ]
        elif info["status"] == "renting":
            lines = [
                "Renting a room. Energy cap: %d. Rent: $%d/day, charged "
                "automatically each morning - miss a payment and you're "
                "back on the street." % (info["maxEnergy"], info["dailyRent"])
            ]
        else:
            lines = [
                "You own a %s. Energy cap: %d." % (info["name"], info["maxEnergy"])
            ]

        for targetTier, targetInfo, netCost in self._availableMoves():
            lines.append(
                "%s, energy cap %d."
                % (
                    self._moveLabel(tier, targetTier, targetInfo, netCost),
                    targetInfo["maxEnergy"],
                )
            )
        return "\n".join(lines)

    def manageHome(self):
        while True:
            tier = housing.currentTier(self.player)
            options = []
            actions = []
            for targetTier, targetInfo, netCost in self._availableMoves():
                options.append(self._moveLabel(tier, targetTier, targetInfo, netCost))
                actions.append(("move", targetTier))
            options.append("Back")
            actions.append(("back", None))

            choice = int(self.userInterface.showOptions(self._housingStatus(), options))
            action, targetTier = actions[choice - 1]

            if action == "move":
                if housing.moveHome(self.player, targetTier, self.stats):
                    self.currentPrompt.text = (
                        "You moved to %s!" % housing.tierInfo(targetTier)["name"]
                    )
                else:
                    self.currentPrompt.text = "You can't afford that move yet."
            elif action == "back":
                self.currentPrompt.text = "What would you like to do?"
                return

    def _statsLines(self):
        lines = [
            "Total Fish Caught: %d" % self.stats.totalFishCaught,
            "Total Money Made: %d" % self.stats.totalMoneyMade,
            "Hours Spent Fishing: %d" % self.stats.hoursSpentFishing,
            "Money Made From Interest: %d" % self.stats.moneyMadeFromInterest,
            "Times Gotten Drunk: %d" % self.stats.timesGottenDrunk,
            "Money Lost Gambling: %d" % self.stats.moneyLostFromGambling,
        ]
        homeTier = housing.currentTier(self.player)
        homeInfo = housing.tierInfo(homeTier)
        lines += [
            "",
            "Home: %s" % homeInfo["name"],
        ]
        if self.stats.totalRentPaid:
            lines.append("Lifetime Rent Paid: %d" % self.stats.totalRentPaid)
        if self.player.hasBoat:
            lines += [
                "",
                "Business: %s" % (self.player.businessName or "Unnamed Fishing Co."),
                "Days in Business: %d" % self.stats.daysInBusiness,
                "Crew Hired (lifetime): %d" % self.stats.totalWorkersHired,
                "Fish Caught by Crew: %d" % self.stats.totalFishCaughtByCrew,
                "Wages Paid: %d" % self.stats.totalWagesPaid,
            ]
        if self.player.rentalProperties:
            lines += [
                "",
                "Investment Properties: %d owned" % len(self.player.rentalProperties),
                "Lifetime Rental Income: %d" % self.stats.totalRentalIncome,
            ]
        lines += [
            "",
            "Milestones:",
        ]
        for milestone, earned in achievements.getMilestoneStatuses(self.stats):
            mark = "x" if earned else " "
            lines.append(
                " [%s] %s - %s" % (mark, milestone["name"], milestone["description"])
            )
        return lines

    def displayStats(self):
        # Render through the active front-end (and wait for acknowledgement) so the
        # stats screen works in any UI rather than only the console.
        self.userInterface.showDialogue("\n".join(self._statsLines()))

    def retire(self):
        """Show a closing summary and end the run, reusing displayStats()'s lines."""
        lines = [
            "You retire from fishing, your fortune secured for good.",
            "Here's how your career adds up:",
            "",
        ] + self._statsLines()
        self.userInterface.showDialogue("\n".join(lines))
