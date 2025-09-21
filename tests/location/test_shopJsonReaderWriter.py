from src.location import shopJsonReaderWriter
from src.location.shop import Shop
from src.player.player import Player
from src.prompt.prompt import Prompt
from src.stats.stats import Stats
from src.ui.userInterface import UserInterface
from src.world.timeService import TimeService
import json
from jsonschema import validate


def createShopJsonReaderWriter():
    return shopJsonReaderWriter.ShopJsonReaderWriter()


def createShop():
    player = Player()
    stats = Stats()
    timeService = TimeService(player, stats)
    prompt = Prompt("What would you like to do?")
    userInterface = UserInterface(prompt, timeService, player)
    return Shop(userInterface, prompt, player, stats, timeService)


def getShopSchema():
    # load json from file
    with open("schemas/shop.json") as json_file:
        return json.load(json_file)


def test_initialization():
    shopJsonReaderWriter = createShopJsonReaderWriter()
    assert shopJsonReaderWriter != None


def test_createJsonFromShop():
    shopJsonReaderWriter = createShopJsonReaderWriter()
    shop = createShop()
    shop.money = 500
    shopJson = shopJsonReaderWriter.createJsonFromShop(shop)
    assert shopJson != None
    assert shopJson["money"] == 500
    
    # Validate against schema
    shopSchema = getShopSchema()
    validate(shopJson, shopSchema)


def test_createShopFromJson():
    shopJsonReaderWriter = createShopJsonReaderWriter()
    shopJson = {"money": 750}

    # Validate against schema
    shopSchema = getShopSchema()
    validate(shopJson, shopSchema)

    player = Player()
    stats = Stats()
    timeService = TimeService(player, stats)
    prompt = Prompt("What would you like to do?")
    userInterface = UserInterface(prompt, timeService, player)
    
    shopFromJson = shopJsonReaderWriter.createShopFromJson(
        shopJson, userInterface, prompt, player, stats, timeService
    )
    assert shopFromJson != None
    assert shopFromJson.money == 750


def test_writeShopToFile():
    shopJsonReaderWriter = createShopJsonReaderWriter()
    shop = createShop()
    shop.money = 300
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        shopJsonReaderWriter.writeShopToFile(shop, f)
        filepath = f.name
    
    # Read back the file to verify
    with open(filepath, 'r') as f:
        data = json.load(f)
        assert data["money"] == 300
    
    import os
    os.unlink(filepath)


def test_readShopFromFile():
    shopJsonReaderWriter = createShopJsonReaderWriter()
    
    import tempfile
    shopData = {"money": 900}
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        json.dump(shopData, f)
        filepath = f.name
    
    player = Player()
    stats = Stats()
    timeService = TimeService(player, stats)
    prompt = Prompt("What would you like to do?")
    userInterface = UserInterface(prompt, timeService, player)
    
    with open(filepath, 'r') as f:
        shop = shopJsonReaderWriter.readShopFromFile(f, userInterface, prompt, player, stats, timeService)
        assert shop != None
        assert shop.money == 900
    
    import os
    os.unlink(filepath)