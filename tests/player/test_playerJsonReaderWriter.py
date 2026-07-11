from src.player import playerJsonReaderWriter
from src.player.player import Player
import json
from jsonschema import validate


def createPlayerJsonReaderWriter():
    return playerJsonReaderWriter.PlayerJsonReaderWriter()


def createPlayer():
    return Player()


def getPlayerSchema():
    # load json from file
    with open("schemas/player.json") as json_file:
        return json.load(json_file)


def test_initialization():
    playerJsonReaderWriter = createPlayerJsonReaderWriter()
    assert playerJsonReaderWriter != None


def test_createJsonFromPlayer():
    playerJsonReaderWriter = createPlayerJsonReaderWriter()
    player = createPlayer()
    playerJson = playerJsonReaderWriter.createJsonFromPlayer(player)

    # check schema
    playerSchema = getPlayerSchema()
    validate(playerJson, playerSchema)


def test_createPlayerFromJson():
    playerJson = {
        "fishCount": 0,
        "fishMultiplier": 1,
        "money": 0,
        "moneyInBank": 0,
        "priceForBait": 50,
        "energy": 100,
    }

    playerJsonReaderWriter = createPlayerJsonReaderWriter()
    player = playerJsonReaderWriter.createPlayerFromJson(playerJson)

    assert player.fishCount == playerJson["fishCount"]
    assert player.fishMultiplier == playerJson["fishMultiplier"]
    assert player.money == playerJson["money"]
    assert player.moneyInBank == playerJson["moneyInBank"]
    assert player.energy == playerJson["energy"]


def test_createPlayerFromJson_backwards_compatibility():
    # Test that old save files without energy still work
    playerJson = {
        "fishCount": 5,
        "fishMultiplier": 2,
        "money": 100,
        "moneyInBank": 50,
        "priceForBait": 75,
        # Note: no energy field
    }

    playerJsonReaderWriter = createPlayerJsonReaderWriter()
    player = playerJsonReaderWriter.createPlayerFromJson(playerJson)

    assert player.fishCount == playerJson["fishCount"]
    assert player.fishMultiplier == playerJson["fishMultiplier"]
    assert player.money == playerJson["money"]
    assert player.moneyInBank == playerJson["moneyInBank"]
    assert player.energy == 100  # Should default to 100


def test_writePlayerToFile():
    # prepare
    import tempfile

    playerJsonReaderWriter = createPlayerJsonReaderWriter()
    player = createPlayer()
    player.fishCount = 10
    player.money = 500

    # call
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as f:
        playerJsonReaderWriter.writePlayerToFile(player, f)
        temp_file_path = f.name

    # check - read back the file and verify
    with open(temp_file_path, "r") as f:
        playerJson = json.load(f)

    assert playerJson["fishCount"] == 10
    assert playerJson["money"] == 500

    # cleanup
    import os

    os.remove(temp_file_path)


def test_readPlayerFromFile():
    # prepare
    import tempfile

    playerJson = {
        "fishCount": 15,
        "fishMultiplier": 3,
        "money": 250,
        "moneyInBank": 100,
        "priceForBait": 60,
        "energy": 80,
    }

    # Write test data to temp file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        json.dump(playerJson, f)
        temp_file_path = f.name

    # call
    playerJsonReaderWriter = createPlayerJsonReaderWriter()
    with open(temp_file_path, "r") as f:
        player = playerJsonReaderWriter.readPlayerFromFile(f)

    # check
    assert player.fishCount == 15
    assert player.fishMultiplier == 3
    assert player.money == 250
    assert player.moneyInBank == 100
    assert player.priceForBait == 60
    assert player.energy == 80

    # cleanup
    import os

    os.remove(temp_file_path)


def test_createPlayerFromJson_missingAllFields_usesDefaults():
    # prepare - a corrupt/partial save with no recognizable fields
    playerJsonReaderWriter = createPlayerJsonReaderWriter()
    playerJson = {}

    # call - must not raise KeyError
    player = playerJsonReaderWriter.createPlayerFromJson(playerJson)

    # check - every field falls back to the Player() default
    defaults = Player()
    assert player.fishCount == defaults.fishCount
    assert player.fishMultiplier == defaults.fishMultiplier
    assert player.money == defaults.money
    assert player.moneyInBank == defaults.moneyInBank
    assert player.priceForBait == defaults.priceForBait
    assert player.energy == defaults.energy
    assert player.rodLevel == defaults.rodLevel


def test_rodLevel_round_trips():
    # prepare
    playerJsonReaderWriter = createPlayerJsonReaderWriter()
    player = Player()
    player.rodLevel = 4

    # call - serialize then deserialize
    playerJson = playerJsonReaderWriter.createJsonFromPlayer(player)
    restored = playerJsonReaderWriter.createPlayerFromJson(playerJson)

    # check - rodLevel persists, and is present in the JSON
    assert playerJson["rodLevel"] == 4
    assert restored.rodLevel == 4


def test_fishByType_round_trips():
    # prepare
    playerJsonReaderWriter = createPlayerJsonReaderWriter()
    player = Player()
    player.fishByType = {"Bass": 3, "Marlin": 1}

    # call
    playerJson = playerJsonReaderWriter.createJsonFromPlayer(player)
    restored = playerJsonReaderWriter.createPlayerFromJson(playerJson)

    # check
    assert playerJson["fishByType"] == {"Bass": 3, "Marlin": 1}
    assert restored.fishByType == {"Bass": 3, "Marlin": 1}


def test_business_fields_round_trip():
    # prepare
    playerJsonReaderWriter = createPlayerJsonReaderWriter()
    player = Player()
    player.hasBoat = True
    player.workers = 3

    # call
    playerJson = playerJsonReaderWriter.createJsonFromPlayer(player)
    restored = playerJsonReaderWriter.createPlayerFromJson(playerJson)

    # check
    assert playerJson["hasBoat"] is True
    assert playerJson["workers"] == 3
    assert restored.hasBoat is True
    assert restored.workers == 3


def test_boatTier_and_businessName_round_trip():
    # prepare
    playerJsonReaderWriter = createPlayerJsonReaderWriter()
    player = Player()
    player.hasBoat = True
    player.boatTier = 2
    player.businessName = "Salty Sea Co."

    # call
    playerJson = playerJsonReaderWriter.createJsonFromPlayer(player)
    restored = playerJsonReaderWriter.createPlayerFromJson(playerJson)

    # check
    assert playerJson["boatTier"] == 2
    assert playerJson["businessName"] == "Salty Sea Co."
    assert restored.boatTier == 2
    assert restored.businessName == "Salty Sea Co."


def test_createPlayerFromJson_missingBusinessFields_defaults():
    # prepare - an older save with no boat/workers fields
    playerJsonReaderWriter = createPlayerJsonReaderWriter()
    playerJson = {
        "fishCount": 5,
        "fishMultiplier": 2,
        "money": 100,
        "moneyInBank": 50,
        "priceForBait": 75,
        "energy": 80,
    }

    # call
    player = playerJsonReaderWriter.createPlayerFromJson(playerJson)

    # check - backward-compatible defaults
    assert player.hasBoat is False
    assert player.workers == 0
    assert player.boatTier == 0
    assert player.businessName == ""


def test_createPlayerFromJson_missingFishByType_defaultsToEmpty():
    # prepare - an older save with no fishByType field
    playerJsonReaderWriter = createPlayerJsonReaderWriter()
    playerJson = {
        "fishCount": 5,
        "fishMultiplier": 2,
        "money": 100,
        "moneyInBank": 50,
        "priceForBait": 75,
        "energy": 80,
    }

    # call
    player = playerJsonReaderWriter.createPlayerFromJson(playerJson)

    # check
    assert player.fishByType == {}


def test_createPlayerFromJson_missingRodLevel_defaultsToOne():
    # prepare - an older save with no rodLevel field
    playerJsonReaderWriter = createPlayerJsonReaderWriter()
    playerJson = {
        "fishCount": 5,
        "fishMultiplier": 2,
        "money": 100,
        "moneyInBank": 50,
        "priceForBait": 75,
        "energy": 80,
    }

    # call
    player = playerJsonReaderWriter.createPlayerFromJson(playerJson)

    # check - backward compatible default
    assert player.rodLevel == 1


def test_homeTier_round_trips():
    # prepare
    playerJsonReaderWriter = createPlayerJsonReaderWriter()
    player = Player()
    player.homeTier = 3

    # call
    playerJson = playerJsonReaderWriter.createJsonFromPlayer(player)
    restored = playerJsonReaderWriter.createPlayerFromJson(playerJson)

    # check
    assert playerJson["homeTier"] == 3
    assert restored.homeTier == 3


def test_createPlayerFromJson_missingHomeTier_defaultsToOne():
    # prepare - an older save with no homeTier field
    playerJsonReaderWriter = createPlayerJsonReaderWriter()
    playerJson = {
        "fishCount": 5,
        "fishMultiplier": 2,
        "money": 100,
        "moneyInBank": 50,
        "priceForBait": 75,
        "energy": 80,
    }

    # call
    player = playerJsonReaderWriter.createPlayerFromJson(playerJson)

    # check - backward compatible default
    assert player.homeTier == 1
