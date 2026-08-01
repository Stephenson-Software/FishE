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
        """Returns the dialogue options currently available.

        An option may carry a "condition" - a zero-arg callable evaluated on
        demand - and stays hidden while that returns False. This lets an NPC
        unlock new lines as the game state changes (e.g. once the player has
        hired villagers onto their crew) instead of every question being
        visible from the first conversation."""
        return [
            option for option in self.dialogue_options if self._is_available(option)
        ]

    def get_dialogue_response(self, option_index: int):
        """Returns the response for a specific dialogue option.

        The index is into the *currently available* options - the same list
        get_dialogue_options() returns and the front-ends number their menus
        from - so conditional options never shift a response onto the wrong
        question.

        A response may be a plain string, or a zero-arg callable that's
        evaluated on demand - letting a response reflect current game state
        (e.g. an NPC commenting on the player's fishing business) instead of
        being fixed at NPC-construction time."""
        options = self.get_dialogue_options()
        if 0 <= option_index < len(options):
            response = options[option_index].get("response", "")
            if callable(response):
                return response()
            return response
        return ""

    def _is_available(self, option):
        condition = option.get("condition")
        if condition is None:
            return True
        return bool(condition())
