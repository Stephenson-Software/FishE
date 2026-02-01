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
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".json"
    ) as f:
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
