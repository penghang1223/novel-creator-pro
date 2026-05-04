#!/usr/bin/env python3
"""Create Feishu docs and write content - clean version."""

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

def api_call(url, data=None, method="GET"):
    """Make Feishu API call."""
    payload = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": f"Bearer {TENANT_TOKEN}",
        "Content-Type": "application/json"
    }, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())

def create_doc(title):
    """Create a new document, return doc_id."""
    result = api_call(
        "https://open.feishu.cn/open-apis/docx/v1/documents",
        {"title": title},
        "POST"
    )
    return result['data']['document']['document_id']

def safe_text(t):
    """Clean text for API."""
    t = t.replace('\\', '\\\\')
    return t[:1800] if len(t) > 1800 else t

def md_to_blocks(md):
    """Convert markdown to blocks."""
    blocks = []
    lines = md.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        s = line.strip()
        if not s:
            i += 1; continue
        if s in ('---', '***', '___'):
            blocks.append({"block_type": 22})
            i += 1; continue
        m = re.match(r'^(#{1,3})\s+(.*)', s)
        if m:
            lv = len(m.group(1))
            txt = safe_text(m.group(2).strip())
            if lv == 1:
                i += 1; continue
            bt = {2: 4, 3: 5}.get(lv, 4)
            key = {4: "heading2", 5: "heading3"}.get(bt, "heading2")
            blocks.append({"block_type": bt, key: {"elements": [{"text_run": {"content": txt}}]}})
            i += 1; continue
        if s.startswith('|'):
            cells = [c.strip() for c in s.split('|') if c.strip()]
            if all(re.match(r'^[-:]+$', c) for c in cells):
                i += 1; continue
            blocks.append({"block_type": 2, "text": {"elements": [{"text_run": {"content": safe_text(' | '.join(cells))}}]}})
            i += 1; continue
        para = []
        while i < len(lines):
            l = lines[i].rstrip().strip()
            if not l or l.startswith('#') or l in ('---',) or l.startswith('|'):
                break
            para.append(l)
            i += 1
        if para:
            blocks.append({"block_type": 2, "text": {"elements": [{"text_run": {"content": safe_text('\n'.join(para))}}]}})
    return blocks

def insert_all(doc_id, blocks):
    """Insert all blocks in batches, appending sequentially."""
    bs = 40  # batch size
    idx = 1  # start after document root
    for start in range(0, len(blocks), bs):
        batch = blocks[start:start+bs]
        try:
            result = api_call(
                f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children",
                {"children": batch, "index": idx},
                "POST"
            )
            idx += len(batch)
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', errors='replace')
            print(f"    ERR@{start}: {e.code} {body[:150]}")
            # Fallback: insert one by one
            for b in batch:
                try:
                    api_call(
                        f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children",
                        {"children": [b], "index": idx},
                        "POST"
                    )
                    idx += 1
                except:
                    pass
                time.sleep(0.15)
        time.sleep(0.3)
    return idx - 1

def main():
    results = []
    for title, filename in FILES:
        filepath = os.path.join(BASE_DIR, filename)
        print(f"\n📄 {title}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            print("  SKIP: not found"); continue
        
        # Strip first H1
        ls = content.split('\n')
        if ls and ls[0].startswith('# '):
            content = '\n'.join(ls[1:])
        
        # Create doc
        doc_id = create_doc(title)
        print(f"  Created: {doc_id}")
        time.sleep(0.5)
        
        # Generate blocks
        blocks = md_to_blocks(content)
        print(f"  Blocks: {len(blocks)}")
        
        # Insert content
        n = insert_all(doc_id, blocks)
        print(f"  Inserted: {n} blocks")
        
        results.append((title, doc_id))
        time.sleep(0.5)
    
    print("\n\n✅ 全部完成！飞书文档链接：\n")
    for title, doc_id in results:
        print(f"  {title}")
        print(f"  https://feishu.cn/docx/{doc_id}\n")

if __name__ == "__main__":
    main()
