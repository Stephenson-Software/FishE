import random

from location.enum.locationType import LocationType
from player.player import Player
from prompt.prompt import Prompt
from world.timeService import TimeService, appendDayReport, dayReportLines
from stats.stats import Stats
from ui.userInterface import UserInterface
from npc.npc import NPC
from npc import villagers
from fish import fish
from business import business
from business import boats
from business import export
from business import adventures
from progression import progression


# The catch reaction window widens with the player's rod level, so a better rod
# (bought at the shop) makes the timing minigame more forgiving. Level 1 keeps
# the original 2.0s window.
REACTION_BASE_WINDOW = 2.0
ROD_WINDOW_STEP = 0.5

# Energy spent per hour of fishing, and so the minimum needed to cast at all.
FISHING_ENERGY_COST = 10


# @author Daniel McCoy Stephenson
class Docks:
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
        self.npc = NPC(
            "Sam the Dock Worker",
            "Been working these docks since I was knee-high to a grasshopper. "
            "My pa was a fisherman, and his pa before him. I help maintain the boats and docks, "
            "and I've learned a thing or two about fishing over the years. "
            "The sea provides for those who respect her!",
            [
                {
                    "question": "Tell me about yourself.",
                    "response": "Been working these docks since I was knee-high to a grasshopper. "
                    "My pa was a fisherman, and his pa before him. I help maintain the boats and docks, "
                    "and I've learned a thing or two about fishing over the years. "
                    "The sea provides for those who respect her!",
                },
                {
                    "question": "How do I fish at the docks?",
                    "response": self._howToFishDialogue,
                },
                {
                    "question": "What other locations can I visit?",
                    "response": self._locationsDialogue,
                },
                {
                    "question": "Tell me about energy and rest.",
                    "response": "Energy is your lifeblood as a fisherman! You start each day with it, "
                    "and fishing uses it up - 10 energy per hour of fishing. "
                    "When you're running low, head home and sleep. That'll restore you for the next day. "
                    "The game keeps track of time - each action moves the clock forward. "
                    "Plan your day wisely!",
                },
                {
                    "question": "What makes a good fisherman?",
                    "response": "Patience and quick reflexes! When that fish bites, you gotta be ready. "
                    "Invest in better bait from Gilbert - it makes a huge difference. "
                    "Fish when you have energy, sell regularly, and save your money. "
                    "The sea has its rhythms - you'll learn them in time. "
                    "And remember: it's not just about catching fish, it's about enjoying the life!",
                },
                {
                    "question": "How's my fishing business doing?",
                    "response": self._businessDialogue,
                },
                {
                    # Sam only has villagers to gossip about once you've hired
                    # some - see NPC.get_dialogue_options.
                    "question": "What do you make of the crew I hired?",
                    "response": self._crewDialogue,
                    "condition": lambda: bool(self.player.hiredWorkers),
                },
            ],
        )

    def run(self):
        # Options and actions are built as a pair - rather than dispatching on
        # a hardcoded number - because almost every entry only appears once the
        # player has earned it, and the menu positions below it would otherwise
        # shift depending on game state.
        #
        # Fishing is the one thing a brand new player can do, and everything
        # else arrives in the order src/progression reveals it, appended at the
        # bottom - so an option the player already knows keeps its number when
        # a new one shows up. Quit stays last.
        li = ["Fish"]
        actions = ["fish"]
        # Fishing is the one option here the player can be blocked from, and
        # running out of energy is the commonest way a day ends - so say so on
        # the option itself rather than only after they've picked it.
        unavailable = {}
        if not self.player.hasEnergy(FISHING_ENERGY_COST):
            unavailable[len(li)] = (
                "needs %d energy - sleep at home" % FISHING_ENERGY_COST
            )
        for feature, label, action in (
            (progression.SHOP, "Go to Shop", "shop"),
            (progression.HOME, "Go Home", "home"),
            (progression.TALK, "Talk to %s" % self.npc.name, "talk"),
            (progression.BANK, "Go to Bank", "bank"),
            (progression.FLEET, "Manage Fleet", "manage"),
            (progression.TAVERN, "Go to Tavern", "tavern"),
        ):
            if progression.isUnlocked(self.stats, feature):
                li.append(label)
                actions.append(action)
        if self.player.hiredWorkers:
            li.append("Talk to Your Crew")
            actions.append("talk_crew")
        if export.canExport(self.player):
            li.append("Export Fish to Other Villages")
            actions.append("export")
        if self.readyToSail():
            li.append("Take the Helm")
            actions.append("voyage")
        # The docks are where the game starts and where a player with nothing
        # unlocked yet spends their first few casts, so the way out of the game
        # lives here as well as at home - otherwise a new player would have no
        # way to stop before they've earned one.
        li.append("Quit")
        actions.append("quit")
        if self.player.hasBoat and self.player.businessName:
            descriptor = (
                "%s is docked and ready for the day." % self.player.businessName
            )
        else:
            descriptor = "You breathe in the fresh air. Salty."
        descriptor += " " + self._weatherDescriptor()
        # Anything wrong with the fleet is said here, on the screen the player
        # is already on. Before this it could only be found by opening Manage
        # Fleet and reading every line - a boat could sit idle for days.
        notices = boats.needsAttention(self.player)
        if notices:
            descriptor += "\n\nNeeds attention: " + "; ".join(notices) + "."
        input = self.userInterface.showOptions(descriptor, li, unavailable)

        choice = int(input)
        action = actions[choice - 1]

        if action == "fish":
            if self.player.hasEnergy(FISHING_ENERGY_COST):
                self.fish()
                return LocationType.DOCKS
            else:
                self.currentPrompt.text = "You're too tired to fish! Go home and sleep."
                return LocationType.DOCKS

        elif action == "talk":
            self.talkToNPC()
            return LocationType.DOCKS

        elif action == "home":
            self.currentPrompt.text = "What would you like to do?"
            return LocationType.HOME

        elif action == "shop":
            self.currentPrompt.text = "What would you like to do?"
            return LocationType.SHOP

        elif action == "tavern":
            self.currentPrompt.text = "What would you like to do?"
            return LocationType.TAVERN

        elif action == "bank":
            self.currentPrompt.text = (
                "What would you like to do? Money in Bank: $%.2f"
                % self.player.moneyInBank
            )
            return LocationType.BANK

        elif action == "manage":
            self.manageFleet()
            return LocationType.DOCKS

        elif action == "talk_crew":
            self.talkToCrew()
            return LocationType.DOCKS

        elif action == "export":
            self.exportFish()
            return LocationType.DOCKS

        elif action == "voyage":
            self.takeTheHelm()
            return LocationType.DOCKS

        elif action == "quit":
            return LocationType.NONE

    def _howToFishDialogue(self):
        """Sam's explanation of the catch timing minigame, quoting the
        player's actual reaction window - it widens with rod level, bought
        at the shop (#145)."""
        window = REACTION_BASE_WINDOW + (self.player.rodLevel - 1) * ROD_WINDOW_STEP
        return (
            "Fishing is what this village is all about! You need at least 10 energy to fish. "
            "When you cast your line, you'll spend several random hours (1-10) fishing. "
            "Each hour uses 10 energy. When a fish bites, press Enter fast - you've got "
            "about %.1f seconds right now, and a better rod widens that window. "
            "React slower and you'll still catch something, just less of it. "
            "The more successful catches, the more fish you'll get. "
            "Don't worry if you miss a few - you'll still catch at least one fish if you tried!"
            % window
        )

    def _locationsDialogue(self):
        """Sam's tour of the village - only the parts of it the player has
        found so far (see src/progression). Listing the bank to someone who
        has never sold a fish would hand back exactly the wall of options the
        staged reveal exists to avoid, and Sam pointing at a door that isn't
        on the menu yet would just be confusing."""
        places = []
        if progression.isUnlocked(self.stats, progression.HOME):
            places.append("there's your home, where you sleep to restore energy")
        if progression.isUnlocked(self.stats, progression.SHOP):
            places.append("Gilbert's shop is where you sell fish and buy better gear")
        if progression.isUnlocked(self.stats, progression.TAVERN):
            places.append("the tavern is run by Old Tom - gambling and drinks there")
        if progression.isUnlocked(self.stats, progression.BANK):
            places.append(
                "the bank is where Margaret keeps your money safe, and even "
                "pays you interest"
            )
        if not places:
            return (
                "Nowhere yet, far as you're concerned! Wet your line first - "
                "the village opens up to a fisherman who's actually fishing."
            )
        text = "Well, %s." % villagers.joinNames(places)
        if len(places) < 4:
            text += (
                " There's more to this village besides, but you'll come to it "
                "in your own time."
            )
        return text

    def _businessDialogue(self):
        """Sam's take on the player's fishing business, staged by boat tier and
        crew size so it reflects real progress rather than being fixed text."""
        if not self.player.hasBoat:
            return (
                "No boat yet, eh? Once you've got one, I can help you find "
                "good hands to hire. A crew changes everything!"
            )
        if self.player.workers == 0:
            starter = business.tierInfo(business.currentTier(self.player))
            return (
                "A %s of your own! Now you just need to hire a crew to get "
                "it earning." % starter["name"]
            )
        tier = business.currentTier(self.player)
        name = self.player.businessName or "your business"
        if tier == 1:
            return (
                "%s is off to a solid start with that Rowboat crew. Save up "
                "and you could afford a bigger boat before long." % name
            )
        if tier == 2:
            return (
                "A Trawler! %s is really coming along. I've seen a lot of "
                "fishermen never make it past a rowboat." % name
            )
        return (
            "A whole Fishing Fleet under %s? You're the talk of the docks! "
            "Never thought I'd see an outfit like that around here." % name
        )

    def _crewDialogue(self):
        """Sam's read on the specific villagers aboard - he grew up with all of
        them, so hiring anyone gives him something new to say."""
        described = []
        for name in self.player.hiredWorkers:
            villager = villagers.getVillager(name)
            if villager is None:
                described.append(name)
            else:
                described.append("%s on %s" % (name, villager["specialty"]))
        text = (
            "You've got %s. I've known every one of 'em since they were "
            "knee-high - you picked well." % villagers.joinNames(described)
        )
        unnamed = self.player.workers - len(self.player.hiredWorkers)
        if unnamed > 0:
            text += " And %d hand%s besides, whose name I never did catch." % (
                unnamed,
                "s" if unnamed != 1 else "",
            )
        return text

    def talkToCrew(self):
        """Pick a hired villager to talk to. Their conversation is separate
        from the village NPCs' - see villagers.createCrewNPC."""
        while True:
            options = list(self.player.hiredWorkers)
            options.append("Back")
            choice = int(
                self.userInterface.showOptions(
                    "Your crew are working the boat. Who do you want a word with?",
                    options,
                )
            )
            if choice == len(options):
                self.currentPrompt.text = "What would you like to do?"
                return
            name = self.player.hiredWorkers[choice - 1]
            self.userInterface.showInteractiveDialogue(
                villagers.createCrewNPC(self.player, name)
            )

    def _fleetStatus(self):
        """The fleet at a glance: every boat, what it's for, who's on it, and
        who's drawing wages without a berth."""
        if not self.player.boats:
            starter = business.tierInfo(1)
            return (
                "You have no boats. A boat lets you hire a crew and dedicate "
                "her to a trade - fishing, hauling, piracy or transport. A %s "
                "costs $%d." % (starter["name"], starter["cost"])
            )
        name = self.player.businessName or "Unnamed Fishing Co."
        # Lead with the one number that decides everything else: is the fleet
        # paying for itself? Before this the player had to multiply the crew
        # count by the wage in their head and compare it to nothing.
        income = boats.fleetDailyIncome(self.player)
        catch = boats.fleetDailyCatch(self.player)
        payroll = boats.dailyPayroll(self.player)
        earning = "$%d" % income
        if catch:
            earning += " and %d fish" % catch
        lines = [
            "%s - %d boat%s, %d crew"
            % (
                name,
                len(self.player.boats),
                "s" if len(self.player.boats) != 1 else "",
                self.player.workers,
            ),
            "Earning %s a day. Payroll $%d a day. Net $%d%s."
            % (
                earning,
                payroll,
                income - payroll,
                " plus the fish" if catch else "",
            ),
            "",
        ]
        for boat in self.player.boats:
            lines.append("  " + boats.describeBoat(boat))
        idle = boats.unassignedNames(self.player)
        idleHands = boats.unassignedHands(self.player)
        if idle or idleHands:
            spare = list(idle) + (
                ["%d unnamed hand(s)" % idleHands] if idleHands else []
            )
            lines.append(
                "Ashore on full wages, earning nothing: %s" % villagers.joinNames(spare)
            )
        return "\n".join(lines)

    def manageFleet(self):
        while True:
            options = []
            actions = []

            unavailable = {}

            starter = business.tierInfo(1)
            options.append("Buy a %s ($%d)" % (starter["name"], starter["cost"]))
            actions.append("buy_boat")
            if not self.player.canAfford(starter["cost"]):
                unavailable[len(options)] = "not enough money"

            if self.player.boats:
                berths = boats.totalCrewBerths(self.player)
                if self.player.workers < berths:
                    options.append(
                        "Hire a Villager ($%d/day)" % business.WORKER_DAILY_WAGE
                    )
                    actions.append("hire")
                if self.player.workers > 0:
                    options.append("Dismiss a Worker")
                    actions.append("dismiss")
                    options.append("Assign Crew to a Boat")
                    actions.append("assign")
                options.append("Change a Boat's Role")
                actions.append("role")
                if any(boat["damage"] > 0 for boat in self.player.boats):
                    options.append("Repair a Boat")
                    actions.append("repair")
                if any(
                    boat["tier"] < len(business.BOAT_TIERS)
                    for boat in self.player.boats
                ):
                    options.append("Upgrade a Boat")
                    actions.append("upgrade_boat")
                options.append("Rename a Boat")
                actions.append("rename_boat")
                options.append("Sell a Boat")
                actions.append("sell_boat")
                options.append("Rename Business")
                actions.append("rename")
            options.append("Back")
            actions.append("back")

            choice = int(
                self.userInterface.showOptions(
                    self._fleetStatus(), options, unavailable
                )
            )
            action = actions[choice - 1]

            if action == "buy_boat":
                self._buyBoat()
            elif action == "hire":
                self._hireVillager()
            elif action == "dismiss":
                self._dismissWorker()
            elif action == "assign":
                self._assignCrew()
            elif action == "role":
                self._changeRole()
            elif action == "repair":
                self._repairBoat()
            elif action == "upgrade_boat":
                self._upgradeBoat()
            elif action == "rename_boat":
                self._renameBoat()
            elif action == "sell_boat":
                self._sellBoat()
            elif action == "rename":
                self._renameBusiness()
            elif action == "back":
                self.currentPrompt.text = "What would you like to do?"
                return

    def _pickBoat(self, prompt, candidates=None, unavailable=None):
        """Shared boat chooser. Returns the boat, or None if the player backed
        out - every fleet action needs one and they should all read the same.

        unavailable maps a 1-based position in candidates to the reason that
        boat can't be chosen (an unaffordable repair bill, say), so the ones
        the player can't act on are greyed out rather than picked and refused.
        "Back" is appended last and is never marked."""
        candidates = self.player.boats if candidates is None else candidates
        if not candidates:
            return None
        options = [boats.describeBoat(boat) for boat in candidates]
        options.append("Back")
        choice = int(self.userInterface.showOptions(prompt, options, unavailable))
        if choice == len(options):
            return None
        return candidates[choice - 1]

    def _buyBoat(self):
        starter = business.tierInfo(1)
        if not self.player.canAfford(starter["cost"]):
            self.currentPrompt.text = (
                "A %s costs $%d and you're carrying $%.2f. Sell some fish "
                "first." % (starter["name"], starter["cost"], self.player.money)
            )
            return
        self.player.spendMoney(starter["cost"])
        boat = boats.addBoat(self.player, 1)
        self.stats.boatsOwned += 1
        self.currentPrompt.text = (
            "You bought a %s. She's a fishing boat for now - crew her up, or "
            "change her role to put her to other work." % starter["name"]
        )
        self._renameBoatPrompt(boat, firstTime=True)

    def _changeRole(self):
        boat = self._pickBoat("Which boat are you re-dedicating?")
        if boat is None:
            return
        options = []
        for role in boats.ROLE_ORDER:
            marker = " (current)" if role == boat["role"] else ""
            options.append(
                "%s - %s%s"
                % (boats.ROLES[role]["name"], boats.ROLES[role]["summary"], marker)
            )
        options.append("Back")
        choice = int(
            self.userInterface.showOptions(
                "What should %s be doing?\n\n%s"
                % (
                    boat["name"],
                    "\n".join(
                        "%s: %s" % (boats.ROLES[r]["name"], boats.ROLES[r]["detail"])
                        for r in boats.ROLE_ORDER
                    ),
                ),
                options,
            )
        )
        if choice == len(options):
            return
        role = boats.ROLE_ORDER[choice - 1]
        boats.setRole(self.player, boat["id"], role)
        self.currentPrompt.text = "%s is now a %s boat." % (
            boat["name"],
            boats.ROLES[role]["name"].lower(),
        )

    def _assignCrew(self):
        boat = self._pickBoat("Which boat are you crewing?")
        if boat is None:
            return
        while True:
            options = []
            actions = []
            for name in boat["crew"]:
                options.append("Take %s off %s" % (name, boat["name"]))
                actions.append(("off", name))
            if boat["hands"] > 0:
                options.append("Take an unnamed hand off %s" % boat["name"])
                actions.append(("off_hand", None))
            if boats.hasRoom(boat):
                for name in boats.unassignedNames(self.player):
                    options.append("Put %s aboard" % name)
                    actions.append(("on", name))
                if boats.unassignedHands(self.player) > 0:
                    options.append("Put an unnamed hand aboard")
                    actions.append(("on_hand", None))
            options.append("Back")
            actions.append(("back", None))

            choice = int(
                self.userInterface.showOptions(
                    "%s\n%s"
                    % (
                        boats.describeBoat(boat),
                        "Her berths are full."
                        if not boats.hasRoom(boat)
                        else "%d berth(s) free."
                        % (boats.maxCrew(boat) - boats.crewSize(boat)),
                    ),
                    options,
                )
            )
            action, name = actions[choice - 1]
            if action == "back":
                return
            if action == "on":
                boats.assignCrew(self.player, boat["id"], name)
                self.currentPrompt.text = "%s joined %s." % (name, boat["name"])
            elif action == "off":
                boats.unassignCrew(self.player, boat["id"], name)
                self.currentPrompt.text = "%s came ashore off %s." % (
                    name,
                    boat["name"],
                )
            elif action == "on_hand":
                boats.assignHand(self.player, boat["id"])
                self.currentPrompt.text = "A hand joined %s." % boat["name"]
            elif action == "off_hand":
                boats.unassignHand(self.player, boat["id"])
                self.currentPrompt.text = "A hand came ashore off %s." % boat["name"]

    def _repairBoat(self):
        damaged = [boat for boat in self.player.boats if boat["damage"] > 0]
        # Each hull has its own bill, so which ones are out of reach depends on
        # the boat rather than on the menu as a whole.
        unaffordable = {
            index + 1: "repair costs $%d" % boats.repairCost(boat)
            for index, boat in enumerate(damaged)
            if not self.player.canAfford(boats.repairCost(boat))
        }
        boat = self._pickBoat("Which boat needs work?", damaged, unaffordable)
        if boat is None:
            return
        cost = boats.repairCost(boat)
        paid = boats.repairBoat(self.player, boat["id"])
        if paid is None:
            self.currentPrompt.text = (
                "Patching %s up costs $%d and you're carrying $%.2f. Sell fish "
                "at the shop, or send another boat out, and come back to her - "
                "she'll keep." % (boat["name"], cost, self.player.money)
            )
            return
        self.currentPrompt.text = "%s is sound again. The yard took $%d." % (
            boat["name"],
            paid,
        )

    def _upgradeBoat(self):
        upgradable = [
            boat
            for boat in self.player.boats
            if boat["tier"] < len(business.BOAT_TIERS)
        ]
        unaffordable = {
            index + 1: "upgrade costs $%d" % business.tierInfo(boat["tier"] + 1)["cost"]
            for index, boat in enumerate(upgradable)
            if not self.player.canAfford(business.tierInfo(boat["tier"] + 1)["cost"])
        }
        boat = self._pickBoat("Which boat are you upgrading?", upgradable, unaffordable)
        if boat is None:
            return
        nextInfo = business.tierInfo(boat["tier"] + 1)
        if not self.player.canAfford(nextInfo["cost"]):
            self.currentPrompt.text = "A %s costs $%d and you're carrying $%.2f." % (
                nextInfo["name"],
                nextInfo["cost"],
                self.player.money,
            )
            return
        self.player.spendMoney(nextInfo["cost"])
        boat["tier"] += 1
        self.currentPrompt.text = "%s is now a %s." % (boat["name"], nextInfo["name"])

    def _renameBoat(self):
        boat = self._pickBoat("Which boat are you renaming?")
        if boat is None:
            return
        self._renameBoatPrompt(boat)

    def _renameBoatPrompt(self, boat, firstTime=False):
        name = self.userInterface.promptForText(
            "What will you call her?" if firstTime else "What's her new name?"
        )
        name = (name or "").strip()[:40]
        if name:
            boat["name"] = name
            self.currentPrompt.text += " She's the %s." % name

    def _sellBoat(self):
        boat = self._pickBoat("Which boat are you selling?")
        if boat is None:
            return
        crew = list(boat["crew"])
        value = boats.sellBoat(self.player, boat["id"])
        self.currentPrompt.text = "You sold %s for $%d." % (boat["name"], value)
        if crew:
            self.currentPrompt.text += (
                " %s came ashore - they're still on the payroll until you give "
                "them another berth or let them go." % villagers.joinNames(crew)
            )

    def _hireVillager(self):
        """Pick which villager joins the crew. Hiring is a choice of person
        rather than a headcount bump, so each hire opens up a conversation
        the player couldn't have before."""
        available = villagers.availableVillagers(self.player)
        if not available:
            self.currentPrompt.text = (
                "Nobody left in the village is looking for a berth right now."
            )
            return

        options = ["%s - %s" % (v["name"], v["blurb"]) for v in available]
        options.append("Back")
        choice = int(
            self.userInterface.showOptions(
                "Sam points out who's looking for work. Any hand you take on "
                "costs $%d a day in wages, whether or not you've found them a "
                "berth." % business.WORKER_DAILY_WAGE,
                options,
            )
        )
        if choice == len(options):
            return

        villager = available[choice - 1]
        if boats.hireWorker(self.player, villager["name"]):
            self.stats.totalWorkersHired += 1
            self.currentPrompt.text = (
                "You hired %s. Assign them to a boat to put them to work - "
                "they draw wages either way." % villager["name"]
            )
        else:
            self.currentPrompt.text = (
                "There's no free berth in the fleet for another hand. Buy "
                "another boat, or upgrade one you have."
            )

    def _dismissWorker(self):
        """Pick which hand leaves the crew. Unnamed hands from an older save
        are listed as a group, since there's no one in particular to name."""
        options = list(self.player.hiredWorkers)
        unnamed = self.player.workers - len(self.player.hiredWorkers)
        if unnamed > 0:
            options.append("An unnamed deckhand (%d aboard)" % unnamed)
        options.append("Back")

        choice = int(self.userInterface.showOptions("Who are you letting go?", options))
        if choice == len(options):
            return

        if choice <= len(self.player.hiredWorkers):
            name = self.player.hiredWorkers[choice - 1]
            boats.dismissWorker(self.player, name)
            self.currentPrompt.text = "You let %s go." % name
        else:
            boats.dismissWorker(self.player)
            self.currentPrompt.text = "You let an unnamed deckhand go."

    def readyToSail(self):
        """Boats the player could take the helm of: crewed, seaworthy, and not
        already away."""
        return [
            boat
            for boat in self.player.boats
            if boats.crewSize(boat) > 0
            and boats.isSeaworthy(boat)
            and not boats.isAtSea(boat)
        ]

    def takeTheHelm(self):
        """Sail one of your own boats yourself.

        The fleet earns on its own every morning; this is the part you play.
        Pick a boat, decide how far out to go, provision her, and then take
        her leg by leg."""
        ready = self.readyToSail()
        # Each line says what she currently brings in, because taking her out
        # is giving that up - an opportunity cost the player was being asked
        # to weigh without being shown.
        options = []
        for boat in ready:
            earning = (
                "%d fish/day" % boats.dailyCatch(boat)
                if boat["role"] == boats.ROLE_FISHING
                else "$%d/day" % boats.dailyIncome(boat)
            )
            options.append(
                "%s (%s) - %d crew, hull %d%%, gives up %s"
                % (
                    boat["name"],
                    boats.ROLES[boat["role"]]["name"],
                    boats.crewSize(boat),
                    boats.MAX_DAMAGE - boat["damage"],
                    earning,
                )
            )
        options.append("Back")

        descriptor = (
            "Which boat are you taking out yourself? She earns nothing at home "
            "while you have her - what you bring back is the point."
        )
        idle = [boat for boat in self.player.boats if boat not in ready]
        if idle:
            descriptor += "\n\nStaying in: " + "; ".join(
                self._cannotSailReason(boat) for boat in idle
            )

        choice = int(self.userInterface.showOptions(descriptor, options))
        if choice == len(options):
            self.currentPrompt.text = "What would you like to do?"
            return
        self._planVoyage(ready[choice - 1])

    def _cannotSailReason(self, boat):
        if boats.isAtSea(boat):
            return "%s is already at sea." % boat["name"]
        if boats.crewSize(boat) <= 0:
            return "%s has no crew aboard." % boat["name"]
        return "%s is too damaged to sail (%d%%); $%d to repair." % (
            boat["name"],
            boat["damage"],
            boats.repairCost(boat),
        )

    def _planVoyage(self, boat):
        """How far out to sail. Further is worth more and is less forgiving,
        which is the whole decision before you leave the harbour."""
        options = []
        for plan in adventures.VOYAGE_PLANS:
            money, catch = adventures.estimateVoyage(boat, plan)
            expected = "about $%d" % money if money else "about %d fish" % catch
            options.append(
                "%s - %d days, %s if it goes well (%s)"
                % (plan["name"], plan["legs"], expected, plan["description"])
            )
        options.append("Back")
        choice = int(
            self.userInterface.showOptions(
                "%s, %s. How far are you taking her?"
                % (boat["name"], boats.ROLES[boat["role"]]["name"].lower()),
                options,
            )
        )
        if choice == len(options):
            return
        self._provisionVoyage(boat, adventures.VOYAGE_PLANS[choice - 1])

    def _provisionVoyage(self, boat, plan):
        """Stores for the crossing. Under-provisioning is allowed on purpose -
        it's cheaper, and it's how a voyage starts going wrong."""
        recommended = adventures.recommendedSupplies(boat, plan)
        options = []
        amounts = []
        # Over-provisioning is on the menu because events can eat the stores:
        # a full load covers the legs and nothing else, so insuring against a
        # bad week is a decision the player gets to make rather than a trap.
        for label, units in (
            ("Deep stores", int(recommended * 1.5)),
            ("Full stores", recommended),
            ("Three quarters", int(recommended * 0.75)),
            ("Half rations", int(recommended * 0.5)),
        ):
            cost = adventures.supplyCost(units)
            lasts = adventures.legsSupplied(boat, units)
            # Say when it runs out. Half rations on a long voyage is starvation
            # and crew deaths with certainty, and it read as a neutral option
            # sitting next to the others.
            if lasts >= plan["legs"]:
                note = "lasts the voyage"
            else:
                note = "runs out on day %d of %d" % (lasts + 1, plan["legs"])
            options.append("%s - %d supplies, $%d, %s" % (label, units, cost, note))
            amounts.append(units)
        options.append("Back")

        descriptor = (
            "%d hands aboard for %d days. Full stores is %d supplies at $%d "
            "each - enough for the legs and no more, and events at sea can "
            "eat into it. You're carrying $%.2f."
            % (
                boats.crewSize(boat),
                plan["legs"],
                recommended,
                adventures.SUPPLY_COST,
                self.player.money,
            )
        )
        # Sailing a damaged hull on a long voyage is how a whole hold gets
        # lost; flag it before departure rather than at the bottom of the sea.
        if boat["damage"] >= boats.UNSEAWORTHY_DAMAGE / 2:
            descriptor += (
                "\n\nShe's already %d%% damaged. That's %d%% of hull between "
                "you and losing everything aboard - $%d would put her right "
                "before you go."
                % (
                    boat["damage"],
                    boats.MAX_DAMAGE - boat["damage"],
                    boats.repairCost(boat),
                )
            )

        choice = int(self.userInterface.showOptions(descriptor, options))
        if choice == len(options):
            return

        units = amounts[choice - 1]
        cost = adventures.supplyCost(units)
        if not self.player.canAfford(cost):
            self.currentPrompt.text = (
                "That's $%d of stores and you're carrying $%.2f. Sell some "
                "fish, or sail lighter." % (cost, self.player.money)
            )
            return
        self.player.spendMoney(cost)
        self._sailVoyage(adventures.startVoyage(boat, plan, units))

    def _voyageStatus(self, voyage):
        """The line at the top of every leg: where you are and what's left.

        The hold is on it because the voyage is about the hold. Without it the
        only numbers moving on screen were the player's money and fish at
        home - which climb from the rest of the fleet's day and have nothing
        to do with the voyage, so they read as progress when they weren't."""
        hold = "$%d" % voyage["money"]
        if voyage["fish"]:
            hold += " + %d fish" % voyage["fish"]
        return "LEG %d of %d   Hull %d%%   Supplies %d   Crew %d   Hold %s" % (
            voyage["leg"] + 1,
            voyage["legs"],
            voyage["hull"],
            voyage["supplies"],
            adventures.crewAboard(voyage),
            hold,
        )

    def _sailVoyage(self, voyage):
        """One leg at a time until she's home or she isn't."""
        while not adventures.isOver(voyage):
            # The standing prompt is "What would you like to do?", which is
            # meaningless once you're at sea and belongs to the village screens.
            self.currentPrompt.text = "Your call, captain."
            event = adventures.rollEvent(voyage)
            choices = adventures.offeredChoices(voyage, event)
            # Always offered, because being unable to break off turned a bad
            # hull into a slow walk to the bottom rather than a decision.
            options = [choice["text"] for choice in choices] + [
                "Break off and run for home (keep the hold)"
            ]

            picked = int(
                self.userInterface.showOptions(
                    "%s\n\n%s" % (self._voyageStatus(voyage), event["text"]),
                    options,
                )
            )
            if picked == len(options):
                adventures.turnBack(voyage)
                break
            outcome = adventures.resolveChoice(voyage, choices[picked - 1])
            notes = adventures.advanceLeg(voyage)

            # A day at sea is a day at home too - the fleet still lands its
            # catch and rent still comes due while the player is away. The
            # day rolls before the dialogue is built so its news goes on the
            # same screen as the leg that caused it; dropping it is how a
            # player could sail a five-day voyage and come home evicted with
            # nothing on screen having said so.
            dayLines = dayReportLines(self.timeService.increaseDay())

            self.userInterface.showDialogue("\n".join([outcome] + notes + dayLines))

        self._endVoyage(voyage)

    def _endVoyage(self, voyage):
        summary = adventures.finishVoyage(self.player, voyage, self.stats)
        self.userInterface.showDialogue(self._voyageReport(summary))
        self.currentPrompt.text = "What would you like to do?"

    def _voyageReport(self, summary):
        """The homecoming, good or bad."""
        if summary["foundered"]:
            lines = [
                "The hull gives at last, %d days out of %d."
                % (summary["legsSailed"], summary["legs"]),
                "",
                "You make port on the pumps.",
                "  Cargo    lost overboard",
            ]
        else:
            lines = [
                "%s comes home%s."
                % (
                    summary["boat"],
                    " early - you broke off" if summary.get("turnedBack") else "",
                ),
                "",
                "  Earned   $%d" % summary["money"],
            ]
            if summary["fish"]:
                lines.append("  Hold     %d fish" % summary["fish"])
        if summary["crewLost"]:
            lines.append(
                "  Crew     %s did not come back"
                % villagers.joinNames(summary["crewLost"])
            )
        else:
            lines.append("  Crew     all hands accounted for")
        lines.append(
            "  Hull     %d%% - $%d to repair"
            % (
                boats.MAX_DAMAGE - summary["hullDamage"],
                boats.REPAIR_COST_PER_POINT * summary["hullDamage"],
            )
            if summary["hullDamage"]
            else "  Hull     sound"
        )
        return "\n".join(lines)

    def _exportStatus(self):
        """What the next export run would look like, shown above the market
        list so the player can see the load and the day it costs before
        picking where to sail."""
        # With a fleet, say which boat would actually make the crossing - the
        # answer changes when a hauling boat is fitted out for cargo.
        runner = export.exportBoat(self.player)
        name = runner["name"] if runner else "your boat"
        capacity = export.exportCapacity(self.player)
        cargo = export.buildCargo(self.player)
        if not cargo:
            return (
                "%s can carry %d fish to another village, but your hold is "
                "empty. Land a catch first - the crossing costs you a day "
                "either way." % (name, capacity)
            )
        leftBehind = self.player.fishCount - len(cargo)
        status = (
            "%s can carry %d fish per run. You'd load %d of your %d, "
            "best first"
            % (
                name,
                capacity,
                len(cargo),
                self.player.fishCount,
            )
        )
        if leftBehind > 0:
            status += ", leaving %d for the next run" % leftBehind
        status += (
            ".\nFreight is charged before you sail, and the round trip " "takes a day."
        )
        return status

    def _marketOption(self, market, cargo):
        """One line in the market list: what the village is, what the freight
        costs, and what this particular load is worth there."""
        estimate = export.estimateEarnings(cargo, market)
        if estimate >= 0:
            outcome = "about $%.2f clear" % estimate
        else:
            outcome = "a $%.2f loss on this load" % abs(estimate)
        return "%s - %s (freight $%d, %s)" % (
            market["name"],
            market["description"],
            market["shippingCost"],
            outcome,
        )

    def exportFish(self):
        """Pick a village to ship the hold to. Unlike the shop, the export
        markets have no daily budget - the limits are the hold's capacity, the
        freight, and the day the round trip costs."""
        while True:
            markets = export.availableMarkets(self.player)
            cargo = export.buildCargo(self.player)
            options = [self._marketOption(market, cargo) for market in markets]
            options.append("Back")

            choice = int(self.userInterface.showOptions(self._exportStatus(), options))
            if choice == len(options):
                self.currentPrompt.text = "What would you like to do?"
                return

            if self._runExport(markets[choice - 1]):
                return

    def _runExport(self, market):
        """Ship to one market. Returns True if the run actually sailed, so the
        caller knows to leave the menu rather than offer another run on a hold
        that's now empty and a day that's already gone."""
        summary = export.runExport(self.player, market, self.stats)
        if not summary["shipped"]:
            self.currentPrompt.text = self._exportRefusal(summary, market)
            return False

        self.currentPrompt.text = (
            "You sailed to %s and sold %d fish for $%.2f. After the $%d "
            "freight, that's $%.2f clear."
            % (
                market["name"],
                summary["fishExported"],
                summary["gross"],
                summary["shippingCost"],
                summary["earned"],
            )
        )
        if self.player.fishCount > 0:
            self.currentPrompt.text += (
                " %d fish are still in the hold." % self.player.fishCount
            )

        # The round trip is what stops exporting from being a free repeatable
        # action, so the day passes here (and everything a new day brings -
        # the crew's catch, wages, rent - happens while you're away).
        appendDayReport(self.currentPrompt, self.timeService.increaseDay())
        return True

    def _exportRefusal(self, summary, market):
        """Say why a run didn't sail and what the player can do about it."""
        if summary["reason"] == "empty_hold":
            return "You have no fish to ship. Land a catch first."
        if summary["reason"] == "cannot_afford_freight":
            return (
                "Freight to %s costs $%d up front and you're carrying $%.2f. "
                "Sell a few fish at the shop to cover it, or ship somewhere "
                "nearer." % (market["name"], market["shippingCost"], self.player.money)
            )
        return "Your boat can't make the crossing to %s. You'd need a %s." % (
            market["name"],
            business.tierInfo(market["minBoatTier"])["name"],
        )

    def _weatherDescriptor(self):
        """Flavour text for the current day's weather, shown alongside the
        docks descriptor so the player can factor it into the fish/rest
        decision before casting a line."""
        descriptors = {
            "clear": "The sky is clear.",
            "rainy": "Rain is falling steadily.",
            "stormy": "Storm clouds churn overhead.",
        }
        return descriptors.get(self.timeService.weather, "")

    def _renameBusiness(self):
        name = self.userInterface.promptForText(
            "What would you like to name your fishing business?"
        )
        name = (name or "").strip()[:40]
        if name:
            self.player.businessName = name
            self.currentPrompt.text = "Your business is now known as %s!" % name
        else:
            self.currentPrompt.text = "Never mind - the name stays %s." % (
                self.player.businessName or "Unnamed Fishing Co."
            )

    def getTimeOfDayModifier(self, hour):
        """Return (yield factor, flavour label) for fishing at the given hour.

        Fish feed most actively around dawn and dusk and go quiet under the
        midday sun, so the time of day now meaningfully affects the catch."""
        if 5 <= hour <= 8:
            return 1.5, "The dawn bite is on!"
        if 17 <= hour <= 20:
            return 1.5, "The fish are feeding at dusk!"
        if 11 <= hour <= 14:
            return 0.6, "The midday sun keeps the fish deep."
        return 1.0, ""

    def getWeatherModifier(self, weather):
        """Return (yield factor, flavour label) for fishing in the given
        weather, in the same (factor, label) shape as getTimeOfDayModifier.

        Rain stirs up feeding activity while a storm makes the water too
        rough to fish well; clear weather is neutral."""
        if weather == "rainy":
            return 1.3, "The rain has the fish biting eagerly!"
        if weather == "stormy":
            return 0.5, "The stormy seas make for tough fishing."
        return 1.0, ""

    def fish(self):
        self.userInterface.showBusy("Fishing...", 1)

        # Capture the time of day at the start of the trip (the loop advances it).
        timeFactor, timeLabel = self.getTimeOfDayModifier(self.timeService.time)
        weatherFactor, weatherLabel = self.getWeatherModifier(self.timeService.weather)

        hours = random.randint(1, 10)

        # Check if player has enough energy for all hours
        energy_needed = hours * FISHING_ENERGY_COST
        if not self.player.hasEnergy(energy_needed):
            # Fish for as many hours as energy allows
            hours = self.player.energy // FISHING_ENERGY_COST
            if hours == 0:
                self.currentPrompt.text = "You're too tired to fish! Go home and sleep."
                return

        # A better rod widens the timing window, making catches more forgiving.
        reactionWindow = (
            REACTION_BASE_WINDOW + (self.player.rodLevel - 1) * ROD_WINDOW_STEP
        )

        # One timing challenge per cast (not a pass/fail repeated every hour):
        # how quickly you set the hook maps to a catch-quality tier. The active
        # front-end captures and times the reaction, so this works in any UI.
        reactionTime = self.userInterface.timedKeyPress(
            "A fish is biting! React the moment you feel a bite!"
        )

        if reactionTime <= reactionWindow / 2:
            quality, qualityLabel = 1.0, "A perfect hook!"
        elif reactionTime <= reactionWindow:
            quality, qualityLabel = 0.6, "A solid hook."
        else:
            quality, qualityLabel = 0.25, "The fish nearly got away."

        # Spend the fishing hours: time passes and energy is consumed. A long
        # enough trip can cross a day boundary - missing a rent payment, or
        # landing the fleet's catch - without the player ever seeing a "new
        # day" screen, so the day's news is collected here and folded into the
        # trip's own report below. It has to be collected rather than appended
        # as it happens, because that report is written further down and would
        # overwrite anything put on the prompt now. A trip runs 1-10 hours, so
        # it crosses at most one 8am boundary and these lines can't stack up.
        dayLines = []
        for i in range(hours):
            self.stats.hoursSpentFishing += 1
            dayLines += dayReportLines(self.timeService.increaseTime())
            self.player.spendEnergy(10)  # Consume 10 energy per hour

        baseFish = random.randint(1, 10)
        fishToAdd = int(
            baseFish * quality * self.player.fishMultiplier * timeFactor * weatherFactor
        )
        if fishToAdd == 0:
            fishToAdd = 1  # always land at least one fish for the effort

        # Which species you hooked this trip, weighted by rarity.
        fishTypeName = fish.rollFishType()
        self.player.addFish(fishTypeName, fishToAdd)
        self.stats.totalFishCaught += fishToAdd

        self.currentPrompt.text = "You caught %d %s over %d hours! %s" % (
            fishToAdd,
            fishTypeName,
            hours,
            qualityLabel,
        )

        if timeLabel:
            self.currentPrompt.text += " " + timeLabel

        if weatherLabel:
            self.currentPrompt.text += " " + weatherLabel

        # What the fleet did while the player was out on the water, and the
        # eviction notice if a day turned over mid-trip.
        for line in dayLines:
            self.currentPrompt.text += " " + line

    def talkToNPC(self):
        self.userInterface.showInteractiveDialogue(self.npc)
