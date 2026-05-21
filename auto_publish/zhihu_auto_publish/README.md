# 知乎盐选自动发布工具

知乎创作中心（签约后）全自动作品发布脚本。

> **注意**：知乎盐选采用投稿制，需要先投稿等待编辑审核（3-20天），签约后才能发布。本脚本仅支持**签约后**的作品发布。

## 目录结构

```
zhihu_auto_publish/
├── login.py          # 知乎登录工具
├── publish.py        # 章节自动发布脚本
├── state.json        # 登录状态（自动生成，.gitignore）
├── chapters/         # 待发章节（按作品名分子目录）
│   └── 作品名/
│       ├── 第1章_xxx.txt
│       └── 第2章_xxx.txt
└── uploaded/         # 已发布归档
    └── 作品名/
```

## 快速开始

### 1. 首次登录

```bash
cd auto_publish/zhihu_auto_publish
.venv/bin/python3 login.py
```

弹出浏览器后，使用手机号/邮箱/扫码等方式登录知乎。登录成功并进入创作中心后按回车继续。

### 2. 准备章节

将待发章节放入 `chapters/作品名/` 目录，每章一个 txt 文件：

```
chapters/
└── 我的知乎故事/
    ├── 第1章_开头.txt
    ├── 第2章_发展.txt
    └── 第3章_高潮.txt
```

### 3. 发布章节

```bash
# 交互选择要发布的作品
.venv/bin/python3 publish.py

# 指定作品名直接发布
.venv/bin/python3 publish.py --book "我的知乎故事"

# 只发布前5章
.venv/bin/python3 publish.py --book "我的知乎故事" --count 5

# 存草稿模式（不直接发布）
.venv/bin/python3 publish.py --book "我的知乎故事" --draft
```

## 常用参数

| 参数 | 说明 |
|------|------|
| `--book "作品名"` | 指定作品名（自动选择，跳过交互） |
| `--count N` | 发布章节数量 |
| `--draft` | 存草稿模式（不直接发布） |

## 发布流程

1. 启动浏览器，加载保存的登录状态
2. 跳转知乎创作中心（zhihu.com/creator）
3. 找到对应作品 → 进入编辑模式
4. 逐章：填写标题 → 注入正文 → 发布/存草稿
5. 成功后自动归档到 `uploaded/作品名/`

## 注意事项

- Cookie 会过期，登录过期时重新运行 `login.py`
- 知乎UI可能变化，如发布失败请检查截图 `error_*.png`
- 知乎有内容审核机制，需确保内容合规
- 脚本使用 Playwright，需要安装 chromium 浏览器
- 本脚本仅支持**签约后**发布，首次投稿需手动完成
