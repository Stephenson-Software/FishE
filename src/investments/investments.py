# @author Daniel McCoy Stephenson
#
# Investment properties: rental units elsewhere in the village that the
# player owns but doesn't live in - unlike src/housing (the player's own
# home), these are pure income assets, the same "you don't personally staff
# it, but it earns" idea as the fishing business' hired crew (see
# src/business). Any number of units can be owned at once, each paying its
# daily rental income automatically every new day, and any unit can be sold
# back for a portion of its price.

PROPERTY_TYPES = [
    {"name": "Dockside Cottage", "cost": 1200, "resaleValue": 840, "dailyIncome": 15},
    {
        "name": "Fisherman's Rowhouse",
        "cost": 4000,
        "resaleValue": 2800,
        "dailyIncome": 45,
    },
    {"name": "Harborview Flat", "cost": 9000, "resaleValue": 6300, "dailyIncome": 90},
]


def typeInfo(typeId):
    return PROPERTY_TYPES[typeId - 1]


def countOwned(player, typeId):
    return player.rentalProperties.count(typeId)


def buyProperty(player, typeId, stats=None):
    """Buy one unit of the given property type. Returns True if bought."""
    cost = typeInfo(typeId)["cost"]
    if not player.canAfford(cost):
        return False
    player.spendMoney(cost)
    player.rentalProperties.append(typeId)
    if stats is not None:
        stats.totalPropertiesBought += 1
    return True


def sellProperty(player, typeId):
    """Sell one owned unit of the given property type for its resale value.
    Returns True if a unit was found and sold."""
    if typeId not in player.rentalProperties:
        return False
    player.rentalProperties.remove(typeId)
    player.money += typeInfo(typeId)["resaleValue"]
    return True


def runDailyIncome(player, stats=None):
    """Apply one day of rental income from every owned property and return
    the total earned."""
    if not player.rentalProperties:
        return 0

    income = sum(typeInfo(typeId)["dailyIncome"] for typeId in player.rentalProperties)
    player.money += income
    if stats is not None:
        stats.totalRentalIncome += income
        stats.totalMoneyMade += income
    return income
