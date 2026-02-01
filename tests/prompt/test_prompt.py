from src.prompt.prompt import Prompt


def test_initialization():
    # call
    prompt = Prompt("Test prompt")

    # check
    assert prompt.text == "Test prompt"


def test_text_can_be_modified():
    # prepare
    prompt = Prompt("Initial text")

    # call
    prompt.text = "Modified text"

    # check
    assert prompt.text == "Modified text"
