#!/usr/bin/env python3
"""
Demo script to showcase both console and pygame UI types for FishE
"""

import sys
import os
import time

# Add src to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ui.enum.uiType import UIType
from ui.userInterfaceFactory import UserInterfaceFactory
from player.player import Player
from prompt.prompt import Prompt
from stats.stats import Stats
from world.timeService import TimeService


def demo_console_ui():
    """Demo the console UI"""
    print("=== Console UI Demo ===")
    
    # Create game objects
    player = Player()
    stats = Stats()
    timeService = TimeService(player, stats)
    prompt = Prompt("Welcome to FishE Console Demo!")
    
    # Create console UI
    ui = UserInterfaceFactory.create_user_interface(
        UIType.CONSOLE, prompt, timeService, player
    )
    
    print("Console UI created successfully!")
    print("This is the traditional text-based interface.")
    print("UI Type:", type(ui).__name__)
    
    # Show some UI elements
    print("\nDemonstrating UI methods:")
    print("- lotsOfSpace() clears the screen")
    print("- divider() shows separator lines")
    print("- showOptions() displays interactive menu\n")
    
    ui.cleanup()
    

def demo_pygame_ui():
    """Demo the pygame UI (without actually showing it in headless environment)"""
    print("\n=== Pygame UI Demo ===")
    
    try:
        # Create game objects
        player = Player()
        stats = Stats()
        timeService = TimeService(player, stats)
        prompt = Prompt("Welcome to FishE Pygame Demo!")
        
        # Create pygame UI
        ui = UserInterfaceFactory.create_user_interface(
            UIType.PYGAME, prompt, timeService, player
        )
        
        print("Pygame UI created successfully!")
        print("This is the windowed interface with graphics.")
        print("UI Type:", type(ui).__name__)
        print("Features:")
        print("- Windowed display (800x600)")
        print("- Keyboard navigation (UP/DOWN arrows)")
        print("- Visual highlighting of selected options")
        print("- Number key shortcuts")
        print("- Clean typography and colors")
        
        ui.cleanup()
        
    except Exception as e:
        print(f"Pygame UI creation failed (expected in headless environment): {e}")
        print("Features that would be available:")
        print("- Windowed display (800x600)")
        print("- Keyboard navigation (UP/DOWN arrows)")
        print("- Visual highlighting of selected options")
        print("- Number key shortcuts")
        print("- Clean typography and colors")


def main():
    """Main demo function"""
    print("FishE Multi-UI Demo")
    print("==================")
    print("This demo shows how FishE now supports multiple UI types:")
    print("1. Console UI (traditional text-based)")
    print("2. Pygame UI (windowed with graphics)")
    print()
    
    demo_console_ui()
    demo_pygame_ui()
    
    print("\n=== Usage Instructions ===")
    print("To run FishE with console UI (default):")
    print("  python3 src/fishE.py")
    print("  python3 src/fishE.py --ui console")
    print()
    print("To run FishE with pygame UI:")
    print("  python3 src/fishE.py --ui pygame")
    print()
    print("Both UIs provide the same game functionality with different interfaces!")


if __name__ == "__main__":
    main()