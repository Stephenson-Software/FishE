#!/usr/bin/env python3
"""
Create a demonstration screenshot showing the responsive UI at different window sizes.
This creates static images showing how the UI adapts to different screen sizes.
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


def create_screenshots():
    """Create screenshots at different window sizes"""
    print("Creating demonstration screenshots...")
    
    # Create game objects with interesting data
    player = Player()
    player.money = 347
    player.fishCount = 23
    
    stats = Stats()
    stats.totalFishCaught = 156
    stats.hoursSpentFishing = 24
    
    timeService = TimeService(player, stats)
    timeService.day = 5
    timeService.time = 10  # 10:00 AM
    
    prompt = Prompt("The responsive UI adapts to any window size!")
    
    # Test options
    options = [
        "Cast your line at the peaceful docks",
        "Browse wares at the general store", 
        "Rest and recover at home",
        "Drink and gamble at the tavern",
        "Make transactions at the bank"
    ]
    
    # Different window sizes to demonstrate
    test_sizes = [
        (600, 400, "small"),
        (800, 600, "medium"), 
        (1024, 768, "large"),
        (1200, 900, "xlarge")
    ]
    
    for width, height, size_name in test_sizes:
        print(f"Creating {size_name} screenshot ({width}x{height})...")
        
        # Create UI instance
        ui = UserInterfaceFactory.create_user_interface(
            UIType.PYGAME, prompt, timeService, player
        )
        
        # Resize to target size
        ui._handle_resize(width, height)
        
        # Set selected option for visual variety
        ui.selected_option = 1 if size_name == "small" else 2
        
        # Draw the screen
        ui._draw_game_screen("Welcome to FishE - Responsive UI Demo", options)
        
        # Save screenshot
        filename = f"responsive_ui_{size_name}_{width}x{height}.png"
        pygame.image.save(ui.screen, filename)
        print(f"  Saved: {filename}")
        
        ui.cleanup()
    
    print("\nScreenshots created successfully!")
    print("These demonstrate how the UI elements scale and reposition based on window size:")
    print("  • Text sizes scale proportionally")
    print("  • Margins and spacing adapt to screen dimensions") 
    print("  • Selection highlights adjust to content width")
    print("  • All elements maintain proper proportions")


def main():
    """Main function"""
    # Set up pygame for screenshot generation
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    
    try:
        create_screenshots()
        return 0
    except Exception as e:
        print(f"Error creating screenshots: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())