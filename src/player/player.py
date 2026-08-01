import os

from housing import housing


# @author Daniel McCoy Stephenson
class Player:
    def __init__(self, config=None):
        self.fishCount = 0 if config is None else config.initialFishCount
        self.money = 20 if config is None else config.initialMoney
        self.moneyInBank = 0.01 if config is None else config.initialMoneyInBank
        self.fishMultiplier = 1 if config is None else config.initialFishMultiplier
        self.priceForBait = 50 if config is None else config.initialPriceForBait
        # Starts at the Homeless tier's energy cap (see src/housing) - a
        # fresh player hasn't found anywhere to stay yet. Deliberately not
        # sourced from Config.initialEnergy: the housing ladder is the
        # source of truth for energy caps (see src/housing/housing.py), and
        # a flat configured starting energy could exceed the Homeless cap.
        self.energy = housing.HOUSING_TIERS[0]["maxEnergy"]
        self.rodLevel = 1
        # Per-species breakdown of the fish currently held. fishCount remains the
        # aggregate total; addFish/clearFish keep the two in sync.
        self.fishByType = {}
        # The fleet (see src/business/boats.py). Every boat the player owns,
        # each dedicated to a role. This is the source of truth for what the
        # player can do on the water; hasBoat and boatTier below are derived
        # from it rather than stored, so the two can't drift apart.
        self.boats = []
        self.workers = 0
        # Names of the villagers hired onto the crew (see src/npc/villagers).
        # workers stays the authoritative headcount - saves made before crews
        # had names have workers without any entries here, and those unnamed
        # hands are still real crew - so this list is never longer than
        # workers (business._trimCrewRoster enforces that).
        self.hiredWorkers = []
        self.businessName = ""
        # Home ownership: a second, independent property track (see
        # src/housing). homeTier is an index into the housing ladder - every
        # player starts homeless (0) and works their way up to renting, then
        # owning.
        self.homeTier = 0
        # Investment properties: rental units the player owns but doesn't
        # live in (see src/investments). A list of PROPERTY_TYPES tier ids,
        # one entry per owned unit - not a single tier like homeTier, since
        # any number of units (of any mix of types) can be owned at once.
        self.rentalProperties = []
        # Testing/debug cheat: when on, every money check passes and spendMoney
        # becomes a no-op, so cash never actually runs out. Not persisted to save
        # files - it's a runtime toggle, not game progress. Defaults from the
        # FISHE_OPERATOR_MODE env var so it can be turned on for a whole session
        # (e.g. `FISHE_OPERATOR_MODE=1 python3 src/fishE.py`) without code changes.
        self.operatorMode = os.environ.get("FISHE_OPERATOR_MODE", "").lower() in (
            "1",
            "true",
            "yes",
        )

    @property
    def hasBoat(self):
        """Whether the player owns any boat at all.

        Derived from the fleet rather than stored: before roles existed this
        was a flag set alongside a single boatTier, and the two could disagree.
        Read-only on purpose - put a boat in the fleet with boats.addBoat."""
        return bool(self.boats)

    @property
    def boatTier(self):
        """The tier of the best boat in the fleet (0 with no boats).

        Everything that asks "how far along is this business?" - NPC dialogue,
        the export markets' minimum, the boat-tier milestones - means the best
        hull the player has, so that's what this answers."""
        if not self.boats:
            return 0
        return max(boat["tier"] for boat in self.boats)

    def canAfford(self, cost):
        return self.operatorMode or self.money >= cost

    def spendMoney(self, cost):
        if not self.operatorMode:
            self.money -= cost

    def hasEnergy(self, amount):
        return self.operatorMode or self.energy >= amount

    def spendEnergy(self, amount):
        if not self.operatorMode:
            self.energy -= amount

    def addFish(self, fishTypeName, amount):
        self.fishByType[fishTypeName] = self.fishByType.get(fishTypeName, 0) + amount
        self.fishCount += amount

    def removeFish(self, fishTypeName, amount=1):
        """Take fish out of the hold, keeping fishByType and fishCount in sync.

        A None species is a legacy save's untyped fish - it only exists in the
        aggregate count, so there's no breakdown entry to decrement."""
        self.fishCount -= amount
        if fishTypeName is None:
            return
        self.fishByType[fishTypeName] -= amount
        if self.fishByType[fishTypeName] <= 0:
            del self.fishByType[fishTypeName]

    def clearFish(self):
        self.fishByType = {}
        self.fishCount = 0
