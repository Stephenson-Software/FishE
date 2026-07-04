# @author Daniel McCoy Stephenson
class NPC:
    def __init__(self, name: str, backstory: str, dialogue_options: list = None):
        self.name = name
        self.backstory = backstory
        if dialogue_options is None:
            self.dialogue_options = []
        else:
            self.dialogue_options = dialogue_options

    def introduce(self):
        """Returns the NPC's introduction text"""
        return f"{self.name}: {self.backstory}"
    
    def get_dialogue_options(self):
        """Returns list of available dialogue options"""
        return self.dialogue_options
    
    def get_dialogue_response(self, option_index: int):
        """Returns the response for a specific dialogue option.

        A response may be a plain string, or a zero-arg callable that's
        evaluated on demand - letting a response reflect current game state
        (e.g. an NPC commenting on the player's fishing business) instead of
        being fixed at NPC-construction time."""
        if 0 <= option_index < len(self.dialogue_options):
            response = self.dialogue_options[option_index].get("response", "")
            if callable(response):
                return response()
            return response
        return ""
