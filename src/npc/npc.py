# @author Daniel McCoy Stephenson
"""NPC now lives in tak (tak.npc.NPC); this module keeps FishE's import path
working. The class is unchanged: name, backstory, dialogue options with
optional "condition" and callable "response"."""

from tak.npc import NPC  # noqa: F401
