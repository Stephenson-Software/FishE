# @author Daniel McCoy Stephenson
"""The prompt now lives in tak (tak.prompt.Prompt); this module keeps FishE's
import path working. tak's Prompt is FishE's with a default text and a
reset() - constructing it with a string, and reading and writing .text, are
unchanged."""

from tak.prompt import Prompt  # noqa: F401
