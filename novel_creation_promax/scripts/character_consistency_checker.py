#!/usr/bin/env python3
"""Wrapper for novel-memory-pro character consistency checker.
Auto-discovers character profiles and runs OOC detection."""
import glob
import json
import os
import subprocess
import sys
import tempfile

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


def materialize_profile(path: str) -> tuple[str, str]:
    """Return a target-compatible character profile path and optional temp path."""
    if not path:
        return "", ""
    try:
        with open(path, "r", encoding="utf-8-sig") as handle:
            payload = json.load(handle)
    except Exception:
        return path, ""

    if isinstance(payload, dict) and "basic_info" in payload:
        return path, ""

    if isinstance(payload, dict) and isinstance(payload.get("memories"), list):
        for item in payload["memories"]:
            data = item.get("data") if isinstance(item, dict) else None
            if isinstance(data, dict) and data.get("basic_info"):
                fd, tmp_path = tempfile.mkstemp(prefix="character_profile_", suffix=".json")
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    json.dump(data, handle, ensure_ascii=False, indent=2)
                return tmp_path, tmp_path

    return path, ""


def normalize_args(args: list[str]) -> tuple[list[str], str]:
    temp_path = ""
    normalized: list[str] = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {"--characters", "--character-profile"} and i + 1 < len(args):
            profile_path, tmp = materialize_profile(args[i + 1])
            temp_path = tmp or temp_path
            normalized.extend(["--character-profile", profile_path])
            i += 2
            continue
        normalized.append(arg)
        i += 1
    return normalized, temp_path


if __name__ == "__main__":
    args = sys.argv[1:]

    # Auto-inject --character-profile if not provided and --input is present.
    has_profile = any(a in {"--characters", "--character-profile"} for a in args)
    if not has_profile:
        for i, arg in enumerate(args):
            if arg == "--input" and i + 1 < len(args):
                chapter_file = args[i + 1]
                novel_dir = os.path.dirname(os.path.dirname(chapter_file))
                chars_file = find_characters_file(novel_dir)
                if chars_file:
                    args.extend(["--character-profile", chars_file])
                break

    normalized_args, temp_path = normalize_args(args)
    try:
        result = subprocess.run([sys.executable, TARGET] + normalized_args)
        sys.exit(result.returncode)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
