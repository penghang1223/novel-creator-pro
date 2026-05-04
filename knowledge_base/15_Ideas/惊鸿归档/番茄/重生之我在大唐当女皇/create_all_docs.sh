#!/bin/bash
# Create 12 Feishu docs and write content
set -e

BASE_DIR="/Users/narain/.openclaw/workspace-jinghong/重生之我在大唐当女皇"

# Get token
TENANT_TOKEN=$(curl -s -X POST "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal" \
  -H "Content-Type: application/json" \
  -d '{"app_id":"cli_a93c22c0f538dbc6","app_secret":"n7drLxI0Tj8ZPV3XVNGvZbspOJdjywzi"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['tenant_access_token'])")

echo "Token OK"

# Clean up test doc
curl -s -X DELETE "https://open.feishu.cn/open-apis/drive/v1/files/COMpdHtF6ozfbwx298bceM92n6g?type=docx" \
  -H "Authorization: Bearer $TENANT_TOKEN" > /dev/null 2>&1

# Function: create doc, convert md to blocks, insert
create_and_fill() {
    local TITLE="$1"
    local FILE="$2"
    local FP="${BASE_DIR}/${FILE}"
    
    echo ""
    echo "📄 ${TITLE}"
    
    # Create document
    DOC_JSON=$(curl -s -X POST "https://open.feishu.cn/open-apis/docx/v1/documents" \
      -H "Authorization: Bearer ${TENANT_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "{\"title\":\"${TITLE}\"}")
    
    DOC_ID=$(echo "$DOC_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['document']['document_id'])")
    echo "  doc_id: ${DOC_ID}"
    sleep 0.3
    
    # Convert markdown to blocks JSON using Python
    BLOCKS=$(python3 -c "
import json, re, os, sys

def safe(t):
    return t.replace('\\\\','\\\\\\\\')[:1500]

with open('${FP}', 'r', encoding='utf-8') as f:
    content = f.read()

# Strip H1
lines = content.split('\n')
if lines and lines[0].startswith('# '):
    content = '\n'.join(lines[1:])

blocks = []
i = 0
lines = content.split('\n')
while i < len(lines):
    s = lines[i].strip()
    if not s:
        i += 1; continue
    if s in ('---', '***', '___'):
        blocks.append({'block_type': 22})
        i += 1; continue
    m = re.match(r'^(#{2,3})\s+(.*)', s)
    if m:
        lv = len(m.group(1))
        txt = safe(m.group(2).strip())
        bt = 4 if lv == 2 else 5
        key = 'heading2' if bt == 4 else 'heading3'
        blocks.append({'block_type': bt, key: {'elements': [{'text_run': {'content': txt}}]}})
        i += 1; continue
    if s.startswith('|'):
        cells = [c.strip() for c in s.split('|') if c.strip()]
        if all(re.match(r'^[-:]+\$', c) for c in cells):
            i += 1; continue
        blocks.append({'block_type': 2, 'text': {'elements': [{'text_run': {'content': safe(' | '.join(cells))}}]}})
        i += 1; continue
    para = []
    while i < len(lines):
        l = lines[i].strip()
        if not l or l.startswith('#') or l == '---' or l.startswith('|'):
            break
        para.append(l); i += 1
    if para:
        blocks.append({'block_type': 2, 'text': {'elements': [{'text_run': {'content': safe(chr(10).join(para))}}]}})

print(json.dumps(blocks, ensure_ascii=False))
")
    
    BLOCK_COUNT=$(echo "$BLOCKS" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
    echo "  blocks: ${BLOCK_COUNT}"
    
    # Insert blocks in batches of 30
    IDX=0
    TOTAL=0
    while [ $IDX -lt $BLOCK_COUNT ]; do
        BATCH=$(echo "$BLOCKS" | python3 -c "
import json, sys
blocks = json.load(sys.stdin)
start = ${IDX}
end = min(start + 30, len(blocks))
print(json.dumps(blocks[start:end], ensure_ascii=False))
")
        
        RESULT=$(curl -s -X POST "https://open.feishu.cn/open-apis/docx/v1/documents/${DOC_ID}/blocks/${DOC_ID}/children" \
          -H "Authorization: Bearer ${TENANT_TOKEN}" \
          -H "Content-Type: application/json" \
          -d "{\"children\": ${BATCH}, \"index\": ${IDX}}")
        
        CODE=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('code','?'))")
        if [ "$CODE" = "0" ]; then
            BATCH_SIZE=$(echo "$BATCH" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
            IDX=$((IDX + BATCH_SIZE))
            TOTAL=$((TOTAL + BATCH_SIZE))
        else
            echo "  ⚠️ batch error at index ${IDX}, code=${CODE}"
            IDX=$((IDX + 30))
        fi
        sleep 0.3
    done
    
    echo "  ✅ ${TOTAL} blocks written"
    echo "  🔗 https://feishu.cn/docx/${DOC_ID}"
    echo "${DOC_ID}" >> /tmp/feishu_docs_created.txt
    
    sleep 0.5
}

# Clear output file
> /tmp/feishu_docs_created.txt

# Create all 12 documents
create_and_fill "00-设定总纲" "00-设定总纲.md"
create_and_fill "00-伏笔台账" "00-伏笔台账.md"
create_and_fill "第一章：重生，长安初雪" "第一章-重生_长安初雪.md"
create_and_fill "第二章：这个公主不受宠" "第二章-这个公主不受宠.md"
create_and_fill "第三章：暗流" "第三章-暗流.md"
create_and_fill "第四章：冬宴" "第四章-冬宴.md"
create_and_fill "第五章：暗棋" "第五章-暗棋.md"
create_and_fill "第六章：借刀" "第六章-借刀.md"
create_and_fill "第七章：太子之怒" "第七章-太子之怒.md"
create_and_fill "第八章：崔善的目光" "第八章-崔善的目光.md"
create_and_fill "第九章：雪夜密谈" "第九章-雪夜密谈.md"
create_and_fill "第十章：第一步棋" "第十章-第一步棋.md"

echo ""
echo "🎉 全部完成！"
