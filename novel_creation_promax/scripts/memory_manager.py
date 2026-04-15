#!/usr/bin/env python3
"""Thin wrapper that delegates to novel-memory-pro/scripts/memory_manager.py"""
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(SCRIPT_DIR, "..", "novel-memory-pro", "scripts", "memory_manager.py")
TARGET = os.path.normpath(TARGET)

if __name__ == "__main__":
    subprocess.run([sys.executable, TARGET] + sys.argv[1:])
