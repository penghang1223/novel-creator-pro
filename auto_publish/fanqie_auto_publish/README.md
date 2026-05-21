# 番茄小说自动发布工具

基于 Playwright 的番茄作家助手自动发布脚本。

## 目录结构

```
fanqie_auto_publish/
├── login.py              # 登录脚本（保存 Cookie）
├── publish.py            # 自动发布脚本
├── state.json            # 登录状态（自动生成，已忽略）
├── chapters/             # 待发布小说章节
│   └── 书名/
│       ├── 第001章.txt
│       └── 第002章.txt
├── short_chapters/       # 待发布短故事
│   └── 短故事名/
│       └── 短故事.txt
├── uploaded/             # 已发布章节归档
└── short_uploaded/       # 已发布短故事归档
```

## 使用方法

### 1. 首次登录

```bash
cd auto_publish/fanqie_auto_publish
python3 login.py
```

浏览器会打开番茄作家助手登录页面，扫码或手机验证码登录。

登录成功后在终端按回车，自动保存 Cookie 到 `state.json`。

### 2. 同步章节

从 `novel_output/` 同步到发布目录：

```bash
python scripts/sync_to_fanqie.py              # 同步所有小说
python scripts/sync_to_fanqie.py --short      # 同步所有短故事
python scripts/sync_to_fanqie.py "书名"        # 同步指定小说
```

### 3. 发布章节

```bash
# 发布所有章节
python3 publish.py --book "书名"

# 发布前3章
python3 publish.py --book "书名" --count 3

# 存草稿模式（不直接发布）
python3 publish.py --book "书名" --draft

# 发布短故事
python3 publish.py --short --book "短故事名"
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `--book "书名"` | 指定书名（模糊匹配，自动选择） |
| `--count N` | 发布章节数量 |
| `--draft` | 存草稿模式（不直接发布） |
| `--short` | 短故事模式（合并所有章节为一个文档） |
| `--no-close` | 不关闭浏览器（便于调试） |
