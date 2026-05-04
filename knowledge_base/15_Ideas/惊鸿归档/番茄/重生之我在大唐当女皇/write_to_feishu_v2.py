#!/usr/bin/env python3
"""Write markdown content to Feishu docx documents - fixed version."""

import json
import re
import sys
import time
import urllib.request

TENANT_TOKEN = sys.argv[1]
ACTION = sys.argv[2] if len(sys.argv) > 2 else "create"

DOCS = [
    ("00-设定总纲", "EMVUdL4wPoZgsTxndNgctR5RnHg", "00-设定总纲.md"),
    ("00-伏笔台账", "R97adwmFrop5lJx38QTcpFionUh", "00-伏笔台账.md"),
    ("第一章", "IxiudtA9TordOVxEwZ6cnA5Pngh", "第一章-重生_长安初雪.md"),
    ("第二章", "WtRudrkbZo8tl5xfv4Ich4finVg", "第二章-这个公主不受宠.md"),
    ("第三章", "OyxWd25INoXoSSxFizpcV0gXnBc", "第三章-暗流.md"),
    ("第四章", "DdIQdyEZMomgvjxmKWdcIiVdnFc", "第四章-冬宴.md"),
    ("第五章", "Awiwd6HjKo6GEyxhmmQckl1onkf", "第五章-暗棋.md"),
    ("第六章", "KZdidjlneoaMyIx32U6c9u67nyd", "第六章-借刀.md"),
    ("第七章", "Kh5IdGEDdow2w6xLQkicVhmknTg", "第七章-太子之怒.md"),
    ("第八章", "Tw2odCbhwoddutxs02Nct7v2nNf", "第八章-崔善的目光.md"),
    ("第九章", "ITQWdlgiko8ebYx1EFQc3yA3ntP", "第九章-雪夜密谈.md"),
    ("第十章", "WhLNdaRwpoTGCPxArdncZ4ypnPd", "第十章-第一步棋.md"),
]

BASE_DIR = "/Users/narain/.openclaw/workspace-jinghong/重生之我在大唐当女皇/"

def safe_text(text):
    """Clean text for Feishu API - remove problematic chars."""
    # Remove or escape special chars that might cause issues
    text = text.replace('\\', '\\\\')
    # Truncate very long lines
    if len(text) > 2000:
        text = text[:2000] + "..."
    return text

def md_to_blocks(md_content):
    """Convert markdown to Feishu blocks."""
    blocks = []
    lines = md_content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()
        
        if not stripped:
            i += 1
            continue
        
        # Divider
        if stripped in ('---', '***', '___'):
            blocks.append({"block_type": 22})
            i += 1
            continue
        
        # Heading
        m = re.match(r'^(#{1,3})\s+(.*)', stripped)
        if m:
            level = len(m.group(1))
            text = safe_text(m.group(2).strip())
            if level == 1:
                i += 1
                continue  # Skip H1 (doc title)
            type_map = {2: 4, 3: 5}
            key_map = {4: "heading2", 5: "heading3"}
            bt = type_map.get(level, 4)
            blocks.append({
                "block_type": bt,
                key_map[bt]: {"elements": [{"text_run": {"content": text}}]}
            })
            i += 1
            continue
        
        # Table row - convert to plain text
        if stripped.startswith('|'):
            cells = [c.strip() for c in stripped.split('|') if c.strip()]
            # Skip separator rows
            if all(re.match(r'^[-:]+$', c) for c in cells):
                i += 1
                continue
            text = safe_text(' | '.join(cells))
            blocks.append({
                "block_type": 2,
                "text": {"elements": [{"text_run": {"content": text}}]}
            })
            i += 1
            continue
        
        # Regular paragraph - collect lines until empty/special
        para = []
        while i < len(lines):
            l = lines[i].rstrip().strip()
            if not l:
                break
            if l.startswith('#') or l in ('---', '***', '___'):
                break
            if l.startswith('|'):
                break
            para.append(l)
            i += 1
        
        if para:
            text = safe_text('\n'.join(para))
            blocks.append({
                "block_type": 2,
                "text": {"elements": [{"text_run": {"content": text}}]}
            })
    
    return blocks

def clear_document(doc_id):
    """Delete all blocks in a document."""
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {TENANT_TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            items = data.get('data', {}).get('items', [])
            # Don't delete the document root block
            for item in items:
                bid = item.get('block_id')
                if bid and bid != doc_id:
                    del_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{bid}"
                    del_req = urllib.request.Request(del_url, headers={
                        "Authorization": f"Bearer {TENANT_TOKEN}",
                        "Content-Type": "application/json"
                    }, method="DELETE")
                    try:
                        urllib.request.urlopen(del_req, timeout=10)
                    except:
                        pass
                    time.sleep(0.1)
    except Exception as e:
        print(f"  Clear warning: {e}")

def insert_blocks(doc_id, blocks):
    """Insert blocks into document, appending at end."""
    batch_size = 30
    total_inserted = 0
    
    for start in range(0, len(blocks), batch_size):
        batch = blocks[start:start + batch_size]
        
        # Get current block count to determine index
        idx_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks?page_size=500"
        idx_req = urllib.request.Request(idx_url, headers={"Authorization": f"Bearer {TENANT_TOKEN}"})
        try:
            with urllib.request.urlopen(idx_req, timeout=15) as resp:
                data = json.loads(resp.read())
                current_count = len(data.get('data', {}).get('items', []))
        except:
            current_count = total_inserted
        
        payload = json.dumps({
            "children": batch,
            "index": current_count
        }).encode('utf-8')
        
        url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children"
        req = urllib.request.Request(url, data=payload, headers={
            "Authorization": f"Bearer {TENANT_TOKEN}",
            "Content-Type": "application/json"
        }, method="POST")
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
                if result.get('code') == 0:
                    total_inserted += len(batch)
                else:
                    print(f"  Batch error: {result.get('msg')}")
                    # Try to continue with remaining blocks
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', errors='replace')
            print(f"  HTTP {e.code}: {body[:200]}")
            # Try splitting batch further
            if len(batch) > 1:
                for single_block in batch:
                    try:
                        single_payload = json.dumps({
                            "children": [single_block],
                            "index": current_count
                        }).encode('utf-8')
                        single_req = urllib.request.Request(url, data=single_payload, headers={
                            "Authorization": f"Bearer {TENANT_TOKEN}",
                            "Content-Type": "application/json"
                        }, method="POST")
                        with urllib.request.urlopen(single_req, timeout=15) as resp2:
                            result2 = json.loads(resp2.read())
                            if result2.get('code') == 0:
                                total_inserted += 1
                                current_count += 1
                    except Exception as e2:
                        pass  # Skip problematic blocks
                    time.sleep(0.2)
        
        time.sleep(0.5)
    
    return total_inserted

def main():
    for title, doc_id, filename in DOCS:
        filepath = BASE_DIR + filename
        print(f"\n>>> {title} ({doc_id})")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"  SKIP: not found")
            continue
        
        # Strip first H1
        lines = content.split('\n')
        if lines and lines[0].startswith('# '):
            content = '\n'.join(lines[1:])
        
        if ACTION == "clear":
            print(f"  Clearing...")
            clear_document(doc_id)
            time.sleep(1)
        
        blocks = md_to_blocks(content)
        print(f"  Blocks: {len(blocks)}")
        
        if blocks:
            n = insert_blocks(doc_id, blocks)
            print(f"  Inserted: {n}")
        
        time.sleep(1)
    
    print("\n\n=== DONE ===")
    print("\n飞书文档链接：")
    for title, doc_id, _ in DOCS:
        print(f"  {title}: https://feishu.cn/docx/{doc_id}")

if __name__ == "__main__":
    main()
