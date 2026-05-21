# 起点中文网自动发布工具

阅文作家专区（write.qq.com）全自动章节发布脚本。

## 目录结构

```
qidian_auto_publish/
├── login.py          # QQ扫码登录工具
├── publish.py        # 章节自动发布脚本
├── state.json        # 登录状态（自动生成，.gitignore）
├── chapters/         # 待发章节（按书名分子目录）
│   └── 书名/
│       ├── 第1章_xxx.txt
│       └── 第2章_xxx.txt
└── uploaded/         # 已发布归档
    └── 书名/
```

## 快速开始

### 1. 首次登录

```bash
cd auto_publish/qidian_auto_publish
.venv/bin/python3 login.py
```

弹出浏览器后，使用手机QQ扫码登录阅文作家专区。登录成功后自动保存 Cookie 到 `state.json`。

### 2. 准备章节

将待发章节放入 `chapters/书名/` 目录，每章一个 txt 文件：

```
chapters/
└── 我在修仙界开网约车/
    ├── 第1章_穿越.txt
    ├── 第2章_系统绑定.txt
    └── 第3章_第一单.txt
```

文件名需包含章节号（如"第1章"、"第2章"），用于排序和识别。

### 3. 发布章节

```bash
# 交互选择要发布的小说
.venv/bin/python3 publish.py

# 指定书名直接发布
.venv/bin/python3 publish.py --book "我在修仙界开网约车"

# 只发布前3章
.venv/bin/python3 publish.py --book "我在修仙界开网约车" --count 3

# 存草稿模式（不直接发布）
.venv/bin/python3 publish.py --book "我在修仙界开网约车" --draft
```

## 常用参数

| 参数 | 说明 |
|------|------|
| `--book "书名"` | 指定书名（自动选择，跳过交互） |
| `--count N` | 发布章节数量 |
| `--draft` | 存草稿模式（不直接发布） |

## 发布流程

1. 启动浏览器，加载保存的登录状态
2. 跳转阅文作家专区（write.qq.com）
3. 找到对应书籍 → 进入章节管理
4. 逐章：填写标题 → 注入正文 → 发布/存草稿
5. 成功后自动归档到 `uploaded/书名/`

## 注意事项

- Cookie 会过期，登录过期时重新运行 `login.py`
- 起点UI可能变化，如发布失败请检查截图 `error_*.png`
- 起点有内容审核机制，需确保内容合规
- 脚本使用 Playwright，需要安装 chromium 浏览器
