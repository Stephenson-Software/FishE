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
        li = ["Sleep", "See Stats", "Manage Home", "Go to Docks", "Quit"]
        self.input = self.userInterface.showOptions(
            "You sit at home, polishing one of your prized fishing poles.", li
        )

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
        elif self.input == "5":
            return LocationType.NONE

    def sleep(self):
        self.timeService.increaseDay()
        self.player.energy = housing.maxEnergy(self.player)  # Restore full energy
        self.currentPrompt.text = (
            "You sleep until the next morning. You feel refreshed!"
        )

    def _housingStatus(self):
        tier = housing.currentTier(self.player)
        info = housing.tierInfo(tier)
        lines = [
            "%s (tier %d/%d)" % (info["name"], tier, len(housing.HOUSING_TIERS)),
            "Energy cap: %d." % info["maxEnergy"],
        ]
        if tier < len(housing.HOUSING_TIERS):
            nextInfo = housing.tierInfo(tier + 1)
            netCost = housing.netCostToMove(self.player, tier + 1)
            lines.append(
                "Move to a %s for $%d net (energy cap %d): you'll sell your "
                "%s and put the proceeds toward the new place."
                % (nextInfo["name"], netCost, nextInfo["maxEnergy"], info["name"])
            )
        if tier > 1:
            prevInfo = housing.tierInfo(tier - 1)
            netCost = housing.netCostToMove(self.player, tier - 1)
            lines.append(
                "Move down to a %s (energy cap %d): %s."
                % (
                    prevInfo["name"],
                    prevInfo["maxEnergy"],
                    (
                        "you'll pocket $%d" % -netCost
                        if netCost <= 0
                        else "costs $%d net" % netCost
                    ),
                )
            )
        return "\n".join(lines)

    def manageHome(self):
        while True:
            tier = housing.currentTier(self.player)
            options = []
            actions = []
            if tier < len(housing.HOUSING_TIERS):
                nextInfo = housing.tierInfo(tier + 1)
                netCost = housing.netCostToMove(self.player, tier + 1)
                options.append("Move to a %s ($%d net)" % (nextInfo["name"], netCost))
                actions.append(("move", tier + 1))
            if tier > 1:
                prevInfo = housing.tierInfo(tier - 1)
                netCost = housing.netCostToMove(self.player, tier - 1)
                label = "+$%d" % -netCost if netCost <= 0 else "$%d net" % netCost
                options.append("Move down to a %s (%s)" % (prevInfo["name"], label))
                actions.append(("move", tier - 1))
            options.append("Back")
            actions.append(("back", None))

            choice = int(self.userInterface.showOptions(self._housingStatus(), options))
            action, targetTier = actions[choice - 1]

            if action == "move":
                if housing.moveHome(self.player, targetTier, self.stats):
                    self.currentPrompt.text = (
                        "You moved into a %s!" % housing.tierInfo(targetTier)["name"]
                    )
                else:
                    self.currentPrompt.text = "You can't afford that move yet."
            elif action == "back":
                self.currentPrompt.text = "What would you like to do?"
                return

    def displayStats(self):
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
            "Home: %s (tier %d/%d)"
            % (homeInfo["name"], homeTier, len(housing.HOUSING_TIERS)),
        ]
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
        # Render through the active front-end (and wait for acknowledgement) so the
        # stats screen works in any UI rather than only the console.
        self.userInterface.showDialogue("\n".join(lines))
