#!/usr/bin/env python3
"""
Simple terminal-based text editor
"""

import os
import sys

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def read_file(filename):
    """Read file contents"""
    try:
        with open(filename, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return ""
    except Exception as e:
        return f"Error reading file: {e}"

def write_file(filename, content):
    """Write content to file"""
    try:
        with open(filename, 'w') as f:
            f.write(content)
        return True, f"Saved: {filename}"
    except Exception as e:
        return False, f"Error: {e}"

def list_files():
    """List files in current directory"""
    try:
        files = [f for f in os.listdir('.') if os.path.isfile(f)]
        files.sort()
        return files
    except Exception as e:
        return []

def show_menu():
    """Display main menu"""
    clear_screen()
    print("=" * 60)
    print("  SIMPLE TEXT EDITOR")
    print("=" * 60)
    print("\n1. Create new file")
    print("2. Edit existing file")
    print("3. List files")
    print("4. Exit")
    print("\n" + "=" * 60)

def edit_file(filename):
    """Edit a file using multi-line input"""
    clear_screen()
    print("=" * 60)
    print(f"  EDITING: {filename}")
    print("=" * 60)

    content = read_file(filename)

    if content and not content.startswith("Error"):
        print(f"\nCurrent content:\n")
        print("-" * 60)
        print(content)
        print("-" * 60)
        print("\nOptions:")
        print("1. Append to file")
        print("2. Replace entire file")
        print("3. Cancel")

        choice = input("\nChoice (1-3): ").strip()

        if choice == '1':
            print("\n--- APPEND MODE ---")
            print("Enter new content (type 'END' on a new line when done):")
            new_lines = []
            while True:
                line = input()
                if line == 'END':
                    break
                new_lines.append(line)
            content = content + '\n' + '\n'.join(new_lines)
        elif choice == '2':
            print("\n--- REPLACE MODE ---")
            print("Enter new content (type 'END' on a new line when done):")
            new_lines = []
            while True:
                line = input()
                if line == 'END':
                    break
                new_lines.append(line)
            content = '\n'.join(new_lines)
        else:
            print("\nCancelled.")
            input("Press Enter to continue...")
            return
    else:
        print("\nNew file - enter content (type 'END' on a new line when done):")
        lines = []
        while True:
            line = input()
            if line == 'END':
                break
            lines.append(line)
        content = '\n'.join(lines)

    # Save the file
    success, message = write_file(filename, content)
    print(f"\n{message}")
    input("Press Enter to continue...")

def main():
    """Main program loop"""
    while True:
        show_menu()
        choice = input("\nChoice (1-4): ").strip()

        if choice == '1':
            clear_screen()
            filename = input("Enter filename: ").strip()
            if filename:
                edit_file(filename)

        elif choice == '2':
            clear_screen()
            print("Files in current directory:")
            print("-" * 60)
            files = list_files()
            if files:
                for i, f in enumerate(files, 1):
                    print(f"{i}. {f}")
                print(f"{len(files) + 1}. Enter custom filename")
            else:
                print("No files found")
                print("1. Enter custom filename")

            print("-" * 60)

            if files:
                choice_input = input(f"\nChoice (1-{len(files) + 1}): ").strip()
                try:
                    idx = int(choice_input)
                    if 1 <= idx <= len(files):
                        filename = files[idx - 1]
                        edit_file(filename)
                    elif idx == len(files) + 1:
                        filename = input("Enter filename: ").strip()
                        if filename:
                            edit_file(filename)
                except ValueError:
                    print("Invalid choice")
                    input("Press Enter to continue...")
            else:
                filename = input("Enter filename: ").strip()
                if filename:
                    edit_file(filename)

        elif choice == '3':
            clear_screen()
            print("=" * 60)
            print("  FILES IN CURRENT DIRECTORY")
            print("=" * 60)
            files = list_files()
            if files:
                for f in files:
                    size = os.path.getsize(f)
                    print(f"  {f:<40} {size:>10} bytes")
            else:
                print("  No files found")
            print("=" * 60)
            input("\nPress Enter to continue...")

        elif choice == '4':
            clear_screen()
            print("\nGoodbye!\n")
            sys.exit(0)

        else:
            print("\nInvalid choice")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()
