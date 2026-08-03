import pygame
import sys
import time
from ui.baseUserInterface import (
    BaseUserInterface,
    unavailableMessage,
    unavailableSuffix,
)
from prompt.prompt import Prompt
from player.player import Player
from world.timeService import TimeService
from housing import housing


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
        self.screen = pygame.display.set_mode(
            (self.width, self.height), pygame.RESIZABLE
        )
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
        self.screen = pygame.display.set_mode(
            (self.width, self.height), pygame.RESIZABLE
        )

        # Update fonts for new screen size
        self._update_fonts()

    def _textWidth(self):
        """Pixel width available for text, inside the same 6% side margins the
        rest of the layout uses."""
        return int(self.width - 2 * (self.width * 0.06))

    def _splitLongWord(self, word, font, maxWidth):
        """Break a single word wider than maxWidth into chunks that fit.

        Word wrapping alone can't help a word that is itself too wide, and
        pygame clips whatever runs past the window edge, so it is split by
        character instead of being left unreadable."""
        chunks = []
        while len(word) > 1 and font.size(word)[0] > maxWidth:
            fit = 1
            while fit < len(word) and font.size(word[: fit + 1])[0] <= maxWidth:
                fit += 1
            chunks.append(word[:fit])
            word = word[fit:]
        chunks.append(word)
        return chunks

    def _wrapText(self, text, font, maxWidth):
        """Split text into lines that fit maxWidth pixels, keeping newlines.

        pygame's Font.render draws a single row and renders "\\n" as a glyph
        rather than a line break, so any multi-line or window-width text has to
        be broken up here before it is drawn. Split out from the drawing code so
        the layout can be tested (font.size works headless; mocking
        pygame.font.Font.render doesn't)."""
        lines = []
        for paragraph in text.split("\n"):
            words = []
            for word in paragraph.split(" "):
                words.extend(self._splitLongWord(word, font, maxWidth))

            current = ""
            for word in words:
                candidate = "%s %s" % (current, word) if current else word
                if current and font.size(candidate)[0] > maxWidth:
                    lines.append(current)
                    current = word
                else:
                    current = candidate
            lines.append(current)
        return lines

    def lotsOfSpace(self):
        # For pygame, this just clears the screen
        self.screen.fill(self.BLACK)

    def divider(self):
        # For pygame, we'll draw a horizontal line
        # This will be called during drawing, so we'll store it as a flag
        pass

    def _selectableIndexes(self, reasons):
        """Indexes the highlight is allowed to land on, in order.

        Options the game would refuse are drawn greyed out but skipped over by
        the arrow keys, so holding DOWN never parks the cursor somewhere ENTER
        does nothing."""
        return [index for index, reason in enumerate(reasons) if reason is None]

    def _initialSelection(self, reasons):
        """Where the highlight opens: the first option the player can choose,
        so a menu whose first row is greyed out doesn't start on it."""
        selectable = self._selectableIndexes(reasons)
        return selectable[0] if selectable else 0

    def _moveSelection(self, reasons, step):
        """The next selectable option in the given direction, wrapping around."""
        selectable = self._selectableIndexes(reasons)
        if not selectable:
            return self.selected_option
        if self.selected_option in selectable:
            position = selectable.index(self.selected_option)
        else:
            # Nothing selectable is highlighted yet (an empty menu can't happen,
            # but a stale highlight can) - step in from the nearest end.
            position = -1 if step > 0 else 0
        return selectable[(position + step) % len(selectable)]

    def _optionRows(self, optionList, reasons):
        """(text, isUnavailable) per option row, ready to draw.

        Split out from _draw_game_screen for the same reason as _statusLines:
        the wording can be asserted without a real font."""
        return [
            (
                "[%d] %s%s" % (index + 1, option, unavailableSuffix(reason)),
                reason is not None,
            )
            for index, (option, reason) in enumerate(zip(optionList, reasons))
        ]

    def showOptions(self, descriptor, optionList, unavailableOptions=None):
        reasons = self.unavailableReasons(optionList, unavailableOptions)
        self.current_options = optionList
        self.selected_option = self._initialSelection(reasons)
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
                        self.selected_option = self._moveSelection(reasons, -1)
                    elif event.key == pygame.K_DOWN:
                        self.selected_option = self._moveSelection(reasons, 1)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        if reasons[self.selected_option] is None:
                            self.waiting_for_input = False
                            return str(self.selected_option + 1)
                    elif event.key >= pygame.K_1 and event.key <= pygame.K_9:
                        option_num = event.key - pygame.K_1 + 1
                        if option_num <= len(optionList):
                            reason = reasons[option_num - 1]
                            if reason is None:
                                self.waiting_for_input = False
                                return str(option_num)
                            # Say why instead of swallowing the keypress; the
                            # prompt is redrawn on the next frame.
                            self.currentPrompt.text = unavailableMessage(reason)

            # Draw the UI
            self._draw_game_screen(descriptor, optionList, reasons)

            # Update display
            pygame.display.flip()
            pygame.time.Clock().tick(60)  # 60 FPS

        return str(self.selected_option + 1)

    def _statusLines(self):
        """Plain-text status rows shown on the game screen. Split out from
        _draw_game_screen so the content can be tested without a real font
        (pygame.font.Font doesn't allow mocking its render method).

        Stats are grouped a few per row - the same compact header the web
        front-end renders, rather than the console's one-per-line column - so
        the block leaves the option list room in the default window."""
        clock = [f"Day {self.timeService.day}", self.times[self.timeService.time]]
        # The location and goal entries only appear once the game loop has set
        # them, matching the console and web front-ends (empty hides the entry).
        if self.currentLocationName:
            clock.append(f"Location: {self.currentLocationName}")

        wallet = [
            "Money: $%.2f" % self.player.money,
            f"Fish: {self.player.fishCount}",
            f"Energy: {self.player.energy}/{housing.maxEnergy(self.player)}",
        ]

        progress = []
        if self.goalProgress:
            progress.append(f"Goal: {self.goalProgress}")
        if self.player.operatorMode:
            progress.append("[OPERATOR MODE]")

        rows = [clock, wallet]
        if progress:
            rows.append(progress)
        return [" | ".join(row) for row in rows]

    def _gameScreenLayout(self, statusLineCount, promptLineCount, optionCount):
        """Vertical layout of the game screen, as pixel y positions.

        Split out from the drawing for the same reason as _statusLines. The
        option rows are sized against the space actually left over, because the
        blocks above them vary: the status block grows with the location/goal
        entries and the prompt wraps to as many lines as it needs, which in the
        default window would otherwise push the options off the bottom edge."""
        lineHeight = max(self.font_medium.get_linesize(), self.height * 0.04)

        descriptorY = self.height * 0.08
        dividerY = descriptorY + self.height * 0.13
        statusY = dividerY + self.height * 0.05
        promptY = statusY + statusLineCount * lineHeight + self.height * 0.03
        secondDividerY = promptY + promptLineCount * lineHeight + self.height * 0.03
        optionsY = secondDividerY + self.height * 0.05

        # Options shrink toward the font's own line height (never below it, or
        # they would overlap) so that as many as the game offers stay on screen.
        instructionsTop = self.height - (self.height * 0.15)
        optionHeight = max(25, self.height * 0.06)
        if optionCount > 0:
            optionHeight = max(
                self.font_medium.get_linesize(),
                min(optionHeight, (instructionsTop - optionsY) / optionCount),
            )

        # Sits below the options, but never so low that the second instruction
        # line (drawn one instruction_spacing further down) falls off screen.
        instructionsY = min(
            max(
                optionsY + optionCount * optionHeight + self.height * 0.05,
                instructionsTop,
            )
            + 30,
            self.height - 2 * (self.height * 0.04),
        )

        return {
            "lineHeight": lineHeight,
            "descriptorY": descriptorY,
            "dividerY": dividerY,
            "statusY": statusY,
            "promptY": promptY,
            "secondDividerY": secondDividerY,
            "optionsY": optionsY,
            "optionHeight": optionHeight,
            "instructionsY": instructionsY,
        }

    def _draw_game_screen(self, descriptor, optionList, reasons=None):
        """Draw the main game screen with responsive layout"""
        if reasons is None:
            reasons = [None] * len(optionList)
        # Clear screen
        self.screen.fill(self.BLACK)

        # Use proportional positioning based on screen dimensions
        margin_x = self.width * 0.06  # 6% margin from left/right
        status_x = margin_x + (self.width * 0.06)  # Indent status lines
        text_width = int(self.width - margin_x - status_x)

        status_lines = self._statusLines()
        # The prompt carries appended milestone/goal announcements, which easily
        # outrun the window width on a single line.
        prompt_lines = self._wrapText(
            self.currentPrompt.text, self.font_medium, text_width
        )
        layout = self._gameScreenLayout(
            len(status_lines), len(prompt_lines), len(optionList)
        )
        line_height = layout["lineHeight"]

        # Draw descriptor - centered and scaled
        desc_surface = self.font_large.render(descriptor, True, self.WHITE)
        desc_rect = desc_surface.get_rect(
            center=(self.width // 2, layout["descriptorY"])
        )
        self.screen.blit(desc_surface, desc_rect)

        # Draw dividers - proportional margins
        divider_start = margin_x
        divider_end = self.width - margin_x
        for divider_y in (layout["dividerY"], layout["secondDividerY"]):
            pygame.draw.line(
                self.screen,
                self.GRAY,
                (divider_start, divider_y),
                (divider_end, divider_y),
                2,
            )

        # Draw game status
        y_offset = layout["statusY"]
        for line in status_lines:
            text_surface = self.font_medium.render(line, True, self.WHITE)
            self.screen.blit(text_surface, (status_x, y_offset))
            y_offset += line_height

        # Draw current prompt
        y_offset = layout["promptY"]
        for line in prompt_lines:
            prompt_surface = self.font_medium.render(line, True, self.LIGHT_BLUE)
            self.screen.blit(prompt_surface, (status_x, y_offset))
            y_offset += line_height

        # Draw options with responsive sizing
        option_height = layout["optionHeight"]
        highlight_margin = self.width * 0.02  # 2% margin for highlight
        y_offset = layout["optionsY"]

        for i, (option_text, unavailable) in enumerate(
            self._optionRows(optionList, reasons)
        ):
            # Greyed out is how an unavailable option reads here, matching the
            # web front-end's disabled buttons; the highlight never lands on
            # one, so the selected colour can't apply to it.
            if unavailable:
                color = self.GRAY
            else:
                color = self.LIGHT_BLUE if i == self.selected_option else self.WHITE

            # Draw selection highlight with proportional sizing
            if i == self.selected_option and not unavailable:
                highlight_x = margin_x + highlight_margin
                highlight_width = self.width - 2 * (margin_x + highlight_margin)
                rect = pygame.Rect(
                    highlight_x, y_offset - 5, highlight_width, option_height
                )
                pygame.draw.rect(self.screen, self.DARK_GRAY, rect)

            option_surface = self.font_medium.render(option_text, True, color)
            self.screen.blit(option_surface, (status_x, y_offset))
            y_offset += option_height

        # Draw instructions at bottom with proportional spacing
        y_offset = layout["instructionsY"]
        instructions = [
            "Use UP/DOWN arrows or number keys to select",
            "Press ENTER or SPACE to choose",
        ]

        instruction_spacing = self.height * 0.04  # 4% spacing between instructions

        for instruction in instructions:
            inst_surface = self.font_small.render(instruction, True, self.GRAY)
            inst_rect = inst_surface.get_rect(center=(self.width // 2, y_offset))
            self.screen.blit(inst_surface, inst_rect)
            y_offset += instruction_spacing

    def _dialogueScrollBounds(self, lineCount):
        """(visible line count, maximum scroll offset) for the dialogue area."""
        lineHeight = max(self.font_medium.get_linesize(), 1)
        top = self.height * 0.2
        bottom = self.height - self.height * 0.15  # room for the hint line
        visible = max(1, int((bottom - top) // lineHeight))
        return visible, max(0, lineCount - visible)

    def _draw_dialogue(self, lines, scroll, visible):
        """Draw the visible window of a wrapped dialogue plus its hint line."""
        self.screen.fill(self.BLACK)
        margin_x = self.width * 0.06
        lineHeight = max(self.font_medium.get_linesize(), 1)
        y_offset = self.height * 0.2

        for line in lines[scroll : scroll + visible]:
            self.screen.blit(
                self.font_medium.render(line, True, self.WHITE), (margin_x, y_offset)
            )
            y_offset += lineHeight

        hint = self._dialogueHint(len(lines), scroll, visible)
        hint_surface = self.font_small.render(hint, True, self.GRAY)
        hint_rect = hint_surface.get_rect(
            center=(self.width // 2, self.height - self.height * 0.1)
        )
        self.screen.blit(hint_surface, hint_rect)

    def _dialogueHint(self, lineCount, scroll, visible):
        """The footer hint for a dialogue - it only mentions scrolling when
        there is something off screen to scroll to."""
        if lineCount <= visible:
            return "Press any key to continue"
        return "UP/DOWN to scroll (%d-%d of %d) - any other key to continue" % (
            scroll + 1,
            min(scroll + visible, lineCount),
            lineCount,
        )

    def showDialogue(self, text):
        """Render a block of text and wait for the player to press a key.

        The text is wrapped first (see _wrapText) and, when it is taller than the
        window, scrolled with UP/DOWN - the stats and retirement screens are long
        enough to need it. Any other key continues."""
        lines = self._wrapText(text, self.font_medium, self._textWidth())
        visible, maxScroll = self._dialogueScrollBounds(len(lines))
        scroll = 0
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.cleanup()
                    sys.exit()
                elif event.type == pygame.VIDEORESIZE:
                    self._handle_resize(event.w, event.h)
                    # The wrap depends on the window width and the visible line
                    # count on its height, so both are redone after a resize.
                    lines = self._wrapText(text, self.font_medium, self._textWidth())
                    visible, maxScroll = self._dialogueScrollBounds(len(lines))
                    scroll = min(scroll, maxScroll)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        scroll = max(0, scroll - 1)
                    elif event.key == pygame.K_DOWN:
                        scroll = min(maxScroll, scroll + 1)
                    else:
                        waiting = False

            self._draw_dialogue(lines, scroll, visible)
            pygame.display.flip()
            pygame.time.Clock().tick(60)

        self.currentPrompt.text = "What would you like to do?"

    def promptForText(self, promptText):
        """Capture a line of text typed in the pygame window (Enter submits)."""
        entered = ""
        typing = True
        while typing:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.cleanup()
                    sys.exit()
                elif event.type == pygame.VIDEORESIZE:
                    self._handle_resize(event.w, event.h)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        typing = False
                    elif event.key == pygame.K_BACKSPACE:
                        entered = entered[:-1]
                    elif event.unicode and event.unicode.isprintable():
                        entered += event.unicode

            self.screen.fill(self.BLACK)
            margin_x = self.width * 0.06
            lineHeight = max(self.font_medium.get_linesize(), 1)
            # The prompt is the game's current prompt text, which can carry
            # appended announcements - wrap it rather than let it run off screen.
            y_offset = self.height * 0.3
            for line in self._wrapText(promptText, self.font_medium, self._textWidth()):
                prompt_surface = self.font_medium.render(line, True, self.WHITE)
                self.screen.blit(prompt_surface, (margin_x, y_offset))
                y_offset += lineHeight

            # Wrapped too - a long answer (a business name, say) would otherwise
            # type its way off the right edge of the window.
            y_offset = max(y_offset + lineHeight, self.height * 0.45)
            for line in self._wrapText(
                "> " + entered, self.font_medium, self._textWidth()
            ):
                entry_surface = self.font_medium.render(line, True, self.LIGHT_BLUE)
                self.screen.blit(entry_surface, (margin_x, y_offset))
                y_offset += lineHeight

            hint_surface = self.font_small.render(
                "Type your answer and press ENTER", True, self.GRAY
            )
            self.screen.blit(
                hint_surface, (margin_x, max(y_offset + lineHeight, self.height * 0.6))
            )
            pygame.display.flip()
            pygame.time.Clock().tick(60)

        return entered

    def showBusy(self, message, seconds=1.0):
        """Draw a message and hold it for `seconds`, taking no input.

        The window keeps being redrawn and its events pumped throughout, so the
        pause looks like the game working rather than the window hanging."""
        endTime = time.time() + seconds
        while time.time() < endTime:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.cleanup()
                    sys.exit()
                elif event.type == pygame.VIDEORESIZE:
                    self._handle_resize(event.w, event.h)

            self._draw_busy(message)
            pygame.display.flip()
            pygame.time.Clock().tick(60)

    def _draw_busy(self, message):
        """Draw the wrapped busy message. Split out from showBusy so the layout
        can be tested without driving the wait loop."""
        self.screen.fill(self.BLACK)
        margin_x = self.width * 0.06
        lineHeight = max(self.font_medium.get_linesize(), 1)
        y_offset = self.height * 0.4
        for line in self._wrapText(message, self.font_medium, self._textWidth()):
            self.screen.blit(
                self.font_medium.render(line, True, self.WHITE), (margin_x, y_offset)
            )
            y_offset += lineHeight

    def timedKeyPress(self, message):
        """Show a message and return the seconds until the player presses a key."""
        startTime = time.time()
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.cleanup()
                    sys.exit()
                elif event.type == pygame.VIDEORESIZE:
                    self._handle_resize(event.w, event.h)
                elif event.type == pygame.KEYDOWN:
                    waiting = False

            self.screen.fill(self.BLACK)
            margin_x = self.width * 0.06
            lineHeight = max(self.font_medium.get_linesize(), 1)
            y_offset = self.height * 0.4
            for line in self._wrapText(message, self.font_medium, self._textWidth()):
                message_surface = self.font_medium.render(line, True, self.WHITE)
                self.screen.blit(message_surface, (margin_x, y_offset))
                y_offset += lineHeight
            pygame.display.flip()
            pygame.time.Clock().tick(60)

        return time.time() - startTime

    def cleanup(self):
        """Clean up pygame resources"""
        pygame.quit()
