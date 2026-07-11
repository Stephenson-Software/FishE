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
    assert stats.highestHomeTier == 1
