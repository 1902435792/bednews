# 《睡前消息》AI 分析引擎

> 🎯 模拟马督工团队的分析风格，生成深度分析蓝图和口播文稿

[![Antigravity](https://img.shields.io/badge/Platform-Antigravity-blue)](https://github.com/google-gemini/antigravity)
[![Version](https://img.shields.io/badge/Version-15.0-green)]()
[![License](https://img.shields.io/badge/License-MIT-yellow)]()

---

## 🎬 项目简介

这是一个基于 Antigravity (Gemini CLI) 的 AI Skill，用于模拟《睡前消息》节目的深度分析方法论。

**核心能力**：
- 🔍 **热点评估**：抓取微博/知乎热榜，评估选题价值
- 🎭 **三角色协作**：马督工（逻辑）、小戴（数据）、静静（质疑）
- 📊 **历史镜像**：全文搜索 815+ 期历史节目，提取论证结构
- 📝 **蓝图生成**：核心定义 + 论证链条 + 悖论 + 方案钩子
- ✍️ **文稿写作**：4000-5000字口播风格，转折句+数据密集
- 🎨 **可视化归档**：Mermaid + Canvas + Excalidraw

---

## 📁 项目结构

```
.agent/
├── workflows/
│   └── bedtime-news.md          # 主工作流（/bedtime-news）
│
├── resources/bedtime-news/
│   ├── references/              # 参考文档
│   │   ├── bot1_analysis.md     # 核心分析引擎规范
│   │   ├── style.md             # 写作风格指南
│   │   ├── search_tips.md       # 搜索技巧
│   │   └── bedtime_news_index.json  # 历史节目索引
│   │
│   ├── scripts/                 # 脚本工具
│   │   ├── search_archive.py    # 全文搜索（815+期）
│   │   ├── search_index.py      # 索引搜索（快速）
│   │   ├── generate_visual.py   # 可视化生成
│   │   ├── archiver.ps1         # 归档脚本
│   │   └── data_sources/        # 数据增强层
│   │       ├── data_router.py   # 统一调度器
│   │       ├── data_cache.py    # 缓存+评分
│   │       ├── law_search.py    # 法律数据源
│   │       └── academic_search.py  # 学术数据源
│   │
│   ├── archive/                 # 完整文稿库（git clone）
│   │   └── main/                # 815+ 期主节目
│   │
│   └── data/                    # 数据仓库
│       ├── cache/               # 搜索缓存
│       ├── verified/            # 已验证数据
│       └── index/               # 数据索引
```

---

## 🚀 快速开始

### 安装

1. 克隆到 `.agent/` 目录
2. 克隆文稿库：
   ```bash
   git clone --depth 1 https://github.com/bedtimenews/bedtimenews-archive-contents.git .agent/resources/bedtime-news/archive
   ```

### 使用

```bash
# 启动完整工作流
/bedtime-news

# 单独搜索历史节目
python .agent/resources/bedtime-news/scripts/search_archive.py "房地产"

# 深度分析模式（提取论证结构+金句）
python .agent/resources/bedtime-news/scripts/search_archive.py "房地产" --deep

# 数据源查询
python .agent/resources/bedtime-news/scripts/data_sources/data_router.py --query "独居老人" --type auto
```

---

## 🏗️ 核心功能

### 1. 三角色协作

| 角色 | 职责 | 输出格式 |
|------|------|----------|
| **马督工** | 逻辑/主笔，构建分析框架 | `【马督工】：...` |
| **小戴** | 数据/查证，执行搜索验证 | `【小戴】：...` |
| **静静** | 质疑/反方，代表观众提问 | `【静静】：...` |

### 2. 历史镜像搜索

```bash
# 全文搜索
python search_archive.py "死亡 焦虑" --type main --limit 10

# 深度分析（提取核心论点+论证结构+金句）
python search_archive.py "死亡 焦虑" --deep --deep-n 5
```

**输出示例**：
```
📺 第986期 | 相关度: 97
🏗️ 论证结构: 层层剥皮 + 数据堆叠 + 历史类比 + 制度批判
💡 核心论点: 大多数时候，视频跟进新闻是比较慢的...
✨ 金句: 「我们的九年义务教育是有成果的...」
```

### 3. 数据增强层

| 数据源 | 类型 | 权威度 |
|--------|------|--------|
| 国家法律法规数据库 | 法条/判例 | ⭐⭐⭐⭐⭐ |
| Semantic Scholar | 学术论文 | ⭐⭐⭐⭐ |
| 国家统计局（待接入） | 经济数据 | ⭐⭐⭐⭐⭐ |
| search_web | 通用搜索 | ⭐⭐⭐ |

### 4. 可视化归档

```bash
# 自动生成三种格式
python generate_visual.py --blueprint path/to/blueprint.md --output path/to/output
```

| 格式 | 文件 | 用途 |
|------|------|------|
| Mermaid | `.md` | 论证链条流程图 |
| Canvas | `.canvas` | Obsidian 画布 |
| Excalidraw | `.excalidraw.md` | 手绘风格图 |

---

## 📊 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v15.0 | 2026-01-13 | 可视化归档、数据增强层、全文搜索深度分析 |
| v14.0 | 2026-01-12 | 历史节目双链、Pivot检查点、理论框架库 |
| v13.0 | 2026-01-11 | 三角色显式输出、风格指南完善 |

---

## 📋 项目评价

### ✅ 优势

1. **方法论完整**：从选题到成稿的全流程覆盖
2. **数据驱动**：多数据源支持，权威度评分机制
3. **历史复用**：815+ 期文稿可搜索，论证结构可提取
4. **可视化强**：三种格式输出，适配 Obsidian 生态

### ⚠️ 待改进

1. **国家统计局 API**：尚未接入，经济数据依赖网页搜索
2. **反馈回路**：无观众数据反馈机制
3. **多人协作**：暂不支持团队工作流

### 🎯 适用场景

- 时事评论内容创作
- 深度分析报告生成
- 议题研究和资料整理
- Obsidian 知识库构建

---

## 📜 License

MIT License

---

## 🙏 致谢

- [《睡前消息》编辑部](https://archive.bedtime.news)
- [bedtimenews-archive-contents](https://github.com/bedtimenews/bedtimenews-archive-contents)
- [Antigravity (Gemini CLI)](https://github.com/google-gemini/antigravity)
