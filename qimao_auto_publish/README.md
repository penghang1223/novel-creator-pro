# 七猫免费小说自动发布工具

基于 Playwright 的七猫作家专区自动发布脚本。

## 目录结构

```
qimao_auto_publish/
├── login.py        # 登录脚本（保存Cookie）
├── publish.py      # 自动发布脚本
├── state.json      # 登录状态（自动生成，已忽略）
├── chapters/       # 待发布章节
│   └── 书名/       # 每本书一个子目录
│       ├── 第001章 标题.txt
│       └── 第002章 标题.txt
└── uploaded/       # 已发布章节归档
```

## 使用方法

### 1. 首次登录

```bash
cd qimao_auto_publish
python3 login.py
```

浏览器会打开七猫作家登录页面，支持：
- 手机验证码登录
- 账号密码登录

登录成功后在终端按回车，自动保存 Cookie 到 `state.json`。

### 2. 准备章节文件

将章节 `.txt` 文件放入 `chapters/{书名}/` 目录：

```
chapters/
  └── 我的小说名/
      ├── 第001章 开始.txt
      ├── 第002章 发展.txt
      └── 第003章 高潮.txt
```

文件名格式：`第{N}章 {标题}.txt`（标题可选）

### 3. 发布章节

```bash
# 发布所有章节
python3 publish.py --book "我的小说名"

# 发布前3章
python3 publish.py --book "我的小说名" --count 3

# 存草稿模式（不直接发布）
python3 publish.py --book "我的小说名" --draft

# 交互式选择书籍
python3 publish.py
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `--book "书名"` | 指定书名（模糊匹配，自动选择） |
| `--count N` | 发布章节数量 |
| `--draft` | 存草稿模式（不直接发布） |
