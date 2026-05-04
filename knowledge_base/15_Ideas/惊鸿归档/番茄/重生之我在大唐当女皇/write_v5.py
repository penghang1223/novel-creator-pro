#!/usr/bin/env python3
"""Create Feishu docs - insert blocks one by one for reliability."""
import json, re, os, time
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE = "/Users/narain/.openclaw/workspace-jinghong/重生之我在大唐当女皇/"

# Get token
data = json.dumps({"app_id":"cli_a93c22c0f538dbc6","app_secret":"n7drLxI0Tj8ZPV3XVNGvZbspOJdjywzi"}).encode()
req = Request("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal", data,
    {"Content-Type":"application/json"}, method="POST")
token = json.loads(urlopen(req, timeout=15).read())["tenant_access_token"]
print("Token OK", flush=True)

def api_call(url, body=None, method="GET"):
    d = json.dumps(body, ensure_ascii=False).encode("utf-8") if body else None
    r = Request(url, d, {"Authorization":f"Bearer {token}","Content-Type":"application/json"}, method=method)
    return json.loads(urlopen(r, timeout=60).read())

def safe(t):
    return t.replace("\\","\\\\")[:1200]

def md_to_blocks(md):
    blocks, lines, i = [], md.split("\n"), 0
    while i < len(lines):
        s = lines[i].strip()
        if not s: i+=1; continue
        if s in ("---","***"): blocks.append({"block_type":22}); i+=1; continue
        m = re.match(r"^(#{2,3})\s+(.*)",s)
        if m:
            txt=safe(m.group(2).strip()); bt=4 if len(m.group(1))==2 else 5
            k="heading2" if bt==4 else "heading3"
            blocks.append({"block_type":bt,k:{"elements":[{"text_run":{"content":txt}}]}})
            i+=1; continue
        para=[]
        while i<len(lines):
            l=lines[i].strip()
            if not l or re.match(r"^#{1,3}\s",l) or l=="---" or l.startswith("|"): break
            para.append(l); i+=1
        if para:
            blocks.append({"block_type":2,"text":{"elements":[{"text_run":{"content":safe(chr(10).join(para))}}]}})
    return blocks

DOCS=[
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

# Clean up any previously created empty docs
for oid in ["ULxJdQdpFotTVSxQ72EcG4q4nqd","Z6oOdBwJcoVSwlxrjzqcpnAXnqh","UHqsdRH8toiSNKxxG4ZchdlEn7b",
    "Ef5hdYoVCor1HXxzFJzcX3TDnKe","Oy6ddqYWRoZd5dx06dDc0dSrnbd","NPY8d2VaBo8g0xxoFJBczrFen2f",
    "ELrHdtGdxo4t5LxkjpWcp87Snwg","A3NSdKSnzozs2uxX8fBcmP2Rnrc","DEPBd9FbHoRmsfxIH2zckTWlnce",
    "YylFdk6TooKt9IxJeAQc7LIInXT"]:
    try: api_call(f"https://open.feishu.cn/open-apis/drive/v1/files/{oid}?type=docx", method="DELETE")
    except: pass

results=[]
for title,fname in DOCS:
    fp=os.path.join(BASE,fname)
    print(f"\n📄 {title}", flush=True)
    with open(fp,"r",encoding="utf-8") as f: content=f.read()
    ls=content.split("\n")
    if ls and ls[0].startswith("# "): content="\n".join(ls[1:])
    
    # Create doc
    r=api_call("https://open.feishu.cn/open-apis/docx/v1/documents",{"title":title},"POST")
    did=r["data"]["document"]["document_id"]
    print(f"  id: {did}", flush=True)
    time.sleep(0.5)
    
    blocks=md_to_blocks(content)
    print(f"  blocks: {len(blocks)}", flush=True)
    
    # Insert one by one
    done=0
    for idx,b in enumerate(blocks):
        try:
            api_call(f"https://open.feishu.cn/open-apis/docx/v1/documents/{did}/blocks/{did}/children",
                {"children":[b],"index":idx},"POST")
            done+=1
        except HTTPError as e:
            err=e.read().decode("utf-8","replace")[:100]
            print(f"  skip[{idx}]: {e.code} {err}", flush=True)
        if idx%10==0: time.sleep(0.2)
    
    print(f"  ✅ {done}/{len(blocks)}", flush=True)
    results.append((title,did))
    time.sleep(0.5)

print("\n\n🔗 飞书文档链接：\n")
for t,d in results:
    print(f"  📄 {t}")
    print(f"     https://feishu.cn/docx/{d}\n")
