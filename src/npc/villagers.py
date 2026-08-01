# @author Daniel McCoy Stephenson
#
# The village's hireable workforce. Crew slots used to be filled by an
# anonymous headcount; here every hand is a named villager with a backstory
# and a specialty, so hiring is a choice about *who* joins the outfit and each
# hire unlocks a conversation you couldn't have before.
#
# The roster is deliberately at least as long as the largest boat's crew
# capacity (see business.BOAT_TIERS) so a player can always fill every slot
# with a named villager.

from business import business
from npc.npc import NPC


VILLAGERS = [
    {
        "name": "Marta Kell",
        "blurb": "net-mender, sharp eye for a torn mesh",
        "specialty": "mending nets",
        "backstory": "My mother mended nets on this same dock, and her mother "
        "before her. I can spot a bad seam from twenty paces. Give me a torn "
        "net at sunrise and it'll be hauling fish by noon.",
    },
    {
        "name": "Owen Brackish",
        "blurb": "former deep-sea hand, knows the far banks",
        "specialty": "reading the far banks",
        "backstory": "Spent nine years on a deep-sea rig out past the shelf. "
        "Came home when my knees started arguing with the swell. I know where "
        "the fish sit when the water turns cold - that's worth a wage.",
    },
    {
        "name": "Piety Shaw",
        "blurb": "bait mixer, keeps her recipe secret",
        "specialty": "mixing bait",
        "backstory": "I mix my own bait. No, I won't tell you what's in it - "
        "my grandfather took that to his grave and I intend to do the same. "
        "All you need to know is the fish come running.",
    },
    {
        "name": "Tobias Fen",
        "blurb": "young and eager, works twice as long as he's paid for",
        "specialty": "hauling lines",
        "backstory": "I'm the youngest on any crew I've joined, and I hear "
        "about it every day. But I'm first on the boat and last off it. One "
        "day I'll captain my own outfit - until then, put me to work.",
    },
    {
        "name": "Iris Dunmore",
        "blurb": "reads the weather better than the almanac",
        "specialty": "reading the weather",
        "backstory": "The sky tells you everything if you bother to look. I've "
        "kept three crews off the water on days that turned ugly by noon. "
        "Nobody thanks you for the storms you avoid, but I sleep well.",
    },
    {
        "name": "Halvard Stoke",
        "blurb": "hauls more than his share, says less than anyone",
        "specialty": "hauling the heavy catch",
        "backstory": "Not much to tell. I lift what needs lifting. I've been "
        "on eleven boats and left every one of them on good terms.",
    },
    {
        "name": "Nell Tarrow",
        "blurb": "gutter and packer, fastest hands in the village",
        "specialty": "gutting and packing",
        "backstory": "Sixty fish an hour, cleaned and packed, and I'll still "
        "have breath left to argue with you about it. The shop pays better "
        "for a clean fish, so you want me on this crew.",
    },
    {
        "name": "Cormac Ide",
        "blurb": "boat-wright, patches a hull at sea",
        "specialty": "patching the hull",
        "backstory": "I built boats before I crewed them. A hull talks to you "
        "if you listen - creaks in the wrong key and you've got a week to fix "
        "it. I'd rather be aboard when it starts talking.",
    },
    {
        "name": "Sena Vale",
        "blurb": "keeps the ledger, catches every shorted payment",
        "specialty": "keeping the ledger",
        "backstory": "Everyone on a boat can pull a line. Almost nobody can "
        "tell you whether the day turned a profit. I can, down to the coin, "
        "and I'll tell you whether you like the answer or not.",
    },
    {
        "name": "Roderick Pyle",
        "blurb": "old hand, thirty years and every superstition to show for it",
        "specialty": "keeping the old customs",
        "backstory": "Thirty-one years on the water. Never whistled aboard, "
        "never sailed on a Friday, never named a boat after a living soul. "
        "Laugh if you like - I'm still here and plenty of others aren't.",
    },
    {
        "name": "Junia Marsh",
        "blurb": "diver, retrieves what the crew drops overboard",
        "specialty": "diving after lost gear",
        "backstory": "Cold water doesn't bother me the way it bothers other "
        "folk. Anything that goes over the side, I go after - traps, tackle, "
        "the occasional hat. You'd be amazed what a crew loses in a season.",
    },
    {
        "name": "Bastian Roe",
        "blurb": "cook and cheerleader, keeps morale off the rocks",
        "specialty": "feeding the crew",
        "backstory": "A hungry crew is a slow crew. I keep a pot going from "
        "the first hour to the last, and I've talked more than one hand out "
        "of quitting over a bowl of chowder. That's worth a wage too.",
    },
]


def getVillager(name):
    """Return the roster entry for a villager by name, or None if the name
    isn't on the roster (e.g. an unnamed legacy hand from an older save)."""
    for villager in VILLAGERS:
        if villager["name"] == name:
            return villager
    return None


def availableVillagers(player):
    """Villagers who aren't already on the player's crew, in roster order."""
    return [v for v in VILLAGERS if v["name"] not in player.hiredWorkers]


def joinNames(names):
    """Join names the way a person would say them out loud: "A", "A and B",
    "A, B and C". Used wherever the crew is read back to the player."""
    names = list(names)
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    return "%s and %s" % (", ".join(names[:-1]), names[-1])


def createCrewNPC(player, name):
    """Build the NPC for a hired crew member.

    Their conversation is state-aware: the responses reflect the boat they're
    working on and the wages they're being paid, and some questions only
    appear once the outfit has grown into them (see the "condition" keys)."""
    villager = getVillager(name)
    if villager is None:
        # An unnamed hand from a save made before the crew had names. They
        # still work the boat; they just have no roster entry to draw on.
        villager = {
            "name": name,
            "blurb": "an unnamed deckhand",
            "specialty": "whatever needs doing",
            "backstory": "Not much of a talker, this one. Signed on before "
            "you started keeping names.",
        }

    def workDialogue():
        info = business.tierInfo(business.currentTier(player))
        return (
            "Busy, and that's how I like it. I'm on %s most days, and I'm "
            "landing about %d fish a day for you off the %s."
            % (villager["specialty"], info["fishPerDay"], info["name"])
        )

    def boatDialogue():
        tier = business.currentTier(player)
        info = business.tierInfo(tier)
        if tier == 1:
            return (
                "The %s? She's small, but she floats and she's honest work. "
                "Get us something bigger and I'll not complain, mind." % info["name"]
            )
        if tier == 2:
            return (
                "The %s is a proper boat. Room to work, room to stow the "
                "catch. Best rig I've crewed in a while." % info["name"]
            )
        return (
            "A whole %s! Half the village would trade places with me. Don't "
            "let it go to your head, boss." % info["name"]
        )

    def wageDialogue():
        payroll = player.workers * business.WORKER_DAILY_WAGE
        if player.operatorMode or player.money >= payroll:
            return (
                "$%d a day, paid on time. That's more than I can say for the "
                "last outfit I crewed. No complaints from me."
                % business.WORKER_DAILY_WAGE
            )
        return (
            "$%d a day is fair enough - if it turns up. Payroll's $%d a day "
            "for the lot of us and you're carrying $%.2f. I'd sort that out "
            "before morning if I were you."
            % (business.WORKER_DAILY_WAGE, payroll, player.money)
        )

    def crowdedDialogue():
        info = business.tierInfo(business.currentTier(player))
        return (
            "All %d berths full on the %s. Elbow to elbow out there! If you "
            "want more hands you'll need more boat."
            % (info["maxWorkers"], info["name"])
        )

    def businessNameDialogue():
        return (
            "'%s'. It's growing on me. The lads at the tavern have started "
            "saying it without laughing, which is more than you can say for "
            "most outfits round here." % player.businessName
        )

    def ambitionDialogue():
        return (
            "Own boat? Aye, someday. Working a fleet like yours is the best "
            "schooling there is - I'm watching how you do it, %s and all."
            % (player.businessName or "no name")
        )

    return NPC(
        name,
        villager["backstory"],
        [
            {
                "question": "Tell me about yourself.",
                "response": villager["backstory"],
            },
            {
                "question": "How's the work going?",
                "response": workDialogue,
            },
            {
                "question": "How's the boat treating you?",
                "response": boatDialogue,
            },
            {
                "question": "Are the wages treating you right?",
                "response": wageDialogue,
            },
            {
                # Only worth asking once there's no room left to hire.
                "question": "Getting crowded out there, isn't it?",
                "response": crowdedDialogue,
                "condition": lambda: player.workers
                >= business.tierInfo(business.currentTier(player))["maxWorkers"],
            },
            {
                # The outfit has to have a name before anyone can have an
                # opinion about it.
                "question": "What do you make of the name?",
                "response": businessNameDialogue,
                "condition": lambda: bool(player.businessName),
            },
            {
                # Only a hand on a real fleet starts dreaming this way.
                "question": "Ever think about your own boat someday?",
                "response": ambitionDialogue,
                "condition": lambda: business.currentTier(player)
                >= len(business.BOAT_TIERS),
            },
        ],
    )
