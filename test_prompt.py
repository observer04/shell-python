#!/usr/bin/env python3
import readline

def test_prompt():
    print("Testing prompt display...")
    try:
        line = input("$ ")
        print(f"You entered: {line}")
    except EOFError:
        print("EOF received")
    except KeyboardInterrupt:
        print("\nKeyboard interrupt")

if __name__ == "__main__":
    test_prompt()
