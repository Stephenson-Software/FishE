#!/usr/bin/env python3
"""
Visual demo of the responsive UI layout.
Run this script to see a pygame window that you can resize to test the responsive behavior.
Press ESC or close the window to exit.
"""

import sys
import os
import pygame

# Add src to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ui.enum.uiType import UIType
from ui.userInterfaceFactory import UserInterfaceFactory
from player.player import Player
from prompt.prompt import Prompt
from stats.stats import Stats
from world.timeService import TimeService


def main():
    """Run a visual demo of the responsive UI"""
    print("=== Visual Responsive UI Demo ===")
    print("A pygame window will open. You can:")
    print("  • Resize the window by dragging the corners")
    print("  • Use UP/DOWN arrow keys to navigate")
    print("  • Use number keys 1-5 to select options")
    print("  • Press ENTER or SPACE to confirm selection")
    print("  • Press ESC to exit")
    print("\nNotice how the UI elements scale and reposition as you resize!")
    print("Starting demo...\n")
    
    try:
        # Create game objects with some interesting data
        player = Player()
        player.money = 250
        player.fishCount = 12
        
        stats = Stats()
        stats.totalFishCaught = 45
        stats.hoursSpentFishing = 8
        
        timeService = TimeService(player, stats)
        timeService.day = 3
        timeService.time = 16  # 4:00 PM
        
        prompt = Prompt("Try resizing the window to see responsive layout!")
        
        # Create pygame UI
        ui = UserInterfaceFactory.create_user_interface(
            UIType.PYGAME, prompt, timeService, player
        )
        
        print("Pygame window opened! Try resizing it.")
        
        # Demo options
        options = [
            "Go fishing at the docks",
            "Visit the general store",
            "Rest at home",
            "Check your statistics",
            "Exit demo"
        ]
        
        # Show the UI and wait for user interaction
        choice = ui.showOptions("Welcome to the FishE Responsive UI Demo!", options)
        
        # Handle the choice
        if choice == "5":
            print("Demo exited by user selection.")
        else:
            print(f"User selected option {choice}: {options[int(choice)-1]}")
        
        ui.cleanup()
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"Demo error: {e}")
        return 1
    
    print("Demo completed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())