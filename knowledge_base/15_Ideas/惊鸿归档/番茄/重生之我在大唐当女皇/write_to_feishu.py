#!/usr/bin/env python3
"""Convert markdown files to Feishu docx blocks and insert them."""

import json
import re
import sys
import time
import urllib.request

TENANT_TOKEN = sys.argv[1]

DOCS = {
    "00-设定总纲": "EMVUdL4wPoZgsTxndNgctR5RnHg",
    "00-伏笔台账": "R97adwmFrop5lJx38QTcpFionUh",
    "第一章：重生，长安初雪": "IxiudtA9TordOVxEwZ6cnA5Pngh",
    "第二章：这个公主不受宠": "WtRudrkbZo8tl5xfv4Ich4finVg",
    "第三章：暗流": "OyxWd25INoXoSSxFizpcV0gXnBc",
    "第四章：冬宴": "DdIQdyEZMomgvjxmKWdcIiVdnFc",
    "第五章：暗棋": "Awiwd6HjKo6GEyxhmmQckl1onkf",
    "第六章：借刀": "KZdidjlneoaMyIx32U6c9u67nyd",
    "第七章：太子之怒": "Kh5IdGEDdow2w6xLQkicVhmknTg",
    "第八章：崔善的目光": "Tw2odCbhwoddutxs02Nct7v2nNf",
    "第九章：雪夜密谈": "ITQWdlgiko8ebYx1EFQc3yA3ntP",
    "第十章：第一步棋": "WhLNdaRwpoTGCPxArdncZ4ypnPd",
}

FILE_MAP = {
    "00-设定总纲": "00-设定总纲.md",
    "00-伏笔台账": "00-伏笔台账.md",
    "第一章：重生，长安初雪": "第一章-重生_长安初雪.md",
    "第二章：这个公主不受宠": "第二章-这个公主不受宠.md",
    "第三章：暗流": "第三章-暗流.md",
    "第四章：冬宴": "第四章-冬宴.md",
    "第五章：暗棋": "第五章-暗棋.md",
    "第六章：借刀": "第六章-借刀.md",
    "第七章：太子之怒": "第七章-太子之怒.md",
    "第八章：崔善的目光": "第八章-崔善的目光.md",
    "第九章：雪夜密谈": "第九章-雪夜密谈.md",
    "第十章：第一步棋": "第十章-第一步棋.md",
}

BASE_DIR = "/Users/narain/.openclaw/workspace-jinghong/重生之我在大唐当女皇/"

def make_text_elements(text):
    """Create text elements array for a paragraph block."""
    return [{"text_run": {"content": text}}]

def make_heading_block(text, level=2):
    """Create a heading block."""
    block_type = {1: 3, 2: 4, 3: 5}.get(level, 4)
    key = {3: "heading1", 4: "heading2", 5: "heading3"}[block_type]
    return {
        "block_type": block_type,
        key: {"elements": make_text_elements(text)}
    }

def make_text_block(text):
    """Create a text (paragraph) block."""
    return {
        "block_type": 2,
        "text": {"elements": make_text_elements(text)}
    }

def make_divider_block():
    return {"block_type": 22}

def md_to_blocks(md_content):
    """Convert markdown content to Feishu blocks."""
    blocks = []
    lines = md_content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            i += 1
            continue
        
        # Horizontal rule
        if stripped in ('---', '***', '___'):
            blocks.append(make_divider_block())
            i += 1
            continue
        
        # Headings
        if stripped.startswith('#'):
            m = re.match(r'^(#{1,3})\s+(.*)', stripped)
            if m:
                level = len(m.group(1))
                text = m.group(2).strip()
                # Skip the title (H1 matching document title)
                if level == 1:
                    i += 1
                    continue
                blocks.append(make_heading_block(text, level))
                i += 1
                continue
        
        # Regular paragraph - collect consecutive non-empty, non-special lines
        para_lines = []
        while i < len(lines):
            l = lines[i].strip()
            if not l:
                break
            if l.startswith('#') or l in ('---', '***', '___'):
                break
            # Skip markdown table syntax
            if l.startswith('|') and '|' in l[1:]:
                para_lines.append(l)
                i += 1
                continue
            para_lines.append(l)
            i += 1
        
        if para_lines:
            text = '\n'.join(para_lines)
            # Clean up markdown bold/italic markers for Feishu
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove bold markers
            text = re.sub(r'\*(.*?)\*', r'\1', text)  # Remove italic markers
            blocks.append(make_text_block(text))
    
    return blocks

def batch_create_blocks(doc_id, blocks, parent_block_id=None):
    """Insert blocks into a document using batch API."""
    if not parent_block_id:
        parent_block_id = doc_id
    
    # API allows max 50 blocks per batch
    batch_size = 50
    for start in range(0, len(blocks), batch_size):
        batch = blocks[start:start + batch_size]
        
        payload = json.dumps({
            "children": batch,
            "index": 0
        }).encode('utf-8')
        
        url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{parent_block_id}/children"
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Authorization": f"Bearer {TENANT_TOKEN}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
                if result.get('code') != 0:
                    print(f"  WARNING: batch error: {result.get('msg', 'unknown')}")
        except Exception as e:
            print(f"  ERROR: {e}")
        
        time.sleep(0.5)  # Rate limiting

def main():
    for title, doc_id in DOCS.items():
        filename = FILE_MAP[title]
        filepath = BASE_DIR + filename
        
        print(f"Processing: {title} ({doc_id})")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"  SKIP: file not found: {filepath}")
            continue
        
        # Skip the first H1 title line
        lines = content.split('\n')
        if lines and lines[0].startswith('# '):
            content = '\n'.join(lines[1:])
        
        blocks = md_to_blocks(content)
        print(f"  Generated {len(blocks)} blocks")
        
        if blocks:
            batch_create_blocks(doc_id, blocks)
            print(f"  DONE")
        else:
            print(f"  SKIP: no blocks generated")
        
        time.sleep(1)  # Rate limiting between documents
    
    print("\n=== ALL DONE ===")
    print("\nDocument URLs:")
    for title, doc_id in DOCS.items():
        print(f"  {title}: https://feishu.cn/docx/{doc_id}")

if __name__ == "__main__":
    main()
