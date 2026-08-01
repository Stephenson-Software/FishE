from src.player.player import Player
from src.progression import progression
from src.stats.stats import Stats


def createState():
    return Player(), Stats()


def test_a_brand_new_player_has_unlocked_nothing():
    # prepare
    player, stats = createState()

    # call
    unlock = progression.getNextUnlock(player, stats)

    # check - the opening screen is fishing and nothing else
    assert unlock is None
    assert stats.unlockedFeatures == []


def test_first_catch_unlocks_the_shop_and_says_why():
    # prepare
    player, stats = createState()
    stats.totalFishCaught = 1

    # call
    unlock = progression.getNextUnlock(player, stats)

    # check
    assert unlock["id"] == progression.SHOP
    assert "sell" in unlock["announcement"]
    assert progression.isUnlocked(stats, progression.SHOP)


def test_an_unlock_is_only_announced_once():
    # prepare
    player, stats = createState()
    stats.totalFishCaught = 1
    progression.getNextUnlock(player, stats)

    # call - the condition still holds on the next pass
    unlock = progression.getNextUnlock(player, stats)

    # check
    assert unlock is None
    assert stats.unlockedFeatures.count(progression.SHOP) == 1


def test_selling_fish_unlocks_home():
    # prepare
    player, stats = createState()
    stats.totalMoneyMade = 12

    # call
    progression.catchUp(player, stats)

    # check
    assert progression.isUnlocked(stats, progression.HOME)


def test_running_out_of_energy_unlocks_home_even_without_a_sale():
    # prepare - a player who fished themselves flat before selling anything.
    # Without this they would have no way to get their energy back.
    player, stats = createState()
    player.energy = 0

    # call
    progression.catchUp(player, stats)

    # check
    assert progression.isUnlocked(stats, progression.HOME)


def test_bait_unlocks_once_it_is_affordable():
    # prepare
    player, stats = createState()
    player.money = player.priceForBait - 1

    # call
    progression.catchUp(player, stats)

    # check
    assert not progression.isUnlocked(stats, progression.BAIT)

    # prepare - one more sale covers it
    player.money = player.priceForBait

    # call
    progression.catchUp(player, stats)

    # check
    assert progression.isUnlocked(stats, progression.BAIT)


def test_rod_unlocks_after_the_first_bait_upgrade():
    # prepare
    player, stats = createState()
    player.fishMultiplier = 2

    # call
    progression.catchUp(player, stats)

    # check
    assert progression.isUnlocked(stats, progression.ROD)


def test_banked_money_counts_toward_the_wealth_unlocks():
    # prepare - the same wealth, all of it in the bank
    player, stats = createState()
    player.money = 0
    player.moneyInBank = 700

    # call
    progression.catchUp(player, stats)

    # check
    assert progression.isUnlocked(stats, progression.BANK)
    assert progression.isUnlocked(stats, progression.FLEET)
    assert progression.isUnlocked(stats, progression.INVESTMENTS)
    assert not progression.isUnlocked(stats, progression.GOAL)


def test_every_unlock_is_reachable_and_has_its_pieces():
    # check - a row with no id/announcement/condition would be silently
    # un-gateable, and a duplicate id would announce twice
    ids = [unlock["id"] for unlock in progression.UNLOCKS]
    assert len(ids) == len(set(ids))
    assert ids == progression.ALL_FEATURE_IDS
    for unlock in progression.UNLOCKS:
        assert unlock["id"]
        assert unlock["name"]
        assert unlock["announcement"].endswith(".")
        assert callable(unlock["condition"])


def test_unlockAll_grants_the_whole_village():
    # prepare
    _, stats = createState()

    # call
    progression.unlockAll(stats)

    # check
    for featureId in progression.ALL_FEATURE_IDS:
        assert progression.isUnlocked(stats, featureId)


def test_catchUp_grants_an_established_player_without_announcing():
    # prepare - the state of a save written before progression existed: a rich
    # player with an empty unlockedFeatures list
    player, stats = createState()
    player.money = 20000
    player.fishMultiplier = 5
    stats.totalFishCaught = 4000
    stats.totalMoneyMade = 30000
    stats.hoursSpentFishing = 900

    # call
    progression.catchUp(player, stats)

    # check - the whole village is open, and nothing is left to announce on
    # the first screen they see
    assert sorted(stats.unlockedFeatures) == sorted(progression.ALL_FEATURE_IDS)
    assert progression.getNextUnlock(player, stats) is None


def test_catchUp_grants_nothing_to_a_new_game():
    # prepare
    player, stats = createState()

    # call
    progression.catchUp(player, stats)

    # check
    assert stats.unlockedFeatures == []


def test_isFreshStart():
    # prepare
    player, stats = createState()

    # check
    assert progression.isFreshStart(stats)

    # prepare - one cast in
    stats.totalFishCaught = 3
    progression.getNextUnlock(player, stats)

    # check
    assert not progression.isFreshStart(stats)


def test_only_one_feature_is_granted_per_call():
    # prepare - a single long cast can land a first catch and empty the energy
    # bar at the same time, meeting two conditions at once
    player, stats = createState()
    stats.totalFishCaught = 8
    player.energy = 0

    # call
    first = progression.getNextUnlock(player, stats)

    # check - the player is told one thing, not two
    assert first["id"] == progression.SHOP
    assert stats.unlockedFeatures == [progression.SHOP]

    # call - the other arrives on the following screen
    assert progression.getNextUnlock(player, stats)["id"] == progression.HOME
    assert progression.getNextUnlock(player, stats) is None
