#!/usr/bin/env python3
"""Create Feishu docs and write content immediately."""

import json
import re
import sys
import time
import urllib.request
import os

TENANT_TOKEN = sys.argv[1]
BASE_DIR = "/Users/narain/.openclaw/workspace-jinghong/重生之我在大唐当女皇/"

FILES = [
    ("00-设定总纲", "00-设定总纲.md"),
    ("00-伏笔台账", "00-伏笔台账.md"),
    ("第一章：重生，长安初雪", "第一章-重生_长安初雪.md"),
    ("第二章：这个公主不受宠", "第二章-这个公主不受宠.md"),
    ("第三章：暗流", "第三章-暗流.md"),
    ("第四章：冬宴", "第四章-冬宴.md"),
    ("第五章：暗棋", "第五章-暗棋.md"),
    ("第六章：借刀", "第六章-借刀.md"),
    ("第七章：太子之怒", "第七章-太子之怒.md"),
    ("第八章：崔善的目光", "第八章-崔善的目光.md"),
    ("第九章：雪夜密谈", "第九章-雪夜密谈.md"),
    ("第十章：第一步棋", "第十章-第一步棋.md"),
]

def post(url, data):
    req = urllib.request.Request(url, json.dumps(data, ensure_ascii=False).encode('utf-8'),
        headers={"Authorization": f"Bearer {TENANT_TOKEN}", "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())

def safe(t):
    return t.replace('\\','\\\\')[:1500]

def md_to_blocks(md):
    blocks = []
    lines = md.split('\n')
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if not s: i+=1; continue
        if s in ('---','***','___'): blocks.append({"block_type":22}); i+=1; continue
        m = re.match(r'^(#{2,3})\s+(.*)', s)
        if m:
            lv = len(m.group(1))
            txt = safe(m.group(2).strip())
            bt = {2:4,3:5}[lv]
            key = "heading2" if bt==4 else "heading3"
            blocks.append({"block_type":bt, key:{"elements":[{"text_run":{"content":txt}}]}})
            i+=1; continue
        if s.startswith('|'):
            cells = [c.strip() for c in s.split('|') if c.strip()]
            if all(re.match(r'^[-:]+$', c) for c in cells): i+=1; continue
            blocks.append({"block_type":2,"text":{"elements":[{"text_run":{"content":safe(' | '.join(cells))}}]}})
            i+=1; continue
        para = []
        while i < len(lines):
            l = lines[i].strip()
            if not l or l.startswith('#') or l=='---' or l.startswith('|'): break
            para.append(l); i+=1
        if para:
            blocks.append({"block_type":2,"text":{"elements":[{"text_run":{"content":safe('\n'.join(para))}}]}})
    return blocks

def insert_blocks(doc_id, blocks):
    bs = 30
    idx = 0
    total = 0
    for s in range(0, len(blocks), bs):
        batch = blocks[s:s+bs]
        try:
            post(f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children",
                {"children": batch, "index": idx})
            idx += len(batch)
            total += len(batch)
        except Exception as e:
            print(f"    batch err: {e}")
            for b in batch:
                try:
                    post(f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children",
                        {"children": [b], "index": idx})
                    idx += 1; total += 1
                except: pass
                time.sleep(0.1)
        time.sleep(0.3)
    return total

results = []
for title, filename in FILES:
    fp = os.path.join(BASE_DIR, filename)
    print(f"\n📄 {title}")
    try:
        with open(fp, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("  SKIP"); continue
    
    # Strip H1 title
    ls = content.split('\n')
    if ls and ls[0].startswith('# '): content = '\n'.join(ls[1:])
    
    # Create doc
    r = post("https://open.feishu.cn/open-apis/docx/v1/documents", {"title": title})
    doc_id = r['data']['document']['document_id']
    print(f"  doc_id: {doc_id}")
    time.sleep(0.3)
    
    # Convert and insert
    blocks = md_to_blocks(content)
    n = insert_blocks(doc_id, blocks)
    print(f"  ✅ {n} blocks written")
    results.append((title, doc_id))
    time.sleep(0.5)

print("\n\n🔗 飞书文档链接：\n")
for title, doc_id in results:
    print(f"  📄 {title}")
    print(f"     https://feishu.cn/docx/{doc_id}\n")
