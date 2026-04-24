#!/bin/bash
# 小说项目目录结构自检脚本
# 每次新建小说或重写小说前执行
# 用法: bash 小说项目自检.sh <小说目录路径>

NOVEL_DIR="$1"

if [ -z "$NOVEL_DIR" ]; then
  echo "用法: bash 小说项目自检.sh <小说目录路径>"
  exit 1
fi

if [ ! -d "$NOVEL_DIR" ]; then
  echo "目录不存在: $NOVEL_DIR"
  echo "正在创建..."
  mkdir -p "$NOVEL_DIR"
fi

MISSING_DIRS=()
MISSING_FILES=()

# 检查必需目录
for dir in 创意 设定 结构 细纲 正文 摘要 记忆 素材; do
  if [ ! -d "$NOVEL_DIR/$dir" ]; then
    MISSING_DIRS+=("$dir")
  fi
done

# 检查必需文件
for file in novel_state.json; do
  if [ ! -f "$NOVEL_DIR/$file" ]; then
    MISSING_FILES+=("$file")
  fi
done

# 检查素材目录中的必需文件
for file in 素材/小说信息.md; do
  if [ ! -f "$NOVEL_DIR/$file" ]; then
    MISSING_FILES+=("$file")
  fi
done

# 检查记忆系统是否初始化
MEMORY_FILES=("characters.json" "plot_logic.json" "context_relations.json" "creation_history.json" "style_dna.json")
for file in "${MEMORY_FILES[@]}"; do
  if [ -f "$NOVEL_DIR/记忆/$file" ]; then
    SIZE=$(wc -c < "$NOVEL_DIR/记忆/$file")
    if [ "$SIZE" -lt 100 ]; then
      MISSING_FILES+=("记忆/$file (文件过小，可能未初始化)")
    fi
  else
    MISSING_FILES+=("记忆/$file")
  fi
done

# 检查结果
if [ ${#MISSING_DIRS[@]} -eq 0 ] && [ ${#MISSING_FILES[@]} -eq 0 ]; then
  echo "目录结构完整，无需补充。"
  exit 0
fi

# 输出缺失项
echo "====================================="
echo "小说项目自检报告"
echo "目录: $NOVEL_DIR"
echo "====================================="

if [ ${#MISSING_DIRS[@]} -gt 0 ]; then
  echo ""
  echo "缺失目录: ${MISSING_DIRS[*]}"
  echo "正在创建..."
  for dir in "${MISSING_DIRS[@]}"; do
    mkdir -p "$NOVEL_DIR/$dir"
    echo "  ✅ 已创建 $dir/"
  done
fi

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
  echo ""
  echo "缺失/异常文件:"
  for file in "${MISSING_FILES[@]}"; do
    echo "  ❌ $file"
  done
  echo ""
  echo "⚠️  以上文件需要AI手动创建，请提醒执行补齐操作"
fi
