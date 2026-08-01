# @author Daniel McCoy Stephenson
#
# Progressive disclosure: which parts of the village the player has been shown
# yet. A new game opens on the docks with a rod and a single thing to do -
# fish - and every other option in the game arrives later, one at a time, as
# the player earns it.
#
# The point is pacing rather than difficulty. Nothing here makes an action
# harder or more expensive; it only decides whether the option is on the menu
# yet, so a first-time player is never handed eleven choices they have no
# context for. Each unlock fires on a state the player has just created
# themselves (a full basket, a first sale, a heavy purse), and announces itself
# with the reason - "your basket is heavy, go sell them" - so the next thing to
# do is always the thing that just became possible.
#
# Data-driven the same way src/achievements is: add a row to UNLOCKS and it is
# tracked, gated and announced automatically. Conditions read only the Player
# and the Stats, deliberately - both are already threaded through every
# location, so gating a menu entry never needs a new constructor argument.
#
# Unlocks are permanent. The set of already-granted ids lives on
# Stats (stats.unlockedFeatures) so it is saved, and a feature is announced
# exactly once across the whole run.

# Feature ids. Each is referenced by the location that owns the menu entry.
SHOP = "shop"
HOME = "home"
TALK = "talk"
BAIT = "bait"
ROD = "rod"
HOUSING = "housing"
BANK = "bank"
JOURNAL = "journal"
TAVERN = "tavern"
FLEET = "fleet"
INVESTMENTS = "investments"
GOAL = "goal"

# The opening line of a brand new game, in place of the standing "What would
# you like to do?" - which is a strange thing to ask someone whose menu has one
# entry on it.
OPENING_PROMPT = "You've got a rod, a bucket, and the whole sea in front of you."


def _wealth(player):
    return player.money + player.moneyInBank


# Ordered roughly by when they fire, though nothing depends on the order - each
# condition is checked independently every time the game loop comes around.
UNLOCKS = [
    {
        "id": SHOP,
        "name": "the shop",
        "announcement": "Your basket is heavy with fish. Gilbert buys them at "
        "the shop - better go sell them.",
        "condition": lambda player, stats: stats.totalFishCaught >= 1,
    },
    {
        "id": HOME,
        "name": "home",
        # Either half of this is enough on its own: the first sale is the
        # natural moment to be shown where you sleep, and running the tank dry
        # before selling anything must not leave a player with no way to
        # recover their energy.
        "announcement": "You're worn out, and there's a bunk waiting. You can "
        "head home to sleep.",
        "condition": lambda player, stats: stats.totalMoneyMade > 0
        or player.energy < 10,
    },
    {
        "id": BAIT,
        "name": "better bait",
        "announcement": "You've coin enough for the good bait. Gilbert keeps "
        "it behind the counter.",
        "condition": lambda player, stats: player.money >= player.priceForBait,
    },
    {
        "id": TALK,
        "name": "conversation",
        "announcement": "You've been around the village long enough that folk "
        "will stop and talk to you now.",
        "condition": lambda player, stats: stats.hoursSpentFishing >= 20,
    },
    {
        "id": ROD,
        "name": "better rods",
        "announcement": "Better bait fills the basket; a better rod makes the "
        "fish easier to hook. Gilbert has some on the wall.",
        "condition": lambda player, stats: player.fishMultiplier > 1,
    },
    {
        "id": HOUSING,
        "name": "somewhere to live",
        "announcement": "You've earned enough to keep a roof over your head. "
        "See about a room from home.",
        "condition": lambda player, stats: stats.totalMoneyMade >= 100,
    },
    {
        "id": BANK,
        "name": "the bank",
        "announcement": "That's more coin than you want in your pocket. "
        "Margaret at the bank will keep it safe, and pay you interest.",
        "condition": lambda player, stats: _wealth(player) >= 150,
    },
    {
        "id": JOURNAL,
        "name": "your journal",
        "announcement": "You've put in enough hours to wonder how they add "
        "up. There's a ledger at home.",
        "condition": lambda player, stats: stats.hoursSpentFishing >= 15,
    },
    {
        "id": FLEET,
        "name": "a boat of your own",
        "announcement": "Sam says there's a rowboat for sale. A boat means a "
        "crew, and a crew fishes while you sleep.",
        "condition": lambda player, stats: _wealth(player) >= 250,
    },
    {
        "id": TAVERN,
        "name": "the tavern",
        "announcement": "Word of the new fisherman has reached Old Tom. The "
        "tavern door is open to you.",
        "condition": lambda player, stats: stats.totalMoneyMade >= 250,
    },
    {
        "id": INVESTMENTS,
        "name": "investment properties",
        "announcement": "Margaret mentions the cottages that come up for sale "
        "now and then. A property pays every day, whether you fish or not.",
        "condition": lambda player, stats: _wealth(player) >= 600,
    },
    {
        "id": GOAL,
        "name": "a fortune worth counting",
        "announcement": "A thousand dollars to your name. They say ten "
        "thousand is enough to retire on - you're on your way.",
        "condition": lambda player, stats: _wealth(player) >= 1000,
    },
]

ALL_FEATURE_IDS = [unlock["id"] for unlock in UNLOCKS]


def isUnlocked(stats, featureId):
    """Whether the player has been shown the given feature yet."""
    return featureId in stats.unlockedFeatures


def getNextUnlock(player, stats):
    """Grant and return the next feature the player has earned, or None.

    One per call, deliberately, even when several conditions came true at once.
    A single long cast can land a first catch, empty the energy bar and put
    hours on the clock all at the same time - announcing all of that on one
    screen would hand the player the wall of new options this module exists to
    avoid. The rest are still earned and arrive on the following screens, one
    per action, so the game always unfolds a button at a time.

    The granted id is appended to stats.unlockedFeatures (which is saved), so a
    feature is announced once and then stays available for good - the same "the
    persisted list doubles as the already-announced flag" approach used for
    milestones in src/achievements."""
    for unlock in UNLOCKS:
        if unlock["id"] in stats.unlockedFeatures:
            continue
        if unlock["condition"](player, stats):
            stats.unlockedFeatures.append(unlock["id"])
            return unlock
    return None


def catchUp(player, stats):
    """Grant every already-earned unlock at once, without announcing anything.

    Called when a game is loaded, where the drip above would be wrong. A save
    file written before this module existed has no unlockedFeatures at all, and
    its player may already own a fleet and a manor - re-locking the village
    around them would be a bug, and handing it back one button per action would
    be worse. A save that does have the list is unaffected, and a brand new
    game meets no conditions, so this grants nothing there either."""
    while getNextUnlock(player, stats) is not None:
        pass


def unlockAll(stats):
    """Grant every feature at once. For tests and for anything that needs the
    full menu without playing through to it."""
    stats.unlockedFeatures = list(ALL_FEATURE_IDS)


def isFreshStart(stats):
    """True for a player who hasn't done anything yet - nothing unlocked and
    no fish caught. Used to open the game on something more inviting than the
    standing "What would you like to do?" prompt."""
    return not stats.unlockedFeatures and stats.totalFishCaught == 0
