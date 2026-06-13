# @author Daniel McCoy Stephenson
#
# The fishing business: once the player owns a boat they can hire workers, who
# bring in a passive catch each day in exchange for a daily wage. This turns
# accumulated money into ongoing production rather than just a number that grows.

from fish import fish

BOAT_PRICE = 500
MAX_WORKERS = 5
WORKER_DAILY_WAGE = 10
WORKER_FISH_PER_DAY = 5


def runDailyProduction(player, stats=None):
    """Apply one day of the fishing business and return a summary.

    Each worker catches WORKER_FISH_PER_DAY fish for WORKER_DAILY_WAGE in wages.
    If the player can't cover the full payroll, the workers they can't pay quit
    (so an over-hired, broke business shrinks instead of going into debt)."""
    summary = {
        "workers": player.workers,
        "fishCaught": 0,
        "wagesPaid": 0,
        "quit": 0,
    }
    if not player.hasBoat or player.workers <= 0:
        return summary

    affordable = min(player.workers, int(player.money // WORKER_DAILY_WAGE))
    if affordable < player.workers:
        summary["quit"] = player.workers - affordable
        player.workers = affordable
    summary["workers"] = player.workers

    if affordable <= 0:
        return summary

    wages = affordable * WORKER_DAILY_WAGE
    player.money -= wages
    # Each worker fishes the same waters as the player, landing a rarity-rolled
    # species (not just the cheapest one), so the crew's income is competitive
    # with simply upgrading your own gear.
    caught = 0
    for _ in range(affordable):
        player.addFish(fish.rollFishType(), WORKER_FISH_PER_DAY)
        caught += WORKER_FISH_PER_DAY
    summary["wagesPaid"] = wages
    summary["fishCaught"] = caught
    if stats is not None:
        stats.totalFishCaught += caught
    return summary
