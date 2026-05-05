#!/usr/bin/env python3
"""Wrapper for novel-memory-pro character consistency checker.
Auto-discovers character profiles and runs OOC detection."""
import glob
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(SCRIPT_DIR, "..", "novel-memory-pro", "scripts", "character_consistency_checker.py")
TARGET = os.path.normpath(TARGET)


def find_characters_file(novel_dir: str) -> str:
    """Auto-discover characters JSON in memory directory."""
    memory_dir = os.path.join(novel_dir, "记忆")
    if not os.path.isdir(memory_dir):
        return ""
    for pattern in ["characters.json", "character_*.json", "人物*.json"]:
        matches = glob.glob(os.path.join(memory_dir, pattern))
        if matches:
            return matches[0]
    return ""


if __name__ == "__main__":
    args = sys.argv[1:]

    # Auto-inject --characters if not provided and --input is present
    has_characters = any(a.startswith("--characters") for a in args)
    if not has_characters:
        for i, arg in enumerate(args):
            if arg == "--input" and i + 1 < len(args):
                chapter_file = args[i + 1]
                novel_dir = os.path.dirname(os.path.dirname(chapter_file))
                chars_file = find_characters_file(novel_dir)
                if chars_file:
                    args.extend(["--characters", chars_file])
                break

    result = subprocess.run([sys.executable, TARGET] + args)
    sys.exit(result.returncode)
