from src.npc.npc import NPC


def test_initialization():
    # call
    npc = NPC("Shopkeeper", "A friendly merchant who loves fishing gear.")

    # check
    assert npc.name == "Shopkeeper"
    assert npc.backstory == "A friendly merchant who loves fishing gear."


def test_introduce():
    # prepare
    npc = NPC("Barkeep", "An old sailor with many tales to tell.")

    # call
    introduction = npc.introduce()

    # check
    assert introduction == "Barkeep: An old sailor with many tales to tell."
