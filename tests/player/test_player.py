from src.player.player import Player


def createPlayer():
    return Player()


def test_initialization():
    # call
    player = createPlayer()

    # check
    assert player.fishCount == 0
    assert player.money == 20
    assert player.moneyInBank == 0.01
    assert player.fishMultiplier == 1
    assert player.energy == 100
    assert player.rodLevel == 1
    assert player.fishByType == {}
    assert player.hasBoat is False
    assert player.workers == 0


def test_addFish_and_clearFish_keep_count_in_sync():
    # prepare
    player = createPlayer()

    # call - add two species
    player.addFish("Bass", 3)
    player.addFish("Bass", 2)
    player.addFish("Marlin", 1)

    # check - per-type breakdown and aggregate count agree
    assert player.fishByType == {"Bass": 5, "Marlin": 1}
    assert player.fishCount == 6

    # call - clearing resets both
    player.clearFish()
    assert player.fishByType == {}
    assert player.fishCount == 0
