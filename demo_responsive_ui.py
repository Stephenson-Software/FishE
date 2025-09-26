#!/usr/bin/env python3
"""
Simple demo script to show the responsive UI working with different window sizes.
"""

import os
import sys
import pygame

# Set up for headless testing
os.environ['SDL_VIDEODRIVER'] = 'dummy'

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ui.enum.uiType import UIType
from ui.userInterfaceFactory import UserInterfaceFactory
from player.player import Player
from prompt.prompt import Prompt
from stats.stats import Stats
from world.timeService import TimeService


def demo_responsive_features():
    """Demonstrate the responsive UI features"""
    print("=== FishE Responsive UI Demo ===")
    print()
    
    # Create game objects with some sample data
    player = Player()
    player.money = 150
    player.fishCount = 8
    
    stats = Stats()
    timeService = TimeService(player, stats)
    timeService.day = 3
    timeService.time = 14  # 2:00 PM
    
    prompt = Prompt("Choose your next adventure!")
    
    # Create pygame UI
    ui = UserInterfaceFactory.create_user_interface(UIType.PYGAME, prompt, timeService, player)
    print("✓ Responsive Pygame UI created")
    
    # Test different window sizes
    test_sizes = [
        (600, 400),   # Minimum size
        (800, 600),   # Default size
        (1024, 768),  # Larger size
        (1200, 900),  # Extra large
    ]
    
    options = ["Go fishing", "Visit shop", "Rest at home", "Check stats", "Quit"]
    
    for width, height in test_sizes:
        print(f"✓ Testing {width}x{height} window size")
        
        # Resize the UI
        ui._handle_resize(width, height)
        
        # Verify the resize worked
        assert ui.width == width, f"Width mismatch: expected {width}, got {ui.width}"
        assert ui.height == height, f"Height mismatch: expected {height}, got {ui.height}"
        
        # Test that drawing doesn't crash with the new size
        ui._draw_game_screen("Responsive UI Test", options)
        pygame.display.flip()
        
        # Show font scaling information
        font_info = f"Fonts: {ui.font_large.get_height()}px/{ui.font_medium.get_height()}px/{ui.font_small.get_height()}px"
        print(f"  - {font_info}")
        
    # Test minimum size constraints
    print("✓ Testing minimum size constraints")
    ui._handle_resize(300, 200)  # Below minimum
    assert ui.width >= ui.min_width, f"Width constraint failed: {ui.width} < {ui.min_width}"
    assert ui.height >= ui.min_height, f"Height constraint failed: {ui.height} < {ui.min_height}"
    print(f"  - Enforced minimum size: {ui.width}x{ui.height}")
    
    ui.cleanup()
    print()
    print("✓ All responsive UI features working correctly!")
    print()
    print("Key Features Implemented:")
    print("  • Window resizing with VIDEORESIZE event handling")
    print("  • Proportional layout that scales with screen size")
    print("  • Dynamic font scaling based on window dimensions")
    print("  • Minimum size constraints (600x400)")
    print("  • Percentage-based positioning for all UI elements")
    print()
    print("Usage:")
    print("  python3 src/fishE.py --ui pygame")
    print("  (Then resize the window to see responsive behavior)")


if __name__ == "__main__":
    demo_responsive_features()