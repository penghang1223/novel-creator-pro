#!/usr/bin/env python3
"""
飞书文档读取工具

从飞书 wiki/docx 链接读取文档内容，输出为纯文本/Markdown。

用法：
    python tools/read_feishu_doc.py <feishu_url>
    python tools/read_feishu_doc.py <feishu_url> --format markdown
    python tools/read_feishu_doc.py <feishu_url> --output path/to/save.md

凭证自动从 ~/.openclaw/credentials/ 读取。
"""

import json
import os
import re
import sys

import requests

# ─── 凭证加载 ───────────────────────────────────────────

CREDENTIALS_DIR = os.path.expanduser("~/.openclaw/credentials")
MCP_CONFIG = os.path.expanduser("~/.openclaw/workspace/.mcp.json")


def load_credentials():
    """从已有的 openclaw 凭证加载飞书 App ID 和 Secret"""
    app_id = None
    app_secret = None

    # 方式1: 从 MCP 配置读取
    if os.path.exists(MCP_CONFIG):
        with open(MCP_CONFIG) as f:
            mcp = json.load(f)
        lark_mcp = mcp.get("mcpServers", {}).get("lark-mcp", {})
        args = lark_mcp.get("args", [])
        for i, arg in enumerate(args):
            if arg == "-a" and i + 1 < len(args):
                app_id = args[i + 1]
            elif arg == "-s" and i + 1 < len(args):
                app_secret = args[i + 1]

    # 方式2: 从 credentials 目录读取
    secrets_file = os.path.join(CREDENTIALS_DIR, "lark.secrets.json")
    if os.path.exists(secrets_file):
        with open(secrets_file) as f:
            data = json.load(f)
        if not app_secret:
            app_secret = data.get("lark", {}).get("appSecret", "")

    if not app_id or not app_secret:
        print("❌ 未找到飞书凭证，请检查 ~/.openclaw/credentials/ 和 ~/.openclaw/workspace/.mcp.json", file=sys.stderr)
        sys.exit(1)

    return app_id, app_secret


# ─── API 调用 ────────────────────────────────────────────


def get_tenant_token(app_id, app_secret):
    """获取 tenant_access_token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": app_id, "app_secret": app_secret})
    data = resp.json()
    if data.get("code") != 0:
        print(f"❌ 获取 token 失败: {data.get('msg', '')}", file=sys.stderr)
        sys.exit(1)
    return data["tenant_access_token"]


def parse_feishu_url(url):
    """
    解析飞书 wiki/docx 链接，提取 node_token 和 obj_type。

    支持的 URL 格式：
    - https://xxx.feishu.cn/wiki/KmsiwSTTKiib71kVKTTcdcxbnYg
    - https://xxx.feishu.cn/docx/TcI9dLKkIoXENXx9XffcEtbjnkc
    - https://xxx.feishu.cn/wiki/v2/... (带 /wiki/v2/ 的长链接)
    """
    # 尝试提取 wiki token
    wiki_match = re.search(r'/wiki/([A-Za-z0-9]+)', url)
    if wiki_match:
        return wiki_match.group(1), "wiki"

    # 尝试提取 docx token
    docx_match = re.search(r'/docx/([A-Za-z0-9]+)', url)
    if docx_match:
        return docx_match.group(1), "docx"

    # 尝试提取 doc token
    doc_match = re.search(r'/doc/([A-Za-z0-9]+)', url)
    if doc_match:
        return doc_match.group(1), "doc"

    print(f"❌ 无法解析飞书链接: {url}", file=sys.stderr)
    print("支持的格式：https://xxx.feishu.cn/wiki/TOKEN 或 /docx/TOKEN", file=sys.stderr)
    sys.exit(1)


def get_wiki_node(token, node_token):
    """获取 wiki 节点信息"""
    url = f"https://open.feishu.cn/open-apis/wiki/v2/spaces/get_node?token={node_token}"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    data = resp.json()
    if data.get("code") != 0:
        print(f"❌ 获取 wiki 节点失败: {data.get('msg', '')}", file=sys.stderr)
        return None
    return data["data"]["node"]


def get_raw_content(token, obj_token, obj_type="docx"):
    """获取文档原始内容"""
    if obj_type == "docx":
        url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{obj_token}/raw_content?lang=0"
    elif obj_type == "doc":
        url = f"https://open.feishu.cn/open-apis/doc/v2/{obj_token}/raw_content"
    else:
        return None

    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    data = resp.json()
    if data.get("code") != 0:
        print(f"⚠️ raw_content 接口失败 ({data.get('code')}): {data.get('msg', '')}", file=sys.stderr)
        return None
    return data["data"].get("content", "")


# ─── 输出格式 ────────────────────────────────────────────


def format_output(raw_content, title="", fmt="text"):
    """格式化输出内容"""
    lines = []
    if title:
        lines.append(f"# {title}\n")

    # 原始内容已经包含了一定的格式，做简单清洗
    content = raw_content.strip()

    # 去除连续的多个分隔线
    content = re.sub(r'\n\s*---\s*\n\s*---\s*\n', '\n---\n', content)

    lines.append(content)
    return "\n".join(lines)


# ─── 主流程 ──────────────────────────────────────────────


def main():
    import argparse
    parser = argparse.ArgumentParser(description="读取飞书文档内容")
    parser.add_argument("url", help="飞书 wiki/docx 链接")
    parser.add_argument("--format", "-f", choices=["text", "markdown"], default="text",
                        help="输出格式（默认：text）")
    parser.add_argument("--output", "-o", help="输出到文件路径")
    args = parser.parse_args()

    # 1. 加载凭证
    app_id, app_secret = load_credentials()

    # 2. 获取 token
    token = get_tenant_token(app_id, app_secret)

    # 3. 解析 URL
    node_token, node_type = parse_feishu_url(args.url)

    # 4. 如果是 wiki 链接，先获取节点信息拿到 obj_token
    obj_token = node_token
    obj_type = "docx"
    title = ""

    if node_type == "wiki":
        node = get_wiki_node(token, node_token)
        if node:
            obj_token = node.get("obj_token", node_token)
            obj_type = node.get("obj_type", "docx")
            title = node.get("title", "")
            print(f"📄 文档标题: {title}", file=sys.stderr)
            print(f"   类型: {obj_type}", file=sys.stderr)

    # 5. 获取内容
    content = get_raw_content(token, obj_token, obj_type)
    if not content:
        print("❌ 无法获取文档内容", file=sys.stderr)
        sys.exit(1)

    # 6. 输出
    result = format_output(content, title, args.format)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"✅ 内容已保存到: {args.output}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()
