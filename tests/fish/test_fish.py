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
