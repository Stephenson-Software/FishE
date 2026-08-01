import json
from player.player import Player
from business import boats
from validation.schemaValidator import validate_against_schema

PLAYER_SCHEMA_PATH = "schemas/player.json"


class PlayerJsonReaderWriter:
    def createJsonFromPlayer(self, player):
        return {
            "fishCount": player.fishCount,
            "fishMultiplier": player.fishMultiplier,
            "money": player.money,
            "moneyInBank": player.moneyInBank,
            "priceForBait": player.priceForBait,
            "energy": player.energy,
            "rodLevel": player.rodLevel,
            "fishByType": player.fishByType,
            # hasBoat and boatTier are derived from the fleet (see Player), not
            # stored on it. They're still written out so a build from before
            # roles existed can read a modern save and at least know the player
            # owns a boat and how good their best one is.
            "hasBoat": player.hasBoat,
            "boatTier": player.boatTier,
            "boats": player.boats,
            "workers": player.workers,
            "hiredWorkers": player.hiredWorkers,
            "businessName": player.businessName,
            "homeTier": player.homeTier,
            "rentalProperties": player.rentalProperties,
        }

    def createPlayerFromJson(self, playerJson):
        # Read each field with a fallback to the freshly-constructed Player's
        # default, so a save file missing any field loads gracefully instead of
        # raising KeyError (backwards compatibility for older/partial saves).
        player = Player()
        player.fishCount = playerJson.get("fishCount", player.fishCount)
        player.fishMultiplier = playerJson.get("fishMultiplier", player.fishMultiplier)
        player.money = playerJson.get("money", player.money)
        player.moneyInBank = playerJson.get("moneyInBank", player.moneyInBank)
        player.priceForBait = playerJson.get("priceForBait", player.priceForBait)
        player.energy = playerJson.get("energy", player.energy)
        player.rodLevel = playerJson.get("rodLevel", player.rodLevel)
        player.fishByType = playerJson.get("fishByType", player.fishByType)
        player.workers = playerJson.get("workers", player.workers)
        player.hiredWorkers = playerJson.get("hiredWorkers", player.hiredWorkers)
        # businessName is read before the fleet: migrating a pre-roles save
        # names that save's single boat after the business, so the name has to
        # already be on the player by then.
        player.businessName = playerJson.get("businessName", player.businessName)
        player.boats = self._readFleet(playerJson, player)
        player.homeTier = playerJson.get("homeTier", player.homeTier)
        player.rentalProperties = playerJson.get(
            "rentalProperties", player.rentalProperties
        )

        # Validate the resulting values (not the raw input) against the
        # schema, so a save missing keys still loads via the defaults above
        # (backwards compatibility), while an out-of-range value that was
        # present (e.g. energy: -500) is caught here instead of surfacing as
        # a ValueError deep in game logic later.
        validate_against_schema(self.createJsonFromPlayer(player), PLAYER_SCHEMA_PATH)
        return player

    def _readFleet(self, playerJson, player):
        """Rebuild the fleet from a save.

        A save written before boats had roles has no "boats" key at all, just
        the old hasBoat/boatTier pair - so it's migrated into a single fishing
        boat carrying the whole crew, which is exactly what that save meant.
        Nobody loses a boat or a hand by loading an old file."""
        stored = playerJson.get("boats")
        if stored is not None:
            return [self._readBoat(entry) for entry in stored]

        if not playerJson.get("hasBoat", False):
            return []
        tier = playerJson.get("boatTier", 0) or 1
        boat = boats.newBoat(1, tier, boats.ROLE_FISHING, player.businessName)
        boat["crew"] = list(player.hiredWorkers)
        boat["hands"] = max(0, player.workers - len(player.hiredWorkers))
        return [boat]

    def _readBoat(self, entry):
        """Fill in anything a hand-edited or partial boat entry left out, so a
        missing key can't crash the fleet on load."""
        boat = boats.newBoat(
            entry.get("id", 1),
            entry.get("tier", 1),
            entry.get("role", boats.ROLE_FISHING),
            entry.get("name", ""),
        )
        boat["crew"] = list(entry.get("crew", []))
        boat["hands"] = entry.get("hands", 0)
        boat["damage"] = entry.get("damage", 0)
        return boat

    def writePlayerToFile(self, player, jsonFile):
        playerJson = self.createJsonFromPlayer(player)
        json.dump(playerJson, jsonFile)

    def readPlayerFromFile(self, jsonFile):
        playerJson = json.load(jsonFile)
        return self.createPlayerFromJson(playerJson)
