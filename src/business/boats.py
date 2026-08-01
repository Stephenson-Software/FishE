# @author Daniel McCoy Stephenson
#
# The fleet: the player's boats, what each one is for, and who crews it.
#
# The business started with a single boat that could only do one thing. Here a
# player owns any number of boats and dedicates each to a role - fishing,
# hauling, piracy or transport - so the fleet becomes a set of decisions about
# what to buy, what to point it at, and which of your hired villagers to put
# aboard.
#
# Crew comes from ONE shared roster (player.hiredWorkers, see src/npc/villagers)
# rather than being hired per boat. A second boat therefore means splitting the
# crew you have or hiring more, and since wages are owed on every hire whether
# they're assigned or not, an idle boat is a real cost.

import random

from business import business
from fish import fish


ROLE_FISHING = "fishing"
ROLE_HAULING = "hauling"
ROLE_PIRACY = "piracy"
ROLE_TRANSPORT = "transport"

ROLES = {
    ROLE_FISHING: {
        "name": "Fishing",
        "summary": "works the waters for a daily catch",
        "detail": "Its crew bring in fish every new day, automatically. This is "
        "the only role that catches anything.",
    },
    ROLE_HAULING: {
        "name": "Hauling",
        "summary": "runs freight, and carries more when you export",
        "detail": "Her crew work the coastal freight trade every day, and her "
        "bigger hold raises how many fish an export run can carry.",
    },
    ROLE_PIRACY: {
        "name": "Piracy",
        "summary": "raids shipping lanes - rich, and dangerous",
        "detail": "Her crew take coin and cargo off other vessels every day. "
        "It pays better than honest work, but a raid that goes wrong damages "
        "the boat, and now and then somebody doesn't come back.",
    },
    ROLE_TRANSPORT: {
        "name": "Transport",
        "summary": "carries passengers for steady, safe money",
        "detail": "Passenger runs pay less than freight, but they pay every "
        "day without fail - no weather, no risk to the boat.",
    },
}

# What each role's crew brings in per head, per day, before the tier scaling
# below. Fishing is absent because it produces fish, not money (see
# business.BOAT_TIERS' fishPerDay).
#
# These are deliberately modest next to what the same boat earns on a voyage
# the player captains themselves (see src/business/adventures.py): the fleet is
# the background income, and taking the helm is how you make real money.
ROLE_DAILY_PER_CREW = {
    ROLE_HAULING: 18,
    ROLE_TRANSPORT: 14,
    ROLE_PIRACY: 26,
}

# A day's piracy is a day of picking fights. Most pass without incident; some
# leave a mark, and rarely somebody doesn't come home. Unlike a voyage you
# captain, the crew are running these themselves - so the odds are gentler.
PASSIVE_RAID_TROUBLE_CHANCE = 0.08
PASSIVE_RAID_TROUBLE_DAMAGE = (5, 15)
PASSIVE_RAID_FATALITY_CHANCE = 0.02

# The order roles are offered in, so the menus stay stable.
ROLE_ORDER = [ROLE_FISHING, ROLE_HAULING, ROLE_PIRACY, ROLE_TRANSPORT]

# A hauling boat's hold is fitted out for cargo, so it carries this much more
# than the same hull would on an export run (see business/export.py).
HAULING_CAPACITY_BONUS = 1.5

# Hull damage, 0 (sound) to 100 (wreck). Above the threshold a boat can't be
# sent out until it's repaired - which is what gives a bad raid a lasting cost
# rather than just a bad payout.
MAX_DAMAGE = 100
UNSEAWORTHY_DAMAGE = 50
REPAIR_COST_PER_POINT = 6


def newBoat(boatId, tier, role=ROLE_FISHING, name=""):
    """Build a boat record. Kept in one place so every boat has the same shape
    however it was created (bought, migrated from an old save, or in a test)."""
    return {
        "id": boatId,
        "name": name or defaultBoatName(tier),
        "tier": tier,
        "role": role,
        # Named villagers assigned to this boat, a subset of the shared roster.
        "crew": [],
        # Unnamed hands from a save made before crews had names (see
        # src/npc/villagers); they work like crew but have no roster entry.
        "hands": 0,
        "damage": 0,
    }


def defaultBoatName(tier):
    return "Unnamed %s" % business.tierInfo(tier)["name"]


def nextBoatId(player):
    """An id no boat in the fleet is using.

    Uniqueness is only ever needed among the boats actually owned - that's what
    the menus select by and what getBoat looks up - so ids restart once a fleet
    empties out. There's no boat left for a reused id to be confused with."""
    if not player.boats:
        return 1
    return max(boat["id"] for boat in player.boats) + 1


def getBoat(player, boatId):
    for boat in player.boats:
        if boat["id"] == boatId:
            return boat
    return None


def addBoat(player, tier, role=ROLE_FISHING, name=""):
    """Put a boat in the fleet and return it. Doesn't charge for it - the
    caller decides whether this was bought, granted or migrated."""
    boat = newBoat(nextBoatId(player), tier, role, name)
    player.boats.append(boat)
    return boat


def removeBoat(player, boatId):
    """Take a boat out of the fleet. Its crew aren't dismissed - they go back
    to the unassigned pool, ready for another berth. Returns the boat, or None
    if there was no such boat."""
    boat = getBoat(player, boatId)
    if boat is None:
        return None
    player.boats.remove(boat)
    return boat


def crewSize(boat):
    """Everyone aboard, named or not."""
    return len(boat["crew"]) + boat["hands"]


def maxCrew(boat):
    return business.tierInfo(boat["tier"])["maxWorkers"]


def hasRoom(boat):
    return crewSize(boat) < maxCrew(boat)


def boatsWithRole(player, role):
    return [boat for boat in player.boats if boat["role"] == role]


def bestBoat(player, role=None):
    """The highest-tier boat in the fleet, optionally of one role. Used
    wherever the fleet as a whole has to answer for itself - what tier the
    business counts as, how much an export run can carry."""
    candidates = player.boats if role is None else boatsWithRole(player, role)
    if not candidates:
        return None
    return max(candidates, key=lambda boat: boat["tier"])


def totalCrewBerths(player):
    """How many hands the whole fleet could carry if every berth were filled."""
    return sum(maxCrew(boat) for boat in player.boats)


def assignedNames(player):
    names = []
    for boat in player.boats:
        names.extend(boat["crew"])
    return names


def unassignedNames(player):
    """Hired villagers who aren't on any boat. They still draw wages - which is
    the pressure to either give them a berth or let them go."""
    assigned = set(assignedNames(player))
    return [name for name in player.hiredWorkers if name not in assigned]


def unassignedHands(player):
    """Unnamed legacy hands not assigned to any boat."""
    total = player.workers - len(player.hiredWorkers)
    return max(0, total - sum(boat["hands"] for boat in player.boats))


def assignCrew(player, boatId, name):
    """Put a named villager aboard. Returns True if they moved; False if the
    boat is full, the name isn't on the roster, or they're already aboard
    somewhere."""
    boat = getBoat(player, boatId)
    if boat is None or not hasRoom(boat):
        return False
    if name not in player.hiredWorkers or name in assignedNames(player):
        return False
    boat["crew"].append(name)
    return True


def assignHand(player, boatId):
    """Put one unnamed legacy hand aboard."""
    boat = getBoat(player, boatId)
    if boat is None or not hasRoom(boat) or unassignedHands(player) <= 0:
        return False
    boat["hands"] += 1
    return True


def unassignCrew(player, boatId, name):
    """Take a named villager off a boat. They stay hired, just unassigned."""
    boat = getBoat(player, boatId)
    if boat is None or name not in boat["crew"]:
        return False
    boat["crew"].remove(name)
    return True


def unassignHand(player, boatId):
    boat = getBoat(player, boatId)
    if boat is None or boat["hands"] <= 0:
        return False
    boat["hands"] -= 1
    return True


def releaseCrewMember(player, name):
    """Remove a villager from the roster entirely, wherever they were - used
    when someone quits over unpaid wages, or is lost on a raid."""
    for boat in player.boats:
        if name in boat["crew"]:
            boat["crew"].remove(name)
    if name in player.hiredWorkers:
        player.hiredWorkers.remove(name)
    player.workers = max(0, player.workers - 1)


def setRole(player, boatId, role):
    """Re-dedicate a boat. Free to do - the interesting decision is which boat
    you commit to what, not paying a toll to change your mind."""
    boat = getBoat(player, boatId)
    if boat is None or role not in ROLES:
        return False
    boat["role"] = role
    return True


def isSeaworthy(boat):
    return boat["damage"] < UNSEAWORTHY_DAMAGE


def damageBoat(boat, amount):
    boat["damage"] = min(MAX_DAMAGE, boat["damage"] + amount)
    return boat["damage"]


def repairCost(boat):
    return boat["damage"] * REPAIR_COST_PER_POINT


def repairBoat(player, boatId):
    """Patch a hull up. Returns the amount paid, or None if there was nothing
    to repair or the player couldn't cover it."""
    boat = getBoat(player, boatId)
    if boat is None or boat["damage"] <= 0:
        return None
    cost = repairCost(boat)
    if not player.canAfford(cost):
        return None
    player.spendMoney(cost)
    boat["damage"] = 0
    return cost


def sellBoat(player, boatId):
    """Sell one boat back for its tier's resale value. Its crew aren't fired -
    they go back to the unassigned pool, where they keep drawing wages until
    they're given another berth or let go. Returns the resale value, or None if
    there was no such boat."""
    boat = getBoat(player, boatId)
    if boat is None:
        return None
    value = business.tierInfo(boat["tier"])["resaleValue"]
    player.money += value
    removeBoat(player, boat["id"])
    return value


def hireWorker(player, name=None):
    """Take on one more hand for the roster, optionally a named villager.

    Hiring is now fleet-wide rather than per-boat: the cap is the total berths
    across every boat owned, and where they actually work is a separate
    decision (assignCrew). Returns True if the hire happened; False if there's
    no boat, no free berth anywhere, or that villager is already hired."""
    if not player.boats:
        return False
    if player.workers >= totalCrewBerths(player):
        return False
    if name is not None:
        if name in player.hiredWorkers:
            return False
        player.hiredWorkers.append(name)
    player.workers += 1
    # Put them straight to work on the first boat with a free berth. Hiring
    # someone who then sits on the dock drawing wages until you notice a second
    # menu would be a trap; reassigning them afterwards is the interesting
    # decision, not finding them a berth in the first place.
    berth = firstBoatWithRoom(player)
    if berth is not None:
        if name is not None:
            berth["crew"].append(name)
        else:
            berth["hands"] += 1
    return True


def firstBoatWithRoom(player):
    for boat in player.boats:
        if hasRoom(boat):
            return boat
    return None


def dismissWorker(player, name=None):
    """Let one hand go for good. With a name, that villager leaves whatever
    boat they were on; without one, an unnamed hand goes first. Returns True if
    someone was dismissed."""
    if player.workers <= 0:
        return False
    if name is not None:
        if name not in player.hiredWorkers:
            return False
        releaseCrewMember(player, name)
        return True
    player.workers -= 1
    _trimCrewRoster(player)
    return True


def _trimCrewRoster(player):
    """Drop named crew until the roster fits the headcount, and return the
    names dropped (most recent hire first).

    workers counts every hand hired, named or not, so any unnamed hands from an
    older save are absorbed before a named villager is asked to leave."""
    dropped = []
    while len(player.hiredWorkers) > player.workers:
        name = player.hiredWorkers[-1]
        dropped.append(name)
        for boat in player.boats:
            if name in boat["crew"]:
                boat["crew"].remove(name)
        player.hiredWorkers.pop()
    _trimAssignedHands(player)
    return dropped


def _trimAssignedHands(player):
    """Unnamed hands aboard can outnumber the unnamed hands still hired once
    the headcount drops; take the surplus off the boats, last boat first."""
    hired = player.workers - len(player.hiredWorkers)
    aboard = sum(boat["hands"] for boat in player.boats)
    surplus = aboard - max(0, hired)
    for boat in reversed(player.boats):
        if surplus <= 0:
            break
        taken = min(surplus, boat["hands"])
        boat["hands"] -= taken
        surplus -= taken


def fishingCrewCount(player):
    """How many hands are actually out catching fish - crew on fishing boats
    only. An unassigned worker, or one on a pirate boat, brings in no catch."""
    return sum(crewSize(boat) for boat in boatsWithRole(player, ROLE_FISHING))


def tierFactor(boat):
    """How much more a hand is worth on this hull than on a Rowboat. Derived
    from the tier's own fishPerDay so one number drives every role."""
    return business.tierInfo(boat["tier"])["fishPerDay"] / float(
        business.WORKER_FISH_PER_DAY
    )


def dailyIncome(boat):
    """What this boat's crew earn in a day, before anything goes wrong. Zero
    for a fishing boat, which produces fish instead."""
    perCrew = ROLE_DAILY_PER_CREW.get(boat["role"], 0)
    return int(perCrew * crewSize(boat) * tierFactor(boat))


def isAtSea(boat):
    """A boat the player has taken out as captain isn't around to earn her
    keep at home (see src/business/adventures.py)."""
    return bool(boat.get("atSea"))


def runDailyProduction(player, stats=None):
    """Apply one day of the whole fleet and return a summary.

    Every role earns now, not just fishing: hauling and transport bring in
    money, piracy brings in money and seized fish, and a fishing boat lands a
    catch as before. Wages are owed on every hand hired, wherever they are -
    idle crew and pirates eat the same as fishermen - so an over-hired
    business still shrinks from the crew doing nothing first.

    A boat the player is away captaining earns nothing while she's gone; that
    is the cost of taking the helm."""
    summary = {
        "workers": player.workers,
        "fishCaught": 0,
        "wagesPaid": 0,
        "quit": 0,
        "quitNames": [],
        "earned": 0,
        "fishSeized": 0,
        "damaged": [],
        "lostAtSea": [],
        "plunder": 0,
        "raidDays": 0,
    }
    if not player.boats or player.workers <= 0:
        return summary

    if player.operatorMode:
        affordable = player.workers
    else:
        affordable = min(
            player.workers, int(player.money // business.WORKER_DAILY_WAGE)
        )
    if affordable < player.workers:
        summary["quit"] = player.workers - affordable
        summary["quitNames"] = _shedCrew(player, summary["quit"])
    summary["workers"] = player.workers

    if player.workers <= 0:
        return summary

    wages = player.workers * business.WORKER_DAILY_WAGE
    player.spendMoney(wages)
    summary["wagesPaid"] = wages

    for boat in player.boats:
        if isAtSea(boat) or crewSize(boat) <= 0:
            continue
        if boat["role"] == ROLE_FISHING:
            _runFishingDay(player, boat, summary)
        elif boat["role"] == ROLE_PIRACY:
            _runPiracyDay(player, boat, summary)
        else:
            _runHonestDay(player, boat, summary)

    if stats is not None:
        stats.totalFishCaught += summary["fishCaught"]
        stats.totalFishCaughtByCrew += summary["fishCaught"]
        stats.totalWagesPaid += wages
        stats.totalMoneyMade += summary["earned"]
        stats.totalMoneyFromVoyages += summary["earned"]
        stats.daysInBusiness += 1
        stats.crewLostToPiracy += len(summary["lostAtSea"])
        stats.totalRaids += summary["raidDays"]
        stats.totalPlunder += summary["plunder"]
    return summary


def _runFishingDay(player, boat, summary):
    """Each hand lands a rarity-rolled species, so what a crew is worth
    depends on the hull they're standing on."""
    fishPerHand = business.tierInfo(boat["tier"])["fishPerDay"]
    for _ in range(crewSize(boat)):
        player.addFish(fish.rollFishType(), fishPerHand)
        summary["fishCaught"] += fishPerHand


def _runHonestDay(player, boat, summary):
    """Hauling and transport: money in, nothing at risk."""
    earned = dailyIncome(boat)
    player.money += earned
    summary["earned"] += earned


def _runPiracyDay(player, boat, summary):
    """Piracy pays best and is the only role that can cost you something.

    Most days are just money and whatever came off somebody's hold. A bad one
    marks the hull, and rarely a hand doesn't come back - which is reported,
    never silent, because losing a villager you hired by name should never be
    something the player only notices later."""
    earned = dailyIncome(boat)
    player.money += earned
    summary["earned"] += earned
    summary["plunder"] += earned
    summary["raidDays"] += 1

    seized = random.randint(0, max(1, crewSize(boat)))
    if seized:
        player.addFish(fish.rollFishType(), seized)
        summary["fishSeized"] += seized

    if random.random() >= PASSIVE_RAID_TROUBLE_CHANCE:
        return
    damage = random.randint(*PASSIVE_RAID_TROUBLE_DAMAGE)
    damageBoat(boat, damage)
    summary["damaged"].append((boat["name"], damage))
    if boat["crew"] and random.random() < PASSIVE_RAID_FATALITY_CHANCE:
        lost = random.choice(boat["crew"])
        releaseCrewMember(player, lost)
        summary["lostAtSea"].append((boat["name"], lost))


def describeDay(summary):
    """The overnight report: what the fleet did while the player slept.

    Returned as lines rather than printed so every front-end shows it the same
    way. Empty when nothing worth mentioning happened."""
    lines = []
    if summary["fishCaught"]:
        lines.append("Your crews landed %d fish." % summary["fishCaught"])
    if summary["earned"]:
        line = "The fleet took $%d." % summary["earned"]
        if summary["fishSeized"]:
            line += " %d fish came off somebody else's hold." % summary["fishSeized"]
        lines.append(line)
    elif summary["fishSeized"]:
        lines.append("%d fish came off somebody else's hold." % summary["fishSeized"])
    for name, damage in summary["damaged"]:
        lines.append("%s took %d%% damage in a scrap." % (name, damage))
    for name, lost in summary["lostAtSea"]:
        lines.append(
            "%s was lost off %s. Word reached the village at dawn." % (lost, name)
        )
    if summary["quitNames"]:
        lines.append(
            "%s walked off over unpaid wages." % ", ".join(summary["quitNames"])
        )
    elif summary["quit"]:
        lines.append("%d hand(s) walked off over unpaid wages." % summary["quit"])
    return lines


def _shedCrew(player, count):
    """Let `count` hands go and return the names of the villagers among them.

    Order is deliberate: idle hands leave before working ones, and unnamed
    hands before villagers the player knows by name."""
    lost = []
    for _ in range(count):
        if player.workers <= 0:
            break
        if unassignedHands(player) > 0:
            player.workers -= 1
            continue
        idle = unassignedNames(player)
        if idle:
            name = idle[-1]
            lost.append(name)
            releaseCrewMember(player, name)
            continue
        boat = _lastCrewedBoat(player)
        if boat is None:
            player.workers -= 1
            continue
        if boat["hands"] > 0:
            boat["hands"] -= 1
            player.workers -= 1
            continue
        name = boat["crew"][-1]
        lost.append(name)
        releaseCrewMember(player, name)
    return lost


def _lastCrewedBoat(player):
    for boat in reversed(player.boats):
        if crewSize(boat) > 0:
            return boat
    return None


def dailyCatch(boat):
    """Fish a fishing boat's crew land in a day. Zero for every other role."""
    if boat["role"] != ROLE_FISHING:
        return 0
    return business.tierInfo(boat["tier"])["fishPerDay"] * crewSize(boat)


def describeBoat(boat):
    """One scannable line for a fleet listing.

    Role comes first because it's what the player is deciding about, and the
    hull is labelled - "Fishing Fleet, Fishing" read as a stutter when the
    tier name and the role name sat side by side unlabelled. The earnings are
    here because a boat's whole purpose is what she brings in, and without
    them there was no way to tell a boat that pays her wages from one that
    doesn't."""
    parts = [
        boat["name"],
        ROLES[boat["role"]]["name"],
        business.tierInfo(boat["tier"])["name"] + " hull",
        "crew %d/%d" % (crewSize(boat), maxCrew(boat)),
    ]
    if isAtSea(boat):
        parts.append("AT SEA")
    elif crewSize(boat) == 0:
        parts.append("idle - no crew, earning nothing")
    elif boat["role"] == ROLE_FISHING:
        parts.append("%d fish/day" % dailyCatch(boat))
    else:
        parts.append("$%d/day" % dailyIncome(boat))
    line = " | ".join(parts)
    if boat["damage"] > 0:
        line += " | %d%% damaged" % boat["damage"]
        if not isSeaworthy(boat):
            line += " - CAN'T SAIL"
    return line


def fleetDailyIncome(player):
    return sum(
        dailyIncome(boat) for boat in player.boats if not isAtSea(boat)
    )


def fleetDailyCatch(player):
    return sum(dailyCatch(boat) for boat in player.boats if not isAtSea(boat))


def dailyPayroll(player):
    return player.workers * business.WORKER_DAILY_WAGE
