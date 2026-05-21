"""Web dashboard configuration."""

from pathlib import Path

# Project root: NOVEL_CREAT/ (3 levels up from this file)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Output directory
OUTPUT_DIR = PROJECT_ROOT / "novel_output"

# Scripts
SCRIPTS_DIR = PROJECT_ROOT / "novel_creation_promax" / "scripts"
MEMORY_SCRIPT = PROJECT_ROOT / "novel_creation_promax" / "novel-memory-pro" / "scripts" / "memory_manager.py"

# Supported platforms
PLATFORMS = ["番茄", "起点", "知乎", "七猫", "飞卢", "晋江"]

# Pipeline stages in order
STAGES = ["创意", "设定", "大纲", "细纲", "正文", "记忆更新", "完结复盘"]

# CORS
CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000"]
