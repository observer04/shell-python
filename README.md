[![progress-banner](https://backend.codecrafters.io/progress/shell/cc5284b5-9b5b-4647-b5aa-7672e5b407be)](https://app.codecrafters.io/users/codecrafters-bot?r=2qF)

This is a starting point for Python solutions to the
["Build Your Own Shell" Challenge](https://app.codecrafters.io/courses/shell/overview).

In this challenge, you'll build your own POSIX compliant shell that's capable of
interpreting shell commands, running external programs and builtin commands like
cd, pwd, echo and more. Along the way, you'll learn about shell command parsing,
REPLs, builtin commands, and more.

**Note**: If you're viewing this repo on GitHub, head over to
[codecrafters.io](https://codecrafters.io) to try the challenge.

# CodeCrafters Shell Challenge

## Overview
A custom shell implementation in Python for the CodeCrafters challenge.

## Getting Started
- Clone the repository
- Run the shell:
  ```bash
  python app/main.py
  ```

## Progress Log
- **2025-06-07:** Set up REPL loop using `while` instead of recursion.

## Notes
- for repl: while instead of main inside main as recursion may cause buffer overflow if it runs too long.
