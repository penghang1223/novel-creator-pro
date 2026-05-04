#!/bin/bash
# 御医狂妃 写后自检脚本 v2
# 用法: bash check.sh [章节文件路径]

FILE="$1"
if [ -z "$FILE" ]; then
    echo "❌ 用法: bash check.sh [章节文件路径]"
    exit 1
fi

if [ ! -f "$FILE" ]; then
    echo "❌ 文件不存在: $FILE"
    exit 1
fi

PASS=0
FAIL=0

echo "═══════════════════════════════════════"
echo "  御医狂妃 自检报告: $(basename $FILE)"
echo "═══════════════════════════════════════"

# 1. 字数
WORD_COUNT=$(wc -c < "$FILE" | tr -d '[:space:]')
echo "📏 字数: $WORD_COUNT"
if [ "$WORD_COUNT" -lt 2800 ]; then
    echo "  ❌ 低于2800字"; FAIL=$((FAIL+1))
else
    echo "  ✅ 达标"; PASS=$((PASS+1))
fi

# 2. 名称残留
LATEWAN=$(grep -c "林晚晚" "$FILE" 2>/dev/null)
LATEWAN=${LATEWAN:-0}
echo "🔍 林晚晚残留: $LATEWAN"
if [ "$LATEWAN" -gt 0 ]; then
    echo "  ❌ 发现残留"; FAIL=$((FAIL+1))
else
    echo "  ✅ 零残留"; PASS=$((PASS+1))
fi

# 3. 套路句式
for phrase in "看了很久" "然后笑了" "声音很低" "微微一笑"; do
    COUNT=$(grep -c "$phrase" "$FILE" 2>/dev/null)
    COUNT=${COUNT:-0}
    if [ "$COUNT" -gt 2 ]; then
        echo "  ❌ '$phrase': ${COUNT}次"; FAIL=$((FAIL+1))
    else
        echo "  ✅ '$phrase': ${COUNT}次"; PASS=$((PASS+1))
    fi
done

# 4. "XX地说"检查
SPEAK_TAGS=$(grep -cE "地说|地喊|地叫|地问" "$FILE" 2>/dev/null)
SPEAK_TAGS=${SPEAK_TAGS:-0}
echo "🚫 'XX地说'类标签: $SPEAK_TAGS"
if [ "$SPEAK_TAGS" -gt 3 ]; then
    echo "  ❌ 超过3次，应改用动作/环境"; FAIL=$((FAIL+1))
else
    echo "  ✅ 可接受"; PASS=$((PASS+1))
fi

# 5. 过滤词检测（Deep POV）— 只检测叙述中的过滤词，跳过对话
FILTER_WORDS="觉得|感到|感觉到|意识到|注意到|发现他|发现她|感觉到|他看到|她看到|他听到|她听到|他想到|她想到|他知道|她知道|他决定|她决定"
FILTER_COUNT=$(grep -v '"' "$FILE" | grep -cE "$FILTER_WORDS" 2>/dev/null)
FILTER_COUNT=${FILTER_COUNT:-0}
echo "🔍 叙述中过滤词: $FILTER_COUNT处"
if [ "$FILTER_COUNT" -gt 5 ]; then
    echo "  ❌ 超过5处，应改用Deep POV（删除过滤词，直接写想法/感受）"
    echo "  示例: '她觉得冷' → '冷。她抱紧双臂。'"
    grep -nE "$FILTER_WORDS" "$FILE" 2>/dev/null | head -10 | while read line; do
        echo "    → $line"
    done
    FAIL=$((FAIL+1))
else
    echo "  ✅ 可接受（≤5处）"
    PASS=$((PASS+1))
fi

# 6. 章末钩子
LAST_LINE=$(tail -5 "$FILE" | tr '\n' ' ')
if echo "$LAST_LINE" | grep -qiE "睡了|天黑|安静了|结束了|没事了"; then
    echo "🪝 ⚠️ 结尾可能太平"; FAIL=$((FAIL+1))
else
    echo "🪝 ✅ 结尾有张力"; PASS=$((PASS+1))
fi

echo "═══════════════════════════════════════"
echo "  通过:$PASS | 失败:$FAIL"
if [ "$FAIL" -gt 0 ]; then echo "  ❌ 未通过"; exit 1; else echo "  ✅ 全部通过"; exit 0; fi
