# 《睡前消息》分析引擎 - Antigravity Skill

> 专为 [Antigravity (Gemini CLI)](https://github.com/google-gemini/antigravity) 设计的 AI Skill，模拟马督工团队的深度分析方法论

---

## 什么是 Antigravity Skill？

**Antigravity** 是 Google 开源的下一代 AI 编程助手，基于 Gemini 模型。**Skill** 是 Antigravity 的扩展机制，通过 `.agent/workflows/` 和 `.agent/resources/` 目录定义工作流和资源。

本项目是一个完整的 Antigravity Skill 示例，展示了如何：
- 定义复杂的多阶段工作流
- 集成外部数据源
- 实现智能搜索和检索
- 自动化文档生成

---

## 🎯 Skill 定义

### 工作流入口

```
.agent/workflows/bedtime-news.md  # 触发命令: /bedtime-news
```

### 触发词

```
- /bedtime-news
- 睡前消息、马督工、时事分析
```

### Skill 描述

```yaml
---
description: 《睡前消息》风格分析引擎 - 模拟马督工团队进行议题深度分析并生成口播文稿（4000-5000字）。使用场景：社会议题分析、政策解读、现象批评、争议事件复盘。
---
```

---

## 📁 Skill 结构

```
.agent/
├── workflows/
│   └── bedtime-news.md          # 工作流定义
│
└── resources/bedtime-news/      # 资源目录
    ├── references/              # 参考文档（Markdown）
    │   ├── bot1_analysis.md     # 核心分析逻辑
    │   ├── style.md             # 写作风格规范
    │   └── search_tips.md       # 搜索技巧指南
    │
    ├── scripts/                 # 工具脚本（Python/PowerShell）
    │   ├── search_archive.py    # 全文搜索
    │   ├── generate_visual.py   # 可视化生成
    │   └── data_sources/        # 数据增强层
    │
    └── archive/                 # 外部数据（git clone）
        └── main/                # 815+ 期历史文稿
```

---

## 🔧 Skill 开发模式

### 1. 工作流阶段（Mode）

```markdown
# 在 bedtime-news.md 中定义
Step 1: PLANNING   - 环境检查、选题评估
Step 2: EXECUTION  - 搜索验证、蓝图生成、文稿写作
Step 3: VERIFICATION - 可视化归档、质量检查
```

### 2. 资源引用

```markdown
# 工作流中引用资源
view_file: .agent/resources/bedtime-news/references/bot1_analysis.md
run_command: python .agent/resources/bedtime-news/scripts/search_archive.py "关键词"
```

### 3. 工具调用

```python
# scripts/search_archive.py
# 支持 --deep 深度分析模式

python search_archive.py "房地产" --deep --deep-n 3
```

### 4. 数据增强层

```python
# scripts/data_sources/data_router.py
# 自动路由到合适的数据源

python data_router.py --query "民法典" --type auto
# 输出: 法律数据源 → 权威度 10/10
```

---

## 🚀 安装

### 1. 克隆到 .agent 目录

```bash
# 在你的项目根目录
git clone https://github.com/1902435792/bednews.git .agent/resources/bedtime-news
```

### 2. 复制工作流

```bash
cp .agent/resources/bedtime-news/workflows/bedtime-news.md .agent/workflows/
```

### 3. 克隆文稿库（可选，增强历史搜索）

```bash
git clone --depth 1 https://github.com/bedtimenews/bedtimenews-archive-contents.git .agent/resources/bedtime-news/archive
```

---

## 💡 使用

### 启动工作流

```
/bedtime-news
```

### 单独使用工具

```bash
# 全文搜索历史节目
python .agent/resources/bedtime-news/scripts/search_archive.py "死亡 焦虑"

# 深度分析（提取论证结构+金句）
python .agent/resources/bedtime-news/scripts/search_archive.py "房地产" --deep

# 数据源查询
python .agent/resources/bedtime-news/scripts/data_sources/data_router.py --query "独居" --type auto
```

---

## 🏗️ Skill 架构亮点

### 1. 多角色协作

工作流内置三角色模拟：

| 角色 | 职责 | 输出格式 |
|------|------|----------|
| 马督工 | 逻辑构建 | `【马督工】：...` |
| 小戴 | 数据查证 | `【小戴】：...` |
| 静静 | 质疑反方 | `【静静】：...` |

### 2. 智能搜索

```
相关度评分 → 决定读取深度
├── > 50  → 完整读取 + 结构提取
├── 20-50 → 读取匹配段落
└── < 20  → 仅显示标题
```

### 3. 数据源路由

```
查询类型检测 → 自动选择数据源
├── 法律问题 → law_search.py (权威度 10)
├── 学术问题 → academic_search.py (权威度 8)
└── 其他 → search_web (权威度 5)
```

### 4. 可视化输出

自动生成三种格式：
- `*.md` - Mermaid 流程图
- `*.canvas` - Obsidian 画布
- `*.excalidraw.md` - 手绘风格图

---

## 📊 适用于 Antigravity 的设计原则

1. **工作流文件**：`.agent/workflows/*.md` 定义触发词和执行步骤
2. **资源隔离**：`.agent/resources/<skill-name>/` 存放脚本和参考
3. **脚本可调用**：`run_command: python ...` 调用 Python 脚本
4. **阶段明确**：PLANNING → EXECUTION → VERIFICATION
5. **引用可追溯**：`view_file` 加载参考文档

---

## 📜 License

MIT

---

## 🔗 相关

- [Antigravity (Gemini CLI)](https://github.com/google-gemini/antigravity)
- [《睡前消息》文稿库](https://github.com/bedtimenews/bedtimenews-archive-contents)
- [Skill 开发指南](https://github.com/google-gemini/antigravity/docs/skills)
