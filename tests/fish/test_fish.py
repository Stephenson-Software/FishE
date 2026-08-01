from src.fish import fish


def test_rollFishType_returns_known_species():
    # call repeatedly; every result must be a catalogued species
    names = {fishType["name"] for fishType in fish.FISH_TYPES}
    for _ in range(50):
        assert fish.rollFishType() in names


def test_fishValue_within_species_range():
    # prepare
    marlin = fish.getFishType("Marlin")

    # check - many rolls all fall within the species' value range
    for _ in range(50):
        value = fish.fishValue("Marlin")
        assert marlin["minValue"] <= value <= marlin["maxValue"]


def test_fishValue_unknown_species_falls_back():
    # check - an unknown species (e.g. a legacy/aggregate sale) uses $3-5
    for _ in range(50):
        assert 3 <= fish.fishValue("NotARealFish") <= 5


def test_rarer_fish_are_worth_more():
    # check - the catalogue is ordered so rarer fish carry higher value floors
    minnow = fish.getFishType("Minnow")
    marlin = fish.getFishType("Marlin")
    assert marlin["minValue"] > minnow["maxValue"]


def test_bestFirst_orders_by_value_and_expands_counts():
    # prepare - a mixed hold
    fishByType = {"Minnow": 2, "Golden Koi": 1, "Bass": 1}

    # call
    queue = fish.bestFirst(fishByType, 4)

    # check - one entry per fish, most valuable species first
    assert queue == ["Golden Koi", "Bass", "Minnow", "Minnow"]


def test_bestFirst_falls_back_to_untyped_entries_for_a_legacy_hold():
    # prepare - a save from before fish had species: a count with no breakdown

    # call
    queue = fish.bestFirst({}, 3)

    # check - fishValue prices these at the original flat range
    assert queue == [None, None, None]


def test_bestFirst_puts_unknown_species_last():
    # prepare - a species that isn't in the catalogue any more
    fishByType = {"Sea Serpent": 1, "Bass": 1}

    # call
    queue = fish.bestFirst(fishByType, 2)

    # check - an unpriceable fish sorts below a known one rather than raising
    assert queue == ["Bass", "Sea Serpent"]
