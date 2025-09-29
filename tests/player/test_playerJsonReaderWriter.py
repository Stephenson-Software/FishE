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
