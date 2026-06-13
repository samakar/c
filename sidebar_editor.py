#!/usr/bin/env python3
"""
Terminal text editor with sidebar file browser
Uses curses for split-screen interface
"""

import curses
import os
import sys

class SidebarEditor:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.current_file = None
        self.content = []
        self.cursor_y = 0
        self.cursor_x = 0
        self.scroll_offset = 0
        self.sidebar_width = 25
        self.files = []
        self.selected_file_idx = 0
        self.mode = 'normal'  # normal or insert
        self.status_message = "Press 'h' for help"

        # Initialize colors
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Selected
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)   # Sidebar
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)   # Status bar
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Modified indicator

        self.load_file_list()

    def load_file_list(self):
        """Load list of files in current directory"""
        try:
            self.files = sorted([f for f in os.listdir('.') if os.path.isfile(f)])
        except:
            self.files = []

    def load_file(self, filename):
        """Load a file into the editor"""
        try:
            with open(filename, 'r') as f:
                self.content = f.read().splitlines()
            self.current_file = filename
            self.cursor_y = 0
            self.cursor_x = 0
            self.scroll_offset = 0
            self.status_message = f"Loaded: {filename}"
            return True
        except FileNotFoundError:
            self.content = []
            self.current_file = filename
            self.status_message = f"New file: {filename}"
            return True
        except Exception as e:
            self.status_message = f"Error: {str(e)}"
            return False

    def save_file(self):
        """Save current file"""
        if not self.current_file:
            self.status_message = "No file loaded"
            return False

        try:
            with open(self.current_file, 'w') as f:
                f.write('\n'.join(self.content))
            self.status_message = f"Saved: {self.current_file}"
            self.load_file_list()
            return True
        except Exception as e:
            self.status_message = f"Save error: {str(e)}"
            return False

    def draw_sidebar(self):
        """Draw the file browser sidebar"""
        height, width = self.stdscr.getmaxyx()

        # Draw sidebar background
        for i in range(height - 2):
            self.stdscr.addstr(i, 0, " " * self.sidebar_width, curses.color_pair(2))

        # Draw title
        title = " FILES "
        self.stdscr.addstr(0, 0, title.ljust(self.sidebar_width), curses.color_pair(2) | curses.A_BOLD)

        # Draw files
        visible_files = height - 4
        start_idx = max(0, self.selected_file_idx - visible_files + 1)

        for i, file_idx in enumerate(range(start_idx, min(len(self.files), start_idx + visible_files))):
            y_pos = i + 2
            if y_pos >= height - 2:
                break

            filename = self.files[file_idx]
            display_name = filename[:self.sidebar_width - 3]

            if file_idx == self.selected_file_idx:
                self.stdscr.addstr(y_pos, 0, f" {display_name}".ljust(self.sidebar_width), curses.color_pair(1))
            else:
                self.stdscr.addstr(y_pos, 0, f" {display_name}".ljust(self.sidebar_width), curses.color_pair(2))

    def draw_editor(self):
        """Draw the main editor area"""
        height, width = self.stdscr.getmaxyx()
        editor_x = self.sidebar_width + 1
        editor_width = width - editor_x - 1

        # Draw vertical separator
        for i in range(height - 2):
            self.stdscr.addstr(i, self.sidebar_width, "│")

        # Draw file name
        if self.current_file:
            title = f" {self.current_file} "
            if len(title) > editor_width:
                title = title[:editor_width - 3] + "..."
            self.stdscr.addstr(0, editor_x, title.ljust(editor_width), curses.A_BOLD)

        # Draw content
        visible_lines = height - 4
        for i in range(visible_lines):
            line_num = i + self.scroll_offset
            y_pos = i + 2

            if line_num < len(self.content):
                line = self.content[line_num]
                # Truncate or pad line to fit
                if len(line) > editor_width:
                    display_line = line[:editor_width]
                else:
                    display_line = line.ljust(editor_width)

                try:
                    self.stdscr.addstr(y_pos, editor_x, display_line[:editor_width])
                except:
                    pass
            else:
                try:
                    self.stdscr.addstr(y_pos, editor_x, " " * editor_width)
                except:
                    pass

    def draw_status_bar(self):
        """Draw the status bar at bottom"""
        height, width = self.stdscr.getmaxyx()

        # Mode indicator
        mode_text = "INSERT" if self.mode == 'insert' else "NORMAL"

        # Position info
        pos_info = f"Ln {self.cursor_y + 1}, Col {self.cursor_x + 1}"

        # Build status line
        status_left = f" {mode_text} | {self.status_message}"
        status_right = f"{pos_info} "

        padding = width - len(status_left) - len(status_right)
        status_line = status_left + " " * max(0, padding) + status_right

        try:
            self.stdscr.addstr(height - 2, 0, status_line[:width], curses.color_pair(3))
        except:
            pass

    def draw_help_bar(self):
        """Draw help bar at bottom"""
        height, width = self.stdscr.getmaxyx()
        help_text = "^S:Save ^Q:Quit ^O:Open  i:Insert ESC:Normal  TAB:Switch pane  ↑↓:Navigate"

        try:
            self.stdscr.addstr(height - 1, 0, help_text[:width].ljust(width))
        except:
            pass

    def draw(self):
        """Draw the entire interface"""
        self.stdscr.clear()
        self.draw_sidebar()
        self.draw_editor()
        self.draw_status_bar()
        self.draw_help_bar()
        self.stdscr.refresh()

    def handle_insert_mode(self, key):
        """Handle keypresses in insert mode"""
        height, width = self.stdscr.getmaxyx()
        editor_width = width - self.sidebar_width - 2

        if key == 27:  # ESC
            self.mode = 'normal'
            self.status_message = "Normal mode"
        elif key == curses.KEY_BACKSPACE or key == 127:
            if self.cursor_x > 0:
                line = self.content[self.cursor_y]
                self.content[self.cursor_y] = line[:self.cursor_x - 1] + line[self.cursor_x:]
                self.cursor_x -= 1
            elif self.cursor_y > 0:
                # Merge with previous line
                self.cursor_x = len(self.content[self.cursor_y - 1])
                self.content[self.cursor_y - 1] += self.content[self.cursor_y]
                self.content.pop(self.cursor_y)
                self.cursor_y -= 1
        elif key == curses.KEY_ENTER or key == 10:
            # Split line at cursor
            line = self.content[self.cursor_y]
            self.content[self.cursor_y] = line[:self.cursor_x]
            self.content.insert(self.cursor_y + 1, line[self.cursor_x:])
            self.cursor_y += 1
            self.cursor_x = 0
        elif key == curses.KEY_LEFT:
            if self.cursor_x > 0:
                self.cursor_x -= 1
        elif key == curses.KEY_RIGHT:
            if self.cursor_y < len(self.content) and self.cursor_x < len(self.content[self.cursor_y]):
                self.cursor_x += 1
        elif key == curses.KEY_UP:
            if self.cursor_y > 0:
                self.cursor_y -= 1
                self.cursor_x = min(self.cursor_x, len(self.content[self.cursor_y]))
        elif key == curses.KEY_DOWN:
            if self.cursor_y < len(self.content) - 1:
                self.cursor_y += 1
                self.cursor_x = min(self.cursor_x, len(self.content[self.cursor_y]))
        elif 32 <= key <= 126:  # Printable characters
            if not self.content:
                self.content = ['']
            line = self.content[self.cursor_y]
            self.content[self.cursor_y] = line[:self.cursor_x] + chr(key) + line[self.cursor_x:]
            self.cursor_x += 1

    def run(self):
        """Main editor loop"""
        curses.curs_set(0)  # Hide cursor
        self.stdscr.keypad(True)

        focus = 'sidebar'  # sidebar or editor

        while True:
            self.draw()

            # Adjust scroll offset
            height, _ = self.stdscr.getmaxyx()
            visible_lines = height - 4
            if self.cursor_y < self.scroll_offset:
                self.scroll_offset = self.cursor_y
            elif self.cursor_y >= self.scroll_offset + visible_lines:
                self.scroll_offset = self.cursor_y - visible_lines + 1

            key = self.stdscr.getch()

            # Global commands
            if key == ord('q') or key == ord('Q'):  # Ctrl+Q handled below
                if key == 17:  # Ctrl+Q
                    break
            elif key == 17:  # Ctrl+Q
                break
            elif key == 19:  # Ctrl+S
                if self.current_file:
                    self.save_file()
            elif key == 15:  # Ctrl+O
                focus = 'sidebar'
                self.status_message = "Select file with Enter"
            elif key == 9:  # TAB
                focus = 'editor' if focus == 'sidebar' else 'sidebar'
                self.status_message = f"Focus: {focus}"
            elif key == ord('h') and self.mode == 'normal':
                self.status_message = "i:Insert ^S:Save ^Q:Quit ^O:Open TAB:Switch"

            # Mode-specific commands
            if self.mode == 'insert':
                self.handle_insert_mode(key)
            else:  # normal mode
                if key == ord('i'):
                    self.mode = 'insert'
                    self.status_message = "Insert mode"
                    if not self.content:
                        self.content = ['']
                elif focus == 'sidebar':
                    if key == curses.KEY_UP:
                        self.selected_file_idx = max(0, self.selected_file_idx - 1)
                    elif key == curses.KEY_DOWN:
                        self.selected_file_idx = min(len(self.files) - 1, self.selected_file_idx + 1)
                    elif key == curses.KEY_ENTER or key == 10:
                        if self.files and self.selected_file_idx < len(self.files):
                            self.load_file(self.files[self.selected_file_idx])
                            focus = 'editor'
                elif focus == 'editor':
                    if key == curses.KEY_UP:
                        self.cursor_y = max(0, self.cursor_y - 1)
                    elif key == curses.KEY_DOWN:
                        self.cursor_y = min(len(self.content) - 1, self.cursor_y + 1)
                    elif key == curses.KEY_LEFT:
                        self.cursor_x = max(0, self.cursor_x - 1)
                    elif key == curses.KEY_RIGHT:
                        if self.cursor_y < len(self.content):
                            self.cursor_x = min(len(self.content[self.cursor_y]), self.cursor_x + 1)

def main(stdscr):
    editor = SidebarEditor(stdscr)
    editor.run()

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\nEditor closed")
        sys.exit(0)
