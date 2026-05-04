#!/bin/bash
# 惊鸿小说写作 - Claude Code调用脚本
# 使用方法：在惊鸿的session中执行此脚本

START_CHAPTER=${1:-42}
END_CHAPTER=${2:-46}
WORKSPACE="/Users/narain/.openclaw/workspace-jinghong"

echo "📖 开始生成第${START_CHAPTER}-${END_CHAPTER}章..."

# 检查state.json是否存在
if [ ! -f "$WORKSPACE/novel/state.json" ]; then
    echo "❌ novel/state.json 不存在"
    exit 1
fi

# 读取当前状态
CURRENT=$(python3 -c "import json; d=json.load(open('$WORKSPACE/novel/state.json')); print(d['meta']['current_chapter'])")
echo "📍 当前进度：第${CURRENT}章"

# 检查是否有前文
DRAFT_COUNT=$(ls "$WORKSPACE/novel/drafts/" 2>/dev/null | wc -l)
echo "📚 已有草稿：${DRAFT_COUNT}个文件"

# 调用Claude Code
# 注意：此脚本仅供参考，实际调用通过sessions_spawn完成
echo "✅ 准备就绪，请通过sessions_spawn启动Claude Code"
echo "   task: 见 novel/claude-code-task-template.md"
echo "   runtime: acp"
echo "   mode: run"
echo "   cwd: $WORKSPACE"
