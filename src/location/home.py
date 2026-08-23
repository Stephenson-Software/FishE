from location.enum.locationType import LocationType
from player.player import Player
from prompt.prompt import Prompt
from world.timeService import TimeService, appendDayReport
from stats.stats import Stats
from ui.userInterface import UserInterface
from achievements import achievements
from housing import housing
from progression import progression


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
        # Sleeping is all home is for at first; the ledger and the housing
        # ladder are revealed later (see src/progression), and retiring only
        # once the wealth goal has been reached - so options and actions are
        # built as a pair rather than dispatched on a fixed number.
        li = ["Sleep"]
        actions = ["sleep"]
        if progression.isUnlocked(self.stats, progression.JOURNAL):
            li.append("See Stats")
            actions.append("stats")
        if progression.isUnlocked(self.stats, progression.HOUSING):
            li.append("Manage Home")
            actions.append("housing")
        li.append("Go to Docks")
        actions.append("docks")
        if achievements.GOAL_MILESTONE_NAME in self.stats.earnedMilestones:
            li.append("Retire")
            actions.append("retire")
        li.append("Quit")
        actions.append("quit")

        self.input = self.userInterface.showOptions(self._homeDescriptor(), li)
        action = actions[int(self.input) - 1]

        if action == "sleep":
            self.sleep()
            return LocationType.HOME
        elif action == "stats":
            self.displayStats()
            self.currentPrompt.text = "What would you like to do?"
            return LocationType.HOME
        elif action == "housing":
            self.manageHome()
            return LocationType.HOME
        elif action == "docks":
            self.currentPrompt.text = "What would you like to do?"
            return LocationType.DOCKS
        elif action == "retire":
            self.retire()
            return LocationType.NONE
        elif action == "quit":
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
        # What the fleet did overnight, so a crew lost or a hull damaged is
        # news the player is told rather than something they discover later.
        appendDayReport(self.currentPrompt, summary)

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
            unavailable = {}
            for targetTier, targetInfo, netCost in self._availableMoves():
                options.append(self._moveLabel(tier, targetTier, targetInfo, netCost))
                actions.append(("move", targetTier))
                # Moving down pays out and is always possible; only a move that
                # costs money can be out of reach (see housing.moveHome).
                if netCost > 0 and not self.player.canAfford(netCost):
                    unavailable[len(options)] = "not enough money"
            options.append("Back")
            actions.append(("back", None))

            choice = int(
                self.userInterface.showOptions(
                    self._housingStatus(), options, unavailable
                )
            )
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

    def _careerBlock(self, heading, entries):
        """A headed block of the ledger, built from (label, value, format)
        entries.

        A zero entry is left out and a block with nothing left in it is dropped
        altogether, so the ledger only ever names the parts of the game the
        player has actually played - the same way the business and investment
        blocks only appear once there is something to say."""
        block = [
            "%s: %s" % (label, valueFormat % value)
            for label, value, valueFormat in entries
            if value
        ]
        if not block:
            return []
        return ["", heading] + block

    def _statsLines(self):
        lines = [
            "Total Fish Caught: %d" % self.stats.totalFishCaught,
            # Exports pay a fractional multiplier (see business/export.py), so
            # lifetime earnings are a float and whole dollars would drop the
            # cents the status header shows.
            "Total Money Made: %.2f" % self.stats.totalMoneyMade,
            "Hours Spent Fishing: %d" % self.stats.hoursSpentFishing,
            "Money Made From Interest: %d" % self.stats.moneyMadeFromInterest,
            "Times Gotten Drunk: %d" % self.stats.timesGottenDrunk,
            "Money Lost Gambling: %d" % self.stats.moneyLostFromGambling,
        ]
        if self.stats.moneyLostWhileDrunk:
            lines.append("Money Lost While Drunk: %d" % self.stats.moneyLostWhileDrunk)
        homeTier = housing.currentTier(self.player)
        homeInfo = housing.tierInfo(homeTier)
        lines += [
            "",
            "Home: %s" % homeInfo["name"],
        ]
        if self.stats.totalRentPaid:
            lines.append("Lifetime Rent Paid: %d" % self.stats.totalRentPaid)
        # Gated on ever having run a business, not on owning a boat today: the
        # wage bill below is what the Fleet block's takings were earned against,
        # and showing one without the other would flatter a sold-off fleet.
        if self.player.hasBoat or self.stats.daysInBusiness:
            lines += [
                "",
                "Business: %s" % (self.player.businessName or "Unnamed Fishing Co."),
                "Days in Business: %d" % self.stats.daysInBusiness,
                "Crew Hired (lifetime): %d" % self.stats.totalWorkersHired,
                "Fish Caught by Crew: %d" % self.stats.totalFishCaughtByCrew,
                "Wages Paid: %d" % self.stats.totalWagesPaid,
            ]
        # What the boats did, and what shipping the surplus out was worth.
        # Both are gated on the lifetime totals rather than on what the player
        # owns today, so a career that ended in a sold-off fleet still shows
        # the fleet's record.
        lines += self._careerBlock(
            "Fleet:",
            [
                ("Boats Owned (lifetime)", self.stats.boatsOwned, "%d"),
                # Every role's takings together - the fleet's own working days
                # and the voyages the player captained (see stats.Stats).
                ("Money From Boat Work", self.stats.totalMoneyFromVoyages, "%d"),
                ("Freight Days Run", self.stats.totalHaulingContracts, "%d"),
                ("Passenger Runs", self.stats.totalTransportRuns, "%d"),
                ("Days Spent Raiding", self.stats.totalRaids, "%d"),
                ("Plunder Taken", self.stats.totalPlunder, "%d"),
                ("Voyages Captained", self.stats.totalVoyagesCaptained, "%d"),
                ("Voyages Foundered", self.stats.totalVoyagesFoundered, "%d"),
                ("Crew Lost at Sea", self.stats.crewLostToPiracy, "%d"),
            ],
        )
        lines += self._careerBlock(
            "Exports:",
            [
                ("Fish Exported", self.stats.totalFishExported, "%d"),
                # Gross, before the freight below - the same way Total Money
                # Made counts gross sales (see stats.Stats). Fractional,
                # because a market pays a multiplier of the village price.
                ("Money From Exports", self.stats.totalMoneyFromExports, "%.2f"),
                ("Freight Paid", self.stats.totalShippingPaid, "%d"),
            ],
        )
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
