#!/usr/bin/env python3
"""
A simple greeting program
"""

def greet(name, greeting="Hello"):
    """Generate a personalized greeting"""
    return f"{greeting}, {name}! Welcome to the code playground."

def main():
    # Try changing these values!
    name = "World"
    greeting = "Hello"

    message = greet(name, greeting)
    print(message)
    print(f"\nThe message has {len(message)} characters.")

    # Add your own code below:
    print("\n🎯 Edit this file and run it again to see your changes!")

if __name__ == "__main__":
    main()
