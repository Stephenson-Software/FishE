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
        
        # Screen settings
        self.width = 800
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("FishE - Text-based Fishing Game")
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GRAY = (128, 128, 128)
        self.DARK_GRAY = (64, 64, 64)
        self.BLUE = (0, 100, 200)
        self.LIGHT_BLUE = (100, 150, 255)
        
        # Fonts
        self.font_large = pygame.font.Font(None, 36)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)
        
        # UI state
        self.current_options = []
        self.selected_option = 0
        self.waiting_for_input = False

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
        """Draw the main game screen"""
        # Clear screen
        self.screen.fill(self.BLACK)
        
        y_offset = 50
        
        # Draw descriptor
        desc_surface = self.font_large.render(descriptor, True, self.WHITE)
        desc_rect = desc_surface.get_rect(center=(self.width // 2, y_offset))
        self.screen.blit(desc_surface, desc_rect)
        y_offset += 80
        
        # Draw divider
        pygame.draw.line(self.screen, self.GRAY, (50, y_offset), (self.width - 50, y_offset), 2)
        y_offset += 30
        
        # Draw game status
        status_lines = [
            f"Day {self.timeService.day}",
            f"Time: {self.times[self.timeService.time]}",
            f"Money: ${self.player.money}",
            f"Fish: {self.player.fishCount}"
        ]
        
        for line in status_lines:
            text_surface = self.font_medium.render(line, True, self.WHITE)
            self.screen.blit(text_surface, (100, y_offset))
            y_offset += 30
        
        y_offset += 20
        
        # Draw current prompt
        prompt_surface = self.font_medium.render(self.currentPrompt.text, True, self.LIGHT_BLUE)
        self.screen.blit(prompt_surface, (100, y_offset))
        y_offset += 50
        
        # Draw another divider
        pygame.draw.line(self.screen, self.GRAY, (50, y_offset), (self.width - 50, y_offset), 2)
        y_offset += 30
        
        # Draw options
        for i, option in enumerate(optionList):
            color = self.LIGHT_BLUE if i == self.selected_option else self.WHITE
            option_text = f"[{i + 1}] {option}"
            
            # Draw selection highlight
            if i == self.selected_option:
                rect = pygame.Rect(80, y_offset - 5, self.width - 160, 35)
                pygame.draw.rect(self.screen, self.DARK_GRAY, rect)
            
            option_surface = self.font_medium.render(option_text, True, color)
            self.screen.blit(option_surface, (100, y_offset))
            y_offset += 40
        
        # Draw instructions
        y_offset += 30
        instructions = [
            "Use UP/DOWN arrows or number keys to select",
            "Press ENTER or SPACE to choose"
        ]
        
        for instruction in instructions:
            inst_surface = self.font_small.render(instruction, True, self.GRAY)
            inst_rect = inst_surface.get_rect(center=(self.width // 2, y_offset))
            self.screen.blit(inst_surface, inst_rect)
            y_offset += 25
    
    def cleanup(self):
        """Clean up pygame resources"""
        pygame.quit()