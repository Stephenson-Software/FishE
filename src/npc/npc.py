# @author Daniel McCoy Stephenson
class NPC:
    def __init__(self, name: str, backstory: str, dialogue_options: list = None):
        self.name = name
        self.backstory = backstory
        self.dialogue_options = dialogue_options or []

    def introduce(self):
        """Returns the NPC's introduction text"""
        return f"{self.name}: {self.backstory}"
    
    def get_dialogue_options(self):
        """Returns list of available dialogue options"""
        return self.dialogue_options
    
    def get_dialogue_response(self, option_index: int):
        """Returns the response for a specific dialogue option"""
        if 0 <= option_index < len(self.dialogue_options):
            return self.dialogue_options[option_index].get("response", "")
        return ""
