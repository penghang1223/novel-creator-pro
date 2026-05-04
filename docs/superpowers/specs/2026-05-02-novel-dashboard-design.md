# 小说创作看板 Dashboard 设计文档

## Context

当前项目有 6+ 本小说分散在 `novel_output/` 各平台目录下，每本有独立的 `novel_state.json` 和 `80_Projects/_config.md`，但缺少统一视图。用户痛点：进度不透明、任务不明确、优先级混乱、缺少截止日期。

## 架构

```
localhost:8080
    │
    ▼
scripts/dashboard_server.py     ← Python 轻量HTTP服务（标准库，零依赖）
    │
    ├── GET /              → 返回 dashboard.html
    ├── GET /api/novels    → 扫描 novel_output/ 返回聚合JSON
    └── GET /api/portfolio → 返回 portfolio.json
```

### 数据源

| 数据源 | 路径 | 内容 |
|--------|------|------|
| novel_state.json | `novel_output/{平台}/{小说}/novel_state.json` | 章节数、状态、卷进度 |
| _config.md | `knowledge_base/80_Projects/{编号}_{小说}/_config.md` | 书名、题材、风格、世界观 |
| portfolio.json | `scripts/portfolio.json` | 优先级、截止日期、待办、发布日历 |

## 新增文件

| 文件 | 行数 | 用途 |
|------|------|------|
| `scripts/dashboard_server.py` | ~100行 | HTTP服务，扫描novel_output，聚合数据 |
| `scripts/dashboard.html` | ~400行 | 单页看板，内嵌CSS+JS |
| `scripts/portfolio.json` | 数据文件 | 跨小说管理元数据 |

## 前端模块

### 1. 阶段看板（Kanban）

6列：创意 → 设定 → 大纲 → 写作中 → 已发布 → 完结
- 每本小说一张卡片，按 `novel_state.status` 和 `portfolio.stage` 归列
- 卡片显示：书名、当前章节数、平台标签
- 拖拽改变阶段（通过修改 portfolio.json）

### 2. 进度条

每本小说一行：
- 书名 + 进度条（当前章/目标章）
- 百分比数字
- 按优先级排序（portfolio.json 中的 priority 字段）

### 3. 发布日历

- 从 portfolio.json 的 calendar 数组读取
- 按日期排序，显示未来7天的事件
- 格式：日期 + 事件描述 + 书名标签

### 4. 待办任务

- 从 portfolio.json 的 novels[].next_action 读取
- 按 priority 排序（P0 > P1 > P2）
- 格式：[P0] 书名 - 待办内容

### 5. 刷新按钮

- 手动点击刷新
- 重新调用 /api/novels 和 /api/portfolio
- 页面不刷新，AJAX 更新 DOM

## portfolio.json Schema

```json
{
  "novels": [
    {
      "slug": "目录名（与 novel_output 下一致）",
      "priority": 0,
      "stage": "创意|设定|大纲|写作中|已发布|完结",
      "deadline": "YYYY-MM-DD 或 null",
      "publish_schedule": "日更|周更|攒稿|已完结",
      "next_action": "下一步具体要做什么",
      "notes": "备注"
    }
  ],
  "calendar": [
    {
      "date": "YYYY-MM-DD",
      "event": "事件描述",
      "novel": "书名简称"
    }
  ]
}
```

## 后端 API

### GET /api/novels

扫描 `novel_output/` 下所有平台目录，读取每本小说的 `novel_state.json`，返回：

```json
{
  "novels": [
    {
      "slug": "003_我在修仙界开网约车",
      "platform": "番茄",
      "title": "我在修仙界开网约车",
      "genre": "穿越系统流（女频）",
      "total_chapters": 43,
      "current_chapter": 43,
      "status": "卷二进行中",
      "word_count": 161069
    }
  ]
}
```

### GET /api/portfolio

直接返回 portfolio.json 内容。

## 技术约束

- Python 标准库 only（http.server + json + os），零外部依赖
- 单 HTML 文件，内嵌 CSS + JS，无构建步骤
- 中文界面
- 深色主题（和 Obsidian 风格一致）
- 本地运行，不需要鉴权

## 启动命令

```bash
python scripts/dashboard_server.py
# 自动打开浏览器到 localhost:8080
```
