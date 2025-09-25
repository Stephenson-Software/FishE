#!/usr/bin/env python3
"""
Create a mock screenshot showing what the pygame UI looks like
"""

import sys
import os

# Add src to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set pygame to use a null driver for screenshot creation
os.environ['SDL_VIDEODRIVER'] = 'dummy'

import pygame
from ui.enum.uiType import UIType
from ui.userInterfaceFactory import UserInterfaceFactory
from player.player import Player
from prompt.prompt import Prompt
from stats.stats import Stats
from world.timeService import TimeService


def create_mock_screenshot():
    """Create a screenshot of what the pygame UI would look like"""
    try:
        # Create game objects
        player = Player()
        player.money = 150  # Give some money for the demo
        player.fishCount = 5  # Give some fish
        stats = Stats()
        timeService = TimeService(player, stats)
        timeService.day = 3  # Day 3
        timeService.time = 14  # 2:00 PM
        prompt = Prompt("Welcome to the docks!")
        
        # Create pygame UI
        ui = UserInterfaceFactory.create_user_interface(
            UIType.PYGAME, prompt, timeService, player
        )
        
        # Set up some options like the docks location
        options = ["Fish", "Go Home", "Go to Shop", "Go to Tavern", "Go to Bank"]
        descriptor = "You breathe in the fresh air. Salty."
        
        # Draw the UI
        ui._draw_game_screen(descriptor, options)
        
        # Save screenshot
        pygame.image.save(ui.screen, "pygame_ui_screenshot.png")
        print("Screenshot saved as pygame_ui_screenshot.png")
        
        ui.cleanup()
        
        return True
        
    except Exception as e:
        print(f"Failed to create screenshot: {e}")
        return False


if __name__ == "__main__":
    if create_mock_screenshot():
        print("Mock pygame UI screenshot created successfully!")
    else:
        print("Could not create screenshot in this environment.")