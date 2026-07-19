# @author Daniel McCoy Stephenson
import json

from jsonschema import validate


def validate_against_schema(data, schema_path):
    """Validate data against the JSON Schema at schema_path.

    Raises jsonschema.exceptions.ValidationError if data doesn't conform
    (e.g. a value outside the range the schema declares as valid).
    """
    with open(schema_path) as schema_file:
        schema = json.load(schema_file)
    validate(instance=data, schema=schema)
