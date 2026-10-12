from src.stats.stats import Stats


def createStats():
    return Stats()


def test_initialization():
    # call
    stats = createStats()

    # check
    assert stats.totalFishCaught == 0
    assert stats.totalMoneyMade == 0
    assert stats.hoursSpentFishing == 0
    assert stats.moneyMadeFromInterest == 0
    assert stats.timesGottenDrunk == 0
    assert stats.moneyLostFromGambling == 0
    assert stats.totalRentalIncome == 0
    assert stats.highestHomeTier == 0
    assert stats.totalPropertiesBought == 0
    assert stats.totalRentPaid == 0


def test_initialization_lifetimeTotals():
    # call
    stats = createStats()

    # check - every lifetime total a new game starts from, beyond the core
    # fishing/bank/tavern/housing ones above
    assert stats.moneyLostWhileDrunk == 0
    assert stats.earnedMilestones == []
    assert stats.unlockedFeatures == []
    assert stats.totalWorkersHired == 0
    assert stats.totalFishCaughtByCrew == 0
    assert stats.totalWagesPaid == 0
    assert stats.daysInBusiness == 0
    assert stats.totalFishExported == 0
    assert stats.totalMoneyFromExports == 0
    assert stats.totalShippingPaid == 0
    assert stats.totalHaulingContracts == 0
    assert stats.totalTransportRuns == 0
    assert stats.totalRaids == 0
    assert stats.totalPlunder == 0
    assert stats.totalMoneyFromVoyages == 0
    assert stats.crewLostToPiracy == 0
    assert stats.boatsOwned == 0
    assert stats.totalVoyagesCaptained == 0
    assert stats.totalVoyagesFoundered == 0


def test_initialization_listsAreNotShared():
    # prepare - two independent games
    first = createStats()
    second = createStats()

    # call
    first.earnedMilestones.append("first-catch")
    first.unlockedFeatures.append("shop")

    # check - one save's progress must never leak into another's
    assert second.earnedMilestones == []
    assert second.unlockedFeatures == []
