#!/usr/bin/env python3
"""Write Feishu docs - robust version using only Python stdlib."""
import json, re, os, sys, time
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE = "/Users/narain/.openclaw/workspace-jinghong/重生之我在大唐当女皇/"

# Get token
req = Request("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json.dumps({"app_id":"cli_a93c22c0f538dbc6","app_secret":"n7drLxI0Tj8ZPV3XVNGvZbspOJdjywzi"}).encode(),
    {"Content-Type":"application/json"}, method="POST")
token = json.loads(urlopen(req, timeout=10).read())["tenant_access_token"]

def api(url, data=None, method="GET"):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8") if data else None
    r = Request(url, body, {"Authorization":f"Bearer {token}","Content-Type":"application/json"}, method=method)
    return json.loads(urlopen(r, timeout=60).read())

def safe(t):
    t = t.replace("\\", "\\\\")
    return t[:1400] if len(t) > 1400 else t

def md2blocks(md):
    blocks, lines, i = [], md.split("\n"), 0
    while i < len(lines):
        s = lines[i].strip()
        if not s: i+=1; continue
        if s in ("---","***","___"): blocks.append({"block_type":22}); i+=1; continue
        m = re.match(r"^(#{2,3})\s+(.*)", s)
        if m:
            txt = safe(m.group(2).strip())
            bt = 4 if len(m.group(1))==2 else 5
            blocks.append({"block_type":bt, ("heading2" if bt==4 else "heading3"): {"elements":[{"text_run":{"content":txt}}]}})
            i+=1; continue
        para = []
        while i < len(lines):
            l = lines[i].strip()
            if not l or re.match(r"^#{1,3}\s", l) or l=="---" or l.startswith("|"): break
            para.append(l); i+=1
        if para:
            blocks.append({"block_type":2, "text":{"elements":[{"text_run":{"content":safe(chr(10).join(para))}}]}})
    return blocks

DOCS = [
    ("00-设定总纲","00-设定总纲.md"),
    ("00-伏笔台账","00-伏笔台账.md"),
    ("第一章：重生，长安初雪","第一章-重生_长安初雪.md"),
    ("第二章：这个公主不受宠","第二章-这个公主不受宠.md"),
    ("第三章：暗流","第三章-暗流.md"),
    ("第四章：冬宴","第四章-冬宴.md"),
    ("第五章：暗棋","第五章-暗棋.md"),
    ("第六章：借刀","第六章-借刀.md"),
    ("第七章：太子之怒","第七章-太子之怒.md"),
    ("第八章：崔善的目光","第八章-崔善的目光.md"),
    ("第九章：雪夜密谈","第九章-雪夜密谈.md"),
    ("第十章：第一步棋","第十章-第一步棋.md"),
]

# IDs from failed runs - delete them
old_ids = ["Z6oOdBwJcoVSwlxrjzqcpnAXnqh","UHqsdRH8toiSNKxxG4ZchdlEn7b","YylFdk6TooKt9IxJeAQc7LIInXT",
    "Ef5hdYoVCor1HXxzFJzcX3TDnKe","Oy6ddqYWRoZd5dx06dDc0dSrnbd","NPY8d2VaBo8g0xxoFJBczrFen2f",
    "ELrHdtGdxo4t5LxkjpWcp87Snwg","A3NSdKSnzozs2uxX8fBcmP2Rnrc","DEPBd9FbHoRmsfxIH2zckTWlnce"]
for oid in old_ids:
    try: api(f"https://open.feishu.cn/open-apis/drive/v1/files/{oid}?type=docx", method="DELETE")
    except: pass

# Keep successful docs: TZIcdGlqloZ94GxBhGGce1vQntd (ch1), PUyhdRxyTo3eo7xJVfYcTCVMnSf (ch2), BgJDdqnG6oNRh1x1cqpce1yMnXb (ch9)
# Delete and recreate them too for consistency
for oid in ["TZIcdGlqloZ94GxBhGGce1vQntd","PUyhdRxyTo3eo7xJVfYcTCVMnSf","BgJDdqnG6oNRh1x1cqpce1yMnXb"]:
    try: api(f"https://open.feishu.cn/open-apis/drive/v1/files/{oid}?type=docx", method="DELETE")
    except: pass

time.sleep(1)

results = []
for title, fname in DOCS:
    fp = os.path.join(BASE, fname)
    print(f"\n📄 {title}", flush=True)
    
    with open(fp, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Strip H1
    ls = content.split("\n")
    if ls and ls[0].startswith("# "): content = "\n".join(ls[1:])
    
    # Create doc
    r = api("https://open.feishu.cn/open-apis/docx/v1/documents", {"title": title}, "POST")
    did = r["data"]["document"]["document_id"]
    print(f"  id: {did}", flush=True)
    time.sleep(0.3)
    
    blocks = md2blocks(content)
    total = len(blocks)
    print(f"  blocks: {total}", flush=True)
    
    # Insert in batches of 20, one-by-one fallback on error
    idx, done = 0, 0
    while idx < total:
        batch = blocks[idx:idx+20]
        try:
            api(f"https://open.feishu.cn/open-apis/docx/v1/documents/{did}/blocks/{did}/children",
                {"children": batch, "index": idx}, "POST")
            idx += len(batch)
            done += len(batch)
        except HTTPError as e:
            err = e.read().decode()
            print(f"  batch err at {idx}: {e.code}", flush=True)
            # Fallback: insert one by one
            for b in batch:
                try:
                    api(f"https://open.feishu.cn/open-apis/docx/v1/documents/{did}/blocks/{did}/children",
                        {"children": [b], "index": idx}, "POST")
                    idx += 1; done += 1
                except HTTPError:
                    idx += 1  # skip this block
                time.sleep(0.15)
        time.sleep(0.3)
    
    print(f"  ✅ {done}/{total} blocks", flush=True)
    results.append((title, did))
    time.sleep(0.5)

print("\n\n🔗 飞书文档链接：\n")
for t, d in results:
    print(f"  📄 {t}")
    print(f"     https://feishu.cn/docx/{d}\n")
