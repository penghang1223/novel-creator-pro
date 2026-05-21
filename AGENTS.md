# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

> **权威项目文档在 [`CLAUDE.md`](CLAUDE.md)。** AGENTS.md 只保留 Codex 侧专属信息，所有流程、架构、工具用法、文件指针等详细内容请直接读取 CLAUDE.md。

---

## 双端共享记忆

本项目支持终端 Claude 和飞书 Claude 两个实例同时运行。**必须读取以下共享记忆文件**（启动时加载）：

1. `MEMORY.md` — 共享记忆索引
2. `.claude/memory/decisions/preferences.md` — 用户偏好与协作规则
3. `.claude/memory/active_novels/progress.md` — 当前小说进度
4. `.claude/memory/feedback/corrections.md` — 用户纠正（如字数红线）
5. `.claude/memory/feedback/no-mer-names.md` — 角色名禁止带"默"字

**任何小说进度推进、角色状态变化、伏笔更新，必须同步更新 `knowledge_base/80_Projects/` 对应文件。** 两边实例依赖这些文件保持一致状态。

## Codex 侧 MCP 配置

`.claude/settings.json` 中预置两个 MCP 服务器：

- **`chrome-devtools`** — Chrome 浏览器自动化（用于发布验证、竞品调研、故障排查）
- **`lark-mcp`** — 飞书 Lark API（用于读取飞书文档/wiki、操作多维表格）

## 默认角色

进入此仓库时，**默认以"小说创作 Pro Max 专职助手"身份响应**。不需要用户额外说"激活小说技能"或"进入创作模式"。

## 完整文档

以下全部内容请直接读取 CLAUDE.md：

- 知识库管理系统（Ingest 工作流、Ship-Learn-Next、三级反思、定期巡检）
- 默认工作流（短篇/长篇第1章/长篇续写/风格人物设定）
- 行为准则
- 新增功能清单
- 小说输出目录约定
- 项目架构（四层设计）
- Python 依赖与常用命令
- 质量约束系统（三级红线、9问）
- 重要文件指针
- 自动发布模块（番茄/起点/知乎）
- LLM Wiki 知识库（Karpathy 模式）
