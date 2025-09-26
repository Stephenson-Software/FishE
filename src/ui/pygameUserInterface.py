import pygame
import sys
from ui.baseUserInterface import BaseUserInterface
from prompt.prompt import Prompt
from player.player import Player
from world.timeService import TimeService


# @author Daniel McCoy Stephenson
class PygameUserInterface(BaseUserInterface):
    """Pygame-based user interface implementation"""
    
    def __init__(self, currentPrompt: Prompt, timeService: TimeService, player: Player):
        super().__init__(currentPrompt, timeService, player)
        
        # Initialize pygame
        pygame.init()
        
        # Screen settings - now supports resizing
        self.min_width = 600
        self.min_height = 400
        self.width = 800
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("FishE - Text-based Fishing Game")
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GRAY = (128, 128, 128)
        self.DARK_GRAY = (64, 64, 64)
        self.BLUE = (0, 100, 200)
        self.LIGHT_BLUE = (100, 150, 255)
        
        # Font sizes that scale with screen size
        self._update_fonts()

        # UI state
        self.current_options = []
        self.selected_option = 0
        self.waiting_for_input = False

    def _update_fonts(self):
        """Update font sizes based on current screen dimensions"""
        # Scale fonts proportionally to screen size with better scaling
        base_width, base_height = 800, 600

        # Use a more conservative scaling approach
        width_scale = self.width / base_width
        height_scale = self.height / base_height
        scale_factor = min(width_scale, height_scale)

        # Don't scale too small - use a minimum scale factor
        scale_factor = max(0.5, scale_factor)

        # Calculate scaled sizes
        large_size = int(36 * scale_factor)
        medium_size = int(24 * scale_factor)
        small_size = int(18 * scale_factor)

        # Ensure minimum readable font sizes
        large_size = max(18, large_size)
        medium_size = max(14, medium_size)
        small_size = max(12, small_size)

        self.font_large = pygame.font.Font(None, large_size)
        self.font_medium = pygame.font.Font(None, medium_size)
        self.font_small = pygame.font.Font(None, small_size)

    def _handle_resize(self, new_width, new_height):
        """Handle window resize events"""
        # Enforce minimum window size
        self.width = max(new_width, self.min_width)
        self.height = max(new_height, self.min_height)

        # Recreate the display surface with new dimensions
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)

        # Update fonts for new screen size
        self._update_fonts()

    def lotsOfSpace(self):
        # For pygame, this just clears the screen
        self.screen.fill(self.BLACK)

    def divider(self):
        # For pygame, we'll draw a horizontal line
        # This will be called during drawing, so we'll store it as a flag
        pass

    def showOptions(self, descriptor, optionList):
        self.current_options = optionList
        self.selected_option = 0
        self.waiting_for_input = True
        
        while self.waiting_for_input:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.cleanup()
                    sys.exit()
                elif event.type == pygame.VIDEORESIZE:
                    # Handle window resize
                    self._handle_resize(event.w, event.h)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.selected_option = (self.selected_option - 1) % len(optionList)
                    elif event.key == pygame.K_DOWN:
                        self.selected_option = (self.selected_option + 1) % len(optionList)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        self.waiting_for_input = False
                        return str(self.selected_option + 1)
                    elif event.key >= pygame.K_1 and event.key <= pygame.K_9:
                        option_num = event.key - pygame.K_1 + 1
                        if option_num <= len(optionList):
                            self.waiting_for_input = False
                            return str(option_num)
            
            # Draw the UI
            self._draw_game_screen(descriptor, optionList)
            
            # Update display
            pygame.display.flip()
            pygame.time.Clock().tick(60)  # 60 FPS
        
        return str(self.selected_option + 1)
    
    def _draw_game_screen(self, descriptor, optionList):
        """Draw the main game screen with responsive layout"""
        # Clear screen
        self.screen.fill(self.BLACK)
        
        # Use proportional positioning based on screen dimensions
        margin_x = self.width * 0.06  # 6% margin from left/right
        margin_y = self.height * 0.08  # 8% margin from top
        y_offset = margin_y

        # Draw descriptor - centered and scaled
        desc_surface = self.font_large.render(descriptor, True, self.WHITE)
        desc_rect = desc_surface.get_rect(center=(self.width // 2, y_offset))
        self.screen.blit(desc_surface, desc_rect)
        y_offset += self.height * 0.13  # 13% of screen height

        # Draw divider - proportional margins
        divider_start = margin_x
        divider_end = self.width - margin_x
        pygame.draw.line(self.screen, self.GRAY, (divider_start, y_offset), (divider_end, y_offset), 2)
        y_offset += self.height * 0.05  # 5% spacing

        # Draw game status
        status_lines = [
            f"Day {self.timeService.day}",
            f"Time: {self.times[self.timeService.time]}",
            f"Money: ${self.player.money}",
            f"Fish: {self.player.fishCount}"
        ]
        
        status_x = margin_x + (self.width * 0.06)  # Indent status lines
        line_height = self.height * 0.05  # 5% of screen height per line

        for line in status_lines:
            text_surface = self.font_medium.render(line, True, self.WHITE)
            self.screen.blit(text_surface, (status_x, y_offset))
            y_offset += line_height

        y_offset += self.height * 0.03  # 3% extra spacing

        # Draw current prompt
        prompt_surface = self.font_medium.render(self.currentPrompt.text, True, self.LIGHT_BLUE)
        self.screen.blit(prompt_surface, (status_x, y_offset))
        y_offset += self.height * 0.08  # 8% spacing

        # Draw another divider
        pygame.draw.line(self.screen, self.GRAY, (divider_start, y_offset), (divider_end, y_offset), 2)
        y_offset += self.height * 0.05  # 5% spacing

        # Draw options with responsive sizing
        option_height = max(25, self.height * 0.06)  # At least 25px, or 6% of screen height
        highlight_margin = self.width * 0.02  # 2% margin for highlight

        # Draw options
        for i, option in enumerate(optionList):
            color = self.LIGHT_BLUE if i == self.selected_option else self.WHITE
            option_text = f"[{i + 1}] {option}"
            
            # Draw selection highlight with proportional sizing
            if i == self.selected_option:
                highlight_x = margin_x + highlight_margin
                highlight_width = self.width - 2 * (margin_x + highlight_margin)
                rect = pygame.Rect(highlight_x, y_offset - 5, highlight_width, option_height)
                pygame.draw.rect(self.screen, self.DARK_GRAY, rect)
            
            option_surface = self.font_medium.render(option_text, True, color)
            self.screen.blit(option_surface, (status_x, y_offset))
            y_offset += option_height

        # Draw instructions at bottom with proportional spacing
        instructions_start_y = self.height - (self.height * 0.15)  # 15% from bottom
        y_offset = max(y_offset + self.height * 0.05, instructions_start_y)  # Ensure minimum spacing

        # Draw instructions
        y_offset += 30
        instructions = [
            "Use UP/DOWN arrows or number keys to select",
            "Press ENTER or SPACE to choose"
        ]
        
        instruction_spacing = self.height * 0.04  # 4% spacing between instructions

        for instruction in instructions:
            inst_surface = self.font_small.render(instruction, True, self.GRAY)
            inst_rect = inst_surface.get_rect(center=(self.width // 2, y_offset))
            self.screen.blit(inst_surface, inst_rect)
            y_offset += instruction_spacing

    def cleanup(self):
        """Clean up pygame resources"""
        pygame.quit()