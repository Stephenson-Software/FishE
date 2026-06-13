from ui.userInterface import UserInterface


# @author Daniel McCoy Stephenson
class ConsoleUserInterface(UserInterface):
    """Explicitly-named console/text front-end used by the UI factory.

    The console rendering lives in UserInterface (FishE's default front-end);
    this subclass exists so the factory and callers can refer to the console
    interface by an unambiguous name alongside PygameUserInterface and any
    future web front-end."""

    pass
