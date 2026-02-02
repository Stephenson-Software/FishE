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


def test_initialization_with_dialogue_options():
    # prepare
    dialogue_options = [
        {"question": "How are you?", "response": "I'm doing well!"},
        {"question": "What do you sell?", "response": "I sell fishing gear."}
    ]
    
    # call
    npc = NPC("Merchant", "A trader of goods.", dialogue_options)
    
    # check
    assert npc.name == "Merchant"
    assert npc.backstory == "A trader of goods."
    assert len(npc.dialogue_options) == 2
    assert npc.dialogue_options[0]["question"] == "How are you?"


def test_get_dialogue_options():
    # prepare
    dialogue_options = [
        {"question": "Question 1", "response": "Answer 1"},
        {"question": "Question 2", "response": "Answer 2"}
    ]
    npc = NPC("Guide", "A helpful guide.", dialogue_options)
    
    # call
    options = npc.get_dialogue_options()
    
    # check
    assert len(options) == 2
    assert options[0]["question"] == "Question 1"
    assert options[1]["response"] == "Answer 2"


def test_get_dialogue_response():
    # prepare
    dialogue_options = [
        {"question": "Question 1", "response": "Answer 1"},
        {"question": "Question 2", "response": "Answer 2"}
    ]
    npc = NPC("Guide", "A helpful guide.", dialogue_options)
    
    # call
    response1 = npc.get_dialogue_response(0)
    response2 = npc.get_dialogue_response(1)
    
    # check
    assert response1 == "Answer 1"
    assert response2 == "Answer 2"


def test_get_dialogue_response_invalid_index():
    # prepare
    dialogue_options = [
        {"question": "Question 1", "response": "Answer 1"}
    ]
    npc = NPC("Guide", "A helpful guide.", dialogue_options)
    
    # call
    response_negative = npc.get_dialogue_response(-1)
    response_too_large = npc.get_dialogue_response(10)
    
    # check
    assert response_negative == ""
    assert response_too_large == ""


def test_npc_without_dialogue_options():
    # call
    npc = NPC("Simple NPC", "Just a simple character.")
    
    # check
    assert npc.dialogue_options == []
    assert npc.get_dialogue_options() == []
    assert npc.get_dialogue_response(0) == ""


def test_npc_with_empty_list_preserves_identity():
    # prepare - create an empty list that we'll pass
    empty_list = []
    original_id = id(empty_list)
    
    # call
    npc = NPC("NPC", "A character.", empty_list)
    
    # check - the NPC should use the same list object, not create a new one
    assert npc.dialogue_options is empty_list
    assert id(npc.dialogue_options) == original_id
    
    # Verify behavior: if caller modifies the list, NPC sees the changes
    # (This demonstrates why preserving identity matters)
    test_option = {"question": "Test?", "response": "Test response"}
    empty_list.append(test_option)
    assert len(npc.get_dialogue_options()) == 1
    assert npc.get_dialogue_response(0) == "Test response"
    
    # Clean up the list to avoid side effects
    empty_list.clear()
