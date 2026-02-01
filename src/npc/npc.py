# @author Daniel McCoy Stephenson
class NPC:
    def __init__(self, name: str, backstory: str):
        self.name = name
        self.backstory = backstory

    def introduce(self):
        """Returns the NPC's introduction text"""
        return f"{self.name}: {self.backstory}"
