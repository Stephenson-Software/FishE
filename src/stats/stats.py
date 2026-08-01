# @author Daniel McCoy Stephenson
class Stats:
    def __init__(self):
        self.totalFishCaught = 0
        self.totalMoneyMade = 0
        self.hoursSpentFishing = 0
        self.moneyMadeFromInterest = 0
        self.timesGottenDrunk = 0
        self.moneyLostFromGambling = 0
        self.moneyLostWhileDrunk = 0
        self.earnedMilestones = []
        # Ids of the features the player has been shown so far (see
        # src/progression). Empty for a new game: everything but fishing is
        # revealed as it is earned.
        self.unlockedFeatures = []
        # Lifetime fishing-business totals, tracked so players can see the
        # impact of the business they've built (see src/business).
        self.totalWorkersHired = 0
        self.totalFishCaughtByCrew = 0
        self.totalWagesPaid = 0
        self.daysInBusiness = 0
        # Lifetime export totals (see src/business/export.py).
        # totalMoneyFromExports is gross, before the freight in
        # totalShippingPaid - the same way totalMoneyMade counts gross sales.
        self.totalFishExported = 0
        self.totalMoneyFromExports = 0
        self.totalShippingPaid = 0
        # Lifetime voyage totals. totalRaids/totalPlunder count days of
        # piracy and what they brought in (see business/boats.py); totalPlunder is
        # the money taken on raids specifically; totalMoneyFromVoyages is every
        # role's takings together.
        self.totalHaulingContracts = 0
        self.totalTransportRuns = 0
        self.totalRaids = 0
        self.totalPlunder = 0
        self.totalMoneyFromVoyages = 0
        self.crewLostToPiracy = 0
        self.boatsOwned = 0
        # Voyages the player captained themselves (see business/adventures.py).
        self.totalVoyagesCaptained = 0
        self.totalVoyagesFoundered = 0
        # Lifetime home-ownership totals (see src/housing). highestHomeTier
        # starts at 0 (Homeless) since that's every player's starting rung.
        self.highestHomeTier = 0
        self.totalRentPaid = 0
        # Lifetime investment-property totals (see src/investments).
        self.totalRentalIncome = 0
        self.totalPropertiesBought = 0
