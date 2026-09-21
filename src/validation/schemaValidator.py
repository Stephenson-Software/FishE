# @author Daniel McCoy Stephenson
"""Schema validation now lives in tak (tak.saves.schema.validateAgainstSchema);
this module keeps FishE's import path and function name working."""

from tak.saves.schema import validateAgainstSchema as validate_against_schema  # noqa: F401
