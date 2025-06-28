[![progress-banner](https://backend.codecrafters.io/progress/shell/cc5284b5-9b5b-4647-b5aa-7672e5b407be)](https://app.codecrafters.io/users/codecrafters-bot?r=2qF)

# Python Custom Shell

This project is a custom POSIX-compliant shell built in Python. It's a lightweight, educational implementation that explores the core concepts behind how a command-line interface works.

This shell was developed as a personal project to understand the mechanics of shell design, including command parsing, process management, and system interactions. It demonstrates key OS concepts like file I/O redirection, pipelines, and environment variable handling in a simplified, pure-Python environment.

## Features
*   **REPL (Read-Eval-Print Loop)**: An interactive shell environment.
*   **Built-in Commands**: Supports `cd`, `pwd`, `echo`, `exit`, and `type`.
*   **Command History**: Bash-like history with `history` command, file support (`HISTFILE`), and session management.
*   **External Commands**: Executes external programs found in the system's `PATH`.
*   **Pipelines (`|`)**: Chain commands together, piping the output of one to the input of another.
*   **I/O Redirection**: Redirect `stdin`, `stdout`, and `stderr` using `<`, `>`, `>>`, `2>`, etc.
*   **Tab Completion**: Basic completion for commands and file paths.

## Getting Started

To run the shell, simply execute the main script:

```bash
python3 app/main.py
```

You can then start typing commands as you would in a regular shell.

## Progress Log
- **2025-06-07:** Set up REPL loop using `while` instead of recursion.

## Notes
- for repl: while instead of main inside main as recursion may cause buffer overflow if it runs too long.
