# @author Daniel McCoy Stephenson
#
# Voyages: what a boat actually goes out and does.
#
# A fishing boat earns on its own every morning, but the other three roles are
# things the player chooses to do - pick a boat, pick a job, lose a day. That
# keeps a big fleet a set of decisions rather than a number that grows while
# you sleep.
#
# The three job boards, in ascending order of nerve required:
#
#   Transport - passengers. Pays every time, never damages the boat. The floor.
#   Hauling   - freight. Pays better, but heavy seas can knock the hull about.
#   Piracy    - raids. Pays far better than either, and can cost you a villager
#               you hired by name plus a hull too broken to sail until it's paid
#               to be fixed.
#
# Every job scales with the boat's tier and how many hands are aboard, so the
# fleet decisions (which hull, which role, who crews it) are what determine the
# payout - not just how many boats you managed to buy.

import random

from business import boats
from fish import fish


TRANSPORT_RUNS = [
    {
        "name": "Ferry villagers along the coast",
        "minTier": 1,
        "basePay": 90,
        "perCrew": 20,
    },
    {
        "name": "Carry traders out to Kestrel Cove",
        "minTier": 2,
        "basePay": 240,
        "perCrew": 35,
    },
    {
        "name": "Run passengers to Thornhaven",
        "minTier": 3,
        "basePay": 550,
        "perCrew": 65,
    },
]

HAULING_CONTRACTS = [
    {
        "name": "Timber run down to Saltmarsh",
        "minTier": 1,
        "basePay": 130,
        "perCrew": 30,
        "roughSeasChance": 0.15,
    },
    {
        "name": "Grain haul to Kestrel Cove",
        "minTier": 2,
        "basePay": 340,
        "perCrew": 50,
        "roughSeasChance": 0.2,
    },
    {
        "name": "Stone freight for the Thornhaven yards",
        "minTier": 3,
        "basePay": 780,
        "perCrew": 90,
        "roughSeasChance": 0.25,
    },
]

PIRACY_RAIDS = [
    {
        "name": "Fishing skiffs off Saltmarsh",
        "description": "poorly defended, and poorly stocked",
        "minTier": 1,
        "difficulty": 1,
        "loot": (80, 220),
        "fishLoot": (10, 45),
    },
    {
        "name": "The Kestrel Cove trade lane",
        "description": "merchantmen worth taking, and crews who fight back",
        "minTier": 2,
        "difficulty": 2,
        "loot": (420, 950),
        "fishLoot": (20, 80),
    },
    {
        "name": "The Thornhaven bullion run",
        "description": "an escorted strongbox - the richest prize on the water",
        "minTier": 3,
        "difficulty": 3,
        "loot": (1600, 3400),
        "fishLoot": (0, 25),
    },
]

# A raid's odds come from the boat's strength against the target's difficulty.
# Tier counts for more than a single hand, so a big hull with a small crew is
# still a threat - but a full crew on a Rowboat is not taking a bullion run.
TIER_STRENGTH = 3
DIFFICULTY_STRENGTH = 6
MIN_SUCCESS_ODDS = 0.15
MAX_SUCCESS_ODDS = 0.9

# Of the runs that go well, this share go *very* well.
RICH_SHARE = 0.25
# Of the runs that don't, this share go badly rather than merely emptily.
DISASTER_SHARE = 0.3

ROUGH_SEAS_DAMAGE = (8, 20)
DRIVEN_OFF_DAMAGE = (10, 25)
DISASTER_DAMAGE = (30, 60)


def jobsFor(role):
    """The job board for a role. Fishing has none - it earns every morning on
    its own, with no voyage to choose."""
    return {
        boats.ROLE_TRANSPORT: TRANSPORT_RUNS,
        boats.ROLE_HAULING: HAULING_CONTRACTS,
        boats.ROLE_PIRACY: PIRACY_RAIDS,
    }.get(role, [])


def availableJobs(boat):
    """The jobs this particular boat is big enough to take on."""
    return [job for job in jobsFor(boat["role"]) if job["minTier"] <= boat["tier"]]


def canSail(boat):
    """A boat needs a crew and a hull that floats. Returns (bool, reason)."""
    if boats.crewSize(boat) <= 0:
        return False, "no_crew"
    if not boats.isSeaworthy(boat):
        return False, "too_damaged"
    if not availableJobs(boat):
        return False, "no_jobs"
    return True, None


def readyBoats(player):
    """Every boat that could be sent out right now, in fleet order."""
    return [boat for boat in player.boats if canSail(boat)[0]]


def honestPay(boat, job):
    """What a transport run or hauling contract pays: a base fee for the job
    plus a share for every hand aboard."""
    return job["basePay"] + job["perCrew"] * boats.crewSize(boat)


def raidStrength(boat):
    return boat["tier"] * TIER_STRENGTH + boats.crewSize(boat)


def successOdds(boat, raid):
    """The chance a raid goes the player's way, clamped so no raid is ever a
    certainty and none is ever completely hopeless."""
    required = raid["difficulty"] * DIFFICULTY_STRENGTH
    ratio = raidStrength(boat) / float(required)
    return max(MIN_SUCCESS_ODDS, min(MAX_SUCCESS_ODDS, ratio * 0.7))


def raidOutlook(boat, raid):
    """The four outcome chances, for showing the player before they commit.

    Piracy is meant to be a real gamble, not a mystery - the odds are on the
    menu so choosing to raid above your weight is a decision rather than a
    surprise."""
    odds = successOdds(boat, raid)
    return {
        "rich": odds * RICH_SHARE,
        "success": odds * (1 - RICH_SHARE),
        "drivenOff": (1 - odds) * (1 - DISASTER_SHARE),
        "disaster": (1 - odds) * DISASTER_SHARE,
    }


def runTransport(player, boat, job, stats=None):
    """A passenger run. Always pays, never touches the hull - the safe floor
    under the whole job board."""
    pay = honestPay(boat, job)
    player.money += pay
    summary = {
        "role": boats.ROLE_TRANSPORT,
        "job": job["name"],
        "boat": boat["name"],
        "outcome": "paid",
        "earned": pay,
        "damage": 0,
        "fishTaken": 0,
        "crewLost": None,
    }
    if stats is not None:
        stats.totalMoneyMade += pay
        stats.totalTransportRuns += 1
        stats.totalMoneyFromVoyages += pay
    return summary


def runHauling(player, boat, job, stats=None):
    """A freight contract. Pays better than passengers, but the cargo has to
    cross open water and the hull sometimes pays for it."""
    pay = honestPay(boat, job)
    player.money += pay
    damage = 0
    outcome = "delivered"
    if random.random() < job["roughSeasChance"]:
        damage = random.randint(*ROUGH_SEAS_DAMAGE)
        boats.damageBoat(boat, damage)
        outcome = "rough_seas"
    summary = {
        "role": boats.ROLE_HAULING,
        "job": job["name"],
        "boat": boat["name"],
        "outcome": outcome,
        "earned": pay,
        "damage": damage,
        "fishTaken": 0,
        "crewLost": None,
    }
    if stats is not None:
        stats.totalMoneyMade += pay
        stats.totalHaulingContracts += 1
        stats.totalMoneyFromVoyages += pay
    return summary


def runRaid(player, boat, raid, stats=None):
    """A piracy raid, and the only voyage that can cost you something you can't
    buy back.

    Four ways it can end: a rich take, an ordinary one, being driven off with a
    scratched hull, or a disaster that leaves a villager dead and the boat too
    broken to sail until it's repaired."""
    summary = {
        "role": boats.ROLE_PIRACY,
        "job": raid["name"],
        "boat": boat["name"],
        "outcome": None,
        "earned": 0,
        "damage": 0,
        "fishTaken": 0,
        "crewLost": None,
    }

    outlook = raidOutlook(boat, raid)
    roll = random.random()
    if roll < outlook["rich"]:
        summary["outcome"] = "rich"
    elif roll < outlook["rich"] + outlook["success"]:
        summary["outcome"] = "success"
    elif roll < outlook["rich"] + outlook["success"] + outlook["drivenOff"]:
        summary["outcome"] = "driven_off"
    else:
        summary["outcome"] = "disaster"

    if summary["outcome"] in ("rich", "success"):
        take = random.randint(*raid["loot"])
        if summary["outcome"] == "rich":
            take = int(take * 1.5)
        player.money += take
        summary["earned"] = take

        seized = random.randint(*raid["fishLoot"])
        if seized > 0:
            player.addFish(fish.rollFishType(), seized)
            summary["fishTaken"] = seized
        if stats is not None:
            stats.totalMoneyMade += take
            stats.totalPlunder += take
            stats.totalMoneyFromVoyages += take
    elif summary["outcome"] == "driven_off":
        summary["damage"] = random.randint(*DRIVEN_OFF_DAMAGE)
        boats.damageBoat(boat, summary["damage"])
    else:
        summary["damage"] = random.randint(*DISASTER_DAMAGE)
        boats.damageBoat(boat, summary["damage"])
        # Losing a villager you hired by name, off the roster for good, is the
        # cost that makes a raid a real decision - a named person, not a number.
        if boat["crew"]:
            lost = random.choice(boat["crew"])
            boats.releaseCrewMember(player, lost)
            summary["crewLost"] = lost
        elif boat["hands"] > 0:
            boat["hands"] -= 1
            player.workers = max(0, player.workers - 1)

    if stats is not None:
        stats.totalRaids += 1
        if summary["crewLost"]:
            stats.crewLostToPiracy += 1
    return summary


def runVoyage(player, boat, job, stats=None):
    """Send a boat out on a job it's dedicated to. Returns a summary, or None
    if the boat's role has no voyages (a fishing boat earns each morning
    instead)."""
    if boat["role"] == boats.ROLE_TRANSPORT:
        return runTransport(player, boat, job, stats)
    if boat["role"] == boats.ROLE_HAULING:
        return runHauling(player, boat, job, stats)
    if boat["role"] == boats.ROLE_PIRACY:
        return runRaid(player, boat, job, stats)
    return None


def describeJob(boat, job):
    """One line for the job board: what it is and what it's likely to do."""
    if boat["role"] == boats.ROLE_PIRACY:
        outlook = raidOutlook(boat, job)
        odds = outlook["rich"] + outlook["success"]
        return (
            "%s - %s ($%d-$%d, about %d%% to take the prize, %d%% risk of disaster)"
            % (
                job["name"],
                job["description"],
                job["loot"][0],
                job["loot"][1],
                round(odds * 100),
                round(outlook["disaster"] * 100),
            )
        )
    pay = honestPay(boat, job)
    if boat["role"] == boats.ROLE_HAULING:
        return "%s - $%d, %d%% chance of rough seas" % (
            job["name"],
            pay,
            round(job["roughSeasChance"] * 100),
        )
    return "%s - $%d, no risk" % (job["name"], pay)


def unsailableReason(boat):
    """Why this boat can't go out, phrased so the player knows what to fix."""
    _, reason = canSail(boat)
    if reason == "no_crew":
        return "%s has no crew aboard. Assign someone to her first." % boat["name"]
    if reason == "too_damaged":
        return (
            "%s is too badly damaged to sail (%d%%). Repair her at the docks for $%d."
            % (
                boat["name"],
                boat["damage"],
                boats.repairCost(boat),
            )
        )
    if reason == "no_jobs":
        if boat["role"] == boats.ROLE_FISHING:
            return (
                "%s is a fishing boat - she earns her keep every morning, "
                "there's nothing to send her out on." % boat["name"]
            )
        return "%s is too small for any %s work going." % (
            boat["name"],
            boats.ROLES[boat["role"]]["name"].lower(),
        )
    return None
