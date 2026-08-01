from src.config.config import Config
from src.housing import housing
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
    # a fresh player is Homeless (tier 0), so energy starts at that tier's cap
    assert player.energy == housing.HOUSING_TIERS[0]["maxEnergy"]
    assert player.rodLevel == 1
    assert player.fishByType == {}
    assert player.hasBoat is False
    assert player.workers == 0
    assert player.homeTier == 0
    assert player.rentalProperties == []


def test_initialization_with_config_seeds_from_it():
    # prepare - a config with non-default initial values
    config = Config()
    config.initialMoney = 500
    config.initialFishCount = 3
    config.initialMoneyInBank = 10
    config.initialFishMultiplier = 2
    config.initialPriceForBait = 75

    # call
    player = Player(config)

    # check
    assert player.money == 500
    assert player.fishCount == 3
    assert player.moneyInBank == 10
    assert player.fishMultiplier == 2
    assert player.priceForBait == 75
    # energy stays governed by the housing ladder regardless of config -
    # see Player.__init__'s comment on why it isn't sourced from Config
    assert player.energy == housing.HOUSING_TIERS[0]["maxEnergy"]


def test_initialization_without_config_uses_hardcoded_defaults():
    # call
    player = Player(config=None)

    # check - unaffected by omitting config, same as createPlayer()
    assert player.money == 20
    assert player.fishCount == 0
    assert player.moneyInBank == 0.01
    assert player.fishMultiplier == 1
    assert player.priceForBait == 50


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


def test_removeFish_keeps_the_breakdown_and_count_in_sync():
    # prepare
    player = createPlayer()
    player.addFish("Bass", 3)

    # call
    player.removeFish("Bass")

    # check
    assert player.fishCount == 2
    assert player.fishByType == {"Bass": 2}


def test_removeFish_drops_a_species_once_it_runs_out():
    # prepare
    player = createPlayer()
    player.addFish("Bass", 1)
    player.addFish("Marlin", 1)

    # call
    player.removeFish("Bass")

    # check - the emptied species leaves the breakdown entirely
    assert player.fishByType == {"Marlin": 1}
    assert player.fishCount == 1


def test_removeFish_handles_an_untyped_legacy_fish():
    # prepare - an aggregate count with no species breakdown
    player = createPlayer()
    player.fishCount = 2

    # call
    player.removeFish(None)

    # check - the count drops and no breakdown entry is invented
    assert player.fishCount == 1
    assert player.fishByType == {}


def test_removeFish_can_take_several_at_once():
    # prepare
    player = createPlayer()
    player.addFish("Minnow", 5)

    # call
    player.removeFish("Minnow", 3)

    # check
    assert player.fishCount == 2
    assert player.fishByType == {"Minnow": 2}
