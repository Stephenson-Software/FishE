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
