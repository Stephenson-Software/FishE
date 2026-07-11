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
        # Lifetime fishing-business totals, tracked so players can see the
        # impact of the business they've built (see src/business).
        self.totalWorkersHired = 0
        self.totalFishCaughtByCrew = 0
        self.totalWagesPaid = 0
        self.daysInBusiness = 0
        # Lifetime home-ownership totals (see src/housing). highestHomeTier
        # starts at 0 (Homeless) since that's every player's starting rung.
        self.highestHomeTier = 0
        self.totalRentPaid = 0
        # Lifetime investment-property totals (see src/investments).
        self.totalRentalIncome = 0
        self.totalPropertiesBought = 0
