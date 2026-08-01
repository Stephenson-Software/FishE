# @author Daniel McCoy Stephenson
#
# Captained voyages: the part of the game you actually play.
#
# The fleet earns on its own every morning (see boats.runDailyProduction) -
# that's the background. This is the foreground: the player takes one boat out
# themselves, as captain, and sails her leg by leg through events that ask for
# a decision.
#
# The shape is a journey with legs (each leg is a day at sea) against a set of
# resources that only ever get scarcer unless you spend a decision on them:
#
#   Hull      - damage taken. Reach zero and the voyage is cut short.
#   Supplies  - eaten every leg by every hand aboard. Run out and they starve.
#   Crew      - the named villagers you hired. They can be hurt, and lost.
#   Hold      - money and fish accumulated, and only yours if you get home.
#
# Two things make the decisions specific rather than generic. The boat's role
# picks the event pool and what a good voyage looks like - a fishing voyage
# fills the hold, a raid takes it off somebody else. And the crew you chose to
# bring unlock choices nobody else can offer: Iris Dunmore reads the weather,
# Cormac Ide patches a hull at sea, Junia Marsh goes over the side after what
# was dropped. Who you put aboard is half the game.

import random

from business import boats
from fish import fish
from npc import villagers


# A voyage plan is the pre-departure decision: how far out, and therefore how
# many days at sea, how much it can pay, and how much can go wrong before you
# are too far from home to limp back cheaply.
VOYAGE_PLANS = [
    {
        "name": "A short run",
        "description": "close waters, home in a few days",
        "legs": 4,
        "rewardMultiplier": 1.0,
    },
    {
        "name": "The middle grounds",
        "description": "a week out; better pickings, further from help",
        "legs": 7,
        "rewardMultiplier": 1.6,
    },
    {
        "name": "The far water",
        "description": "a long haul into open sea - the richest and the least forgiving",
        "legs": 11,
        "rewardMultiplier": 2.5,
    },
]

SUPPLY_COST = 4  # per unit, bought before departure
SUPPLIES_PER_CREW_PER_LEG = 1

# What a leg is worth before the plan's multiplier, per hand aboard, scaled by
# the hull. Deliberately several times the passive daily rate: the whole point
# of taking the helm is that it pays far better than letting the crew get on
# with it, because you are the one carrying the risk.
ROLE_LEG_VALUE = {
    boats.ROLE_FISHING: 0,  # fishing voyages pay in fish, not coin
    boats.ROLE_HAULING: 95,
    boats.ROLE_TRANSPORT: 70,
    boats.ROLE_PIRACY: 140,
}
FISHING_LEG_CATCH = 9  # fish per hand per leg, before the plan multiplier

STARVING_DAMAGE_TO_CREW = 0.35  # chance a hungry leg costs a hand


def planFor(index):
    return VOYAGE_PLANS[index]


def estimateVoyage(boat, plan):
    """Roughly what a voyage brings home if it goes to plan, as
    (money, fish).

    Shown on the plan menu because "x1.6 the pickings" is a number the player
    would otherwise have to turn into money themselves, against a per-leg
    value they can't see. Events add to this - it's the floor, not a promise."""
    legs = plan["legs"]
    scale = plan["rewardMultiplier"] * boats.tierFactor(boat)
    aboard = boats.crewSize(boat)
    if boat["role"] == boats.ROLE_FISHING:
        return 0, int(FISHING_LEG_CATCH * aboard * scale) * legs
    perLeg = ROLE_LEG_VALUE.get(boat["role"], 0)
    return int(perLeg * aboard * scale / 4.0) * legs, 0


def recommendedSupplies(boat, plan):
    """Enough to feed everyone aboard for the whole voyage, which is what the
    provisioning screen suggests. Taking less is a real gamble, not a slip."""
    return boats.crewSize(boat) * plan["legs"] * SUPPLIES_PER_CREW_PER_LEG


def supplyCost(units):
    return units * SUPPLY_COST


def legsSupplied(boat, units):
    """How many legs a given load actually feeds. The provisioning menu shows
    this rather than a bare number, because "10 supplies" means nothing until
    you know it runs out halfway."""
    aboard = boats.crewSize(boat) * SUPPLIES_PER_CREW_PER_LEG
    if aboard <= 0:
        return 0
    return units // aboard


def startVoyage(boat, plan, supplies):
    """Build the voyage state. The boat is marked at sea so the fleet knows
    not to count her earnings at home while the player has her."""
    boat["atSea"] = True
    return {
        "boat": boat,
        "role": boat["role"],
        "plan": plan,
        "legs": plan["legs"],
        "leg": 0,
        # Hull starts wherever the boat already was - sailing out on a battered
        # boat is the player's choice to make.
        "hull": max(1, boats.MAX_DAMAGE - boat["damage"]),
        "supplies": supplies,
        "crew": list(boat["crew"]),
        "hands": boat["hands"],
        "money": 0,
        "fish": 0,
        "log": [],
        "status": "sailing",
        "turnedBack": False,
    }


def crewAboard(voyage):
    return len(voyage["crew"]) + voyage["hands"]


def isOver(voyage):
    return voyage["status"] != "sailing"


def turnBack(voyage):
    """Break off and run for home, keeping whatever is in the hold.

    Being committed to every leg once you'd left made a low hull a slow walk
    to a foundering rather than a decision. Cutting your losses is the
    decision."""
    voyage["status"] = "home"
    voyage["turnedBack"] = True


def specialistAboard(voyage, specialty):
    """The first villager aboard with a given specialty, or None. This is what
    turns "who did I bring?" into a decision that shows up on screen."""
    for name in voyage["crew"]:
        villager = villagers.getVillager(name)
        if villager and villager["specialty"] == specialty:
            return name
    return None


# --- the things an outcome can do to a voyage -------------------------------


def damage(voyage, amount):
    voyage["hull"] = max(0, voyage["hull"] - amount)
    if voyage["hull"] <= 0:
        voyage["status"] = "foundering"
    return amount


def repair(voyage, amount):
    voyage["hull"] = min(boats.MAX_DAMAGE, voyage["hull"] + amount)
    return amount


def useSupplies(voyage, amount):
    voyage["supplies"] = max(0, voyage["supplies"] - amount)
    return voyage["supplies"]


def addSupplies(voyage, amount):
    voyage["supplies"] += amount
    return amount


def gain(voyage, money=0, fishCount=0):
    voyage["money"] += money
    voyage["fish"] += fishCount


def loseCrew(voyage, name=None):
    """Take a hand off the voyage. Returns the villager's name, or None if it
    was an unnamed hand (or there was nobody left to lose)."""
    if name is None:
        if voyage["crew"]:
            name = random.choice(voyage["crew"])
        elif voyage["hands"] > 0:
            voyage["hands"] -= 1
            return None
        else:
            return None
    if name in voyage["crew"]:
        voyage["crew"].remove(name)
    return name


# --- the event table --------------------------------------------------------
#
# Each event names the roles it can fire for, the situation, and the choices.
# A choice may carry a "specialty": it is only offered when somebody aboard
# has it, and its text is filled in with their name.

ANY_ROLE = tuple(boats.ROLE_ORDER)


def _squallRunBefore(voyage):
    if random.random() < 0.55:
        taken = damage(voyage, random.randint(10, 22))
        return "She takes it green over the bow. %d%% off the hull." % taken
    return "You outrun it, and make good time doing it."


def _squallHugCoast(voyage):
    useSupplies(voyage, crewAboard(voyage))
    return "You lose a day in the shallows, and the stores with it, but she comes through dry."


def _squallReadIt(voyage, name):
    return "%s finds the seam in it and takes you through clean." % name


def _squallAnchor(voyage):
    if random.random() < 0.3:
        taken = damage(voyage, random.randint(5, 12))
        return "You ride it out. She works at her seams - %d%% damage." % taken
    return "You ride it out at anchor. Long night, no harm done."


def _driftwoodSalvage(voyage):
    haul = random.randint(2, 6)
    addSupplies(voyage, haul)
    return "Barrels, and two of them still sound. %d supplies aboard." % haul


def _driftwoodDive(voyage, name):
    haul = random.randint(6, 12)
    addSupplies(voyage, haul)
    return "%s goes over the side and comes up grinning. %d supplies." % (name, haul)


def _driftwoodPassBy(voyage):
    return "You leave it to the sea. Whatever it was, it wasn't yours."


def _leakPatch(voyage):
    taken = damage(voyage, random.randint(4, 10))
    return "You get canvas over it, badly. %d%% damage before it holds." % taken


def _leakShipwright(voyage, name):
    repaired = repair(voyage, random.randint(8, 16))
    return "%s has her sound again by the middle watch. %d%% back." % (name, repaired)


def _leakIgnore(voyage):
    taken = damage(voyage, random.randint(14, 26))
    return "You pump and hope. It gets worse. %d%% damage." % taken


def _sickPush(voyage):
    if random.random() < 0.4:
        lost = loseCrew(voyage)
        if lost:
            return "You press on, and %s doesn't get up again." % lost
        return "You press on, and a hand doesn't get up again."
    return "You press on. They sweat it out and come right."


def _sickRest(voyage):
    useSupplies(voyage, crewAboard(voyage))
    return "A day hove to, and the sick on full rations. They mend."


def _sickCook(voyage, name):
    return (
        "%s gets broth into them and sits up all night. By morning they're fine." % name
    )


def _becalmedWait(voyage):
    useSupplies(voyage, crewAboard(voyage))
    return "A day of glass-flat water. The stores go down and nothing else happens."


def _becalmedRow(voyage):
    if random.random() < 0.4:
        lost = loseCrew(voyage)
        if lost:
            return "You put the boats out and tow her. %s gives out at the oars." % lost
    return "You put the boats out and tow her clear. Brutal work, but you move."


def _becalmedNavigate(voyage, name):
    return (
        "%s finds a breath of wind nobody else could see, and you're moving by dusk."
        % name
    )


def _goodGroundsFish(voyage):
    haul = random.randint(20, 45)
    gain(voyage, fishCount=haul)
    return "The water boils with them. %d fish aboard." % haul


def _goodGroundsNets(voyage, name):
    haul = random.randint(40, 70)
    gain(voyage, fishCount=haul)
    return "%s has every net right and they come up heavy. %d fish." % (name, haul)


def _goodGroundsMoveOn(voyage):
    return "You leave it. There's better water further out, or so you tell the crew."


def _merchantHail(voyage):
    money = random.randint(60, 160)
    gain(voyage, money=money)
    return "They pay for the escort out of the narrows. $%d." % money


def _merchantBoard(voyage):
    strength = crewAboard(voyage)
    if random.random() < min(0.85, 0.35 + strength * 0.08):
        money = random.randint(250, 700)
        haul = random.randint(10, 40)
        gain(voyage, money=money, fishCount=haul)
        return (
            "You're over the rail before they've cut the lashings. $%d and %d fish."
            % (
                money,
                haul,
            )
        )
    taken = damage(voyage, random.randint(12, 28))
    lost = loseCrew(voyage) if random.random() < 0.3 else None
    text = "They were ready for you. %d%% damage" % taken
    return text + (
        ", and %s doesn't come back." % lost if lost else ", and you break off."
    )


def _merchantShadow(voyage, name):
    money = random.randint(400, 900)
    gain(voyage, money=money)
    return (
        "%s keeps the ledger on their course for a day and you take them at anchor, "
        "asleep. $%d, and not a shot fired." % (name, money)
    )


def _merchantLetPass(voyage):
    return "You let them go. There'll be others."


def _patrolRun(voyage):
    if random.random() < 0.6:
        return "You lose them in the dark and go about your business."
    taken = damage(voyage, random.randint(15, 30))
    return "They put two across your quarter before you're clear. %d%% damage." % taken


def _patrolColours(voyage):
    useSupplies(voyage, crewAboard(voyage))
    return "False colours, a dull cargo, and a very slow inspection. They wave you on."


def _patrolFight(voyage):
    if random.random() < 0.35:
        money = random.randint(300, 800)
        gain(voyage, money=money)
        return "You take the patrol boat itself. $%d off her, and a story." % money
    taken = damage(voyage, random.randint(20, 40))
    lost = loseCrew(voyage) if random.random() < 0.45 else None
    text = "It goes badly. %d%% damage" % taken
    return text + (", and %s is lost over the side." % lost if lost else ".")


def _passengerCalm(voyage):
    money = random.randint(40, 110)
    gain(voyage, money=money)
    return "They settle, and pay the balance without argument. $%d." % money


def _passengerFeed(voyage, name):
    money = random.randint(120, 240)
    gain(voyage, money=money)
    return (
        "%s feeds them properly and they arrive telling everyone. $%d, and a bonus."
        % (
            name,
            money,
        )
    )


def _passengerIgnore(voyage):
    return (
        "You let them stew. They're quieter by morning, and tighter with their money."
    )


EVENTS = [
    {
        "id": "squall",
        "roles": ANY_ROLE,
        "text": "A squall builds to the north and the light goes the colour of a bruise.",
        "choices": [
            {"text": "Run before it", "outcome": _squallRunBefore},
            {"text": "Hug the coast and lose a day", "outcome": _squallHugCoast},
            {
                "specialty": "reading the weather",
                "text": "%s reads the sky for a gap",
                "outcome": _squallReadIt,
            },
            {"text": "Ride it out at anchor", "outcome": _squallAnchor},
        ],
    },
    {
        "id": "driftwood",
        "roles": ANY_ROLE,
        "text": "Wreckage, low in the water, spread across half a mile.",
        "choices": [
            {"text": "Take what floats", "outcome": _driftwoodSalvage},
            {
                "specialty": "diving after lost gear",
                "text": "%s goes down to see what sank with it",
                "outcome": _driftwoodDive,
            },
            {"text": "Give it a wide berth", "outcome": _driftwoodPassBy},
        ],
    },
    {
        "id": "leak",
        "roles": ANY_ROLE,
        "text": "Water in the bilge, more of it every hour, and nobody can find where.",
        "choices": [
            {"text": "Canvas and tar, and hope", "outcome": _leakPatch},
            {
                "specialty": "patching the hull",
                "text": "%s goes looking for the seam",
                "outcome": _leakShipwright,
            },
            {"text": "Pump and press on", "outcome": _leakIgnore},
        ],
    },
    {
        "id": "sickness",
        "roles": ANY_ROLE,
        "text": "Two of the crew are down with something, and a third is going grey.",
        "choices": [
            {"text": "Press on regardless", "outcome": _sickPush},
            {"text": "Heave to and rest them", "outcome": _sickRest},
            {
                "specialty": "feeding the crew",
                "text": "%s takes over the sick berth",
                "outcome": _sickCook,
            },
        ],
    },
    {
        "id": "becalmed",
        "roles": ANY_ROLE,
        "text": "The wind dies at dusk and doesn't come back.",
        "choices": [
            {"text": "Wait it out", "outcome": _becalmedWait},
            {"text": "Put the boats out and tow", "outcome": _becalmedRow},
            {
                "specialty": "reading the far banks",
                "text": "%s knows where the wind lives out here",
                "outcome": _becalmedNavigate,
            },
        ],
    },
    {
        "id": "good_grounds",
        "roles": (boats.ROLE_FISHING,),
        "text": "Birds working the water ahead, thick as smoke.",
        "choices": [
            {"text": "Shoot the nets", "outcome": _goodGroundsFish},
            {
                "specialty": "mending nets",
                "text": "%s rigs every net you have",
                "outcome": _goodGroundsNets,
            },
            {"text": "Push on to deeper water", "outcome": _goodGroundsMoveOn},
        ],
    },
    {
        "id": "merchantman",
        "roles": (boats.ROLE_PIRACY,),
        "text": "A merchantman, low in the water and slow with it, three miles off.",
        "choices": [
            {"text": "Board her", "outcome": _merchantBoard},
            {
                "specialty": "keeping the ledger",
                "text": "%s works out where she'll anchor tonight",
                "outcome": _merchantShadow,
            },
            {"text": "Hail her and offer escort instead", "outcome": _merchantHail},
            {"text": "Let her pass", "outcome": _merchantLetPass},
        ],
    },
    {
        "id": "patrol",
        "roles": (boats.ROLE_PIRACY,),
        "text": "A patrol cutter, and she has seen you.",
        "choices": [
            {"text": "Run for it", "outcome": _patrolRun},
            {"text": "Show false colours and sit still", "outcome": _patrolColours},
            {"text": "Turn and fight", "outcome": _patrolFight},
        ],
    },
    {
        "id": "passengers",
        "roles": (boats.ROLE_TRANSPORT, boats.ROLE_HAULING),
        "text": "Your passengers are cold, loud, and beginning to discuss the fare.",
        "choices": [
            {"text": "Reassure them and press on", "outcome": _passengerCalm},
            {
                "specialty": "feeding the crew",
                "text": "%s puts a hot meal in front of them",
                "outcome": _passengerFeed,
            },
            {"text": "Let them complain", "outcome": _passengerIgnore},
        ],
    },
]


def eventsFor(role):
    return [event for event in EVENTS if role in event["roles"]]


def rollEvent(voyage):
    """Pick the situation this leg presents. Weighted only by which events the
    role allows - the variety comes from the pools, not from tuning."""
    pool = eventsFor(voyage["role"])
    return random.choice(pool)


def offeredChoices(voyage, event):
    """The choices actually available, with specialty-gated ones filled in
    with the name of whoever aboard can do it."""
    offered = []
    for choice in event["choices"]:
        specialty = choice.get("specialty")
        if specialty is None:
            offered.append({"text": choice["text"], "outcome": choice["outcome"]})
            continue
        name = specialistAboard(voyage, specialty)
        if name is None:
            continue
        offered.append(
            {
                "text": choice["text"] % name,
                "outcome": choice["outcome"],
                "specialist": name,
            }
        )
    return offered


def resolveChoice(voyage, choice):
    """Apply a chosen option and return what happened, in words."""
    if "specialist" in choice:
        return choice["outcome"](voyage, choice["specialist"])
    return choice["outcome"](voyage)


def advanceLeg(voyage):
    """Consume a leg's supplies and the leg itself, and return any narration
    the passage of time itself produced (going hungry, or arriving)."""
    voyage["leg"] += 1
    notes = []

    eaten = crewAboard(voyage) * SUPPLIES_PER_CREW_PER_LEG
    if voyage["supplies"] >= eaten:
        useSupplies(voyage, eaten)
    else:
        useSupplies(voyage, voyage["supplies"])
        note = "There's nothing left to eat."
        if random.random() < STARVING_DAMAGE_TO_CREW:
            lost = loseCrew(voyage)
            note += " %s doesn't last the night." % (lost or "One of the hands")
        notes.append(note)

    # The role's steady earnings for a day's work, on top of whatever the
    # event produced.
    _earnLeg(voyage)

    if crewAboard(voyage) <= 0:
        voyage["status"] = "foundering"
        notes.append("There is nobody left to work her.")
    elif voyage["leg"] >= voyage["legs"] and voyage["status"] == "sailing":
        voyage["status"] = "home"
    return notes


def _earnLeg(voyage):
    scale = voyage["plan"]["rewardMultiplier"] * boats.tierFactor(voyage["boat"])
    if voyage["role"] == boats.ROLE_FISHING:
        gain(voyage, fishCount=int(FISHING_LEG_CATCH * crewAboard(voyage) * scale))
        return
    perLeg = ROLE_LEG_VALUE.get(voyage["role"], 0)
    gain(voyage, money=int(perLeg * crewAboard(voyage) * scale / 4.0))


def finishVoyage(player, voyage, stats=None):
    """Bring her home and settle up. Returns a summary of what the voyage cost
    and what it was worth.

    A voyage that founders still gets the boat home - she is not lost - but
    the hold goes over the side and the hull comes back a wreck. That keeps a
    bad voyage a setback rather than the end of a save."""
    boat = voyage["boat"]
    boat["atSea"] = False

    foundered = voyage["status"] == "foundering"
    summary = {
        "boat": boat["name"],
        "foundered": foundered,
        "turnedBack": voyage.get("turnedBack", False),
        "legsSailed": voyage["leg"],
        "legs": voyage["legs"],
        "money": 0,
        "fish": 0,
        "crewLost": [],
        "hullDamage": 0,
    }

    # Whoever didn't come back is off the roster, wherever they were listed.
    for name in list(boat["crew"]):
        if name not in voyage["crew"]:
            boats.releaseCrewMember(player, name)
            summary["crewLost"].append(name)
    lostHands = boat["hands"] - voyage["hands"]
    if lostHands > 0:
        boat["hands"] = voyage["hands"]
        player.workers = max(0, player.workers - lostHands)

    boat["damage"] = boats.MAX_DAMAGE - voyage["hull"] if not foundered else 92
    summary["hullDamage"] = boat["damage"]

    if not foundered:
        summary["money"] = voyage["money"]
        summary["fish"] = voyage["fish"]
        player.money += voyage["money"]
        if voyage["fish"]:
            player.addFish(fish.rollFishType(), voyage["fish"])

    if stats is not None:
        stats.totalVoyagesCaptained += 1
        stats.totalMoneyMade += summary["money"]
        stats.totalMoneyFromVoyages += summary["money"]
        stats.totalFishCaught += summary["fish"]
        stats.crewLostToPiracy += len(summary["crewLost"])
        if foundered:
            stats.totalVoyagesFoundered += 1
    return summary
