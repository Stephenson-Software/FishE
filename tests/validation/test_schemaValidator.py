import pytest
from jsonschema.exceptions import ValidationError

from src.validation.schemaValidator import validate_against_schema


def _validPlayerJson():
    return {
        "fishCount": 0,
        "money": 20,
        "moneyInBank": 0.01,
        "fishMultiplier": 1,
        "priceForBait": 50,
        "energy": 100,
    }


def test_validate_against_schema_passes_for_valid_data():
    # call/check - must not raise
    validate_against_schema(_validPlayerJson(), "schemas/player.json")


def test_validate_against_schema_raises_for_out_of_range_data():
    # prepare
    playerJson = _validPlayerJson()
    playerJson["energy"] = -1

    # call/check
    with pytest.raises(ValidationError):
        validate_against_schema(playerJson, "schemas/player.json")
