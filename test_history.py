#!/usr/bin/env python3

import sys
import os
sys.path.append('/home/observer/projects/codecrafters-shell-python/app')
from main import HistoryManager
import readline

# Test the history manager behavior
print("Testing HistoryManager...")

# Create a test history manager
history_mgr = HistoryManager("/tmp/test_history")

# Test loading (should not load in non-interactive mode)
history_mgr.load()
print(f"After load - session_start: {history_mgr.session_start}, last_append_pos: {history_mgr.last_append_pos}")
print(f"Current history length: {readline.get_current_history_length()}")

# Add some test commands
history_mgr.add("echo strawberry raspberry")
history_mgr.add("echo banana apple")
history_mgr.add("history")

print(f"After adding commands - history length: {readline.get_current_history_length()}")

# Test history display
print("\nHistory output:")
history_mgr.history_cmd()
