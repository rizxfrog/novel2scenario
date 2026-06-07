# Novel2Scenario — 项目入门指南

> 基于知识图谱自动生成 | 分析时间: 2026-06-07 | Commit: `88ad0d2`

---

## 1. 项目概览

**AI 小说转剧本工具** — 将小说文本自动转换为结构化剧本（JSON/YAML 格式）。

| 项目属性 | 详情 |
|----------|------|
| **后端** | Python 3.14, FastAPI, Uvicorn |
| **前端** | React 18, TypeScript, Vite |
| **数据库** | SQLite (WAL 模式) |
| **AI 引擎** | OpenAI GPT-4o |
| **数据模型** | Pydantic v2 (15 个模型类) |
| **测试** | pytest + FastAPI TestClient |

**核心能力：** 上传 TXT 小说 → 自动五阶段流水线处理 → 输出结构化剧本 JSON/YAML。

---

## 2. 架构分层

项目按职责划分为 **8 个架构层**：

### 2.1 配置与入口层 (`layer:config`)
> 11 个文件 — 环境变量配置、FastAPI 启动、构建工具配置

| 文件 | 说明 | 复杂度 |
|------|------|--------|
| `main.py`（根目录） | uvicorn 启动入口，监听 8000 端口 | simple |
| `backend/main.py` | FastAPI 应用工厂，CORS + 路由注册 | simple |
| `backend/config.py` | dotenv 环境变量加载 | simple |
| `.env` / `.env.example` | API Key、Base URL、模型名、并发数 | simple |
| `pyproject.toml` | Python 3.14 项目配置 | simple |
| `frontend/package.json` | Vite + React 构建脚本 | simple |

### 2.2 数据层 (`layer:data`)
> 2 个文件 — SQLite 连接 + Pydantic 模型

| 文件 | 说明 | 复杂度 |
|------|------|--------|
| `backend/database.py` | 线程安全 SQLite 连接，线程本地存储，8 张表初始化 | moderate |
| `backend/models.py` | 15 个 Pydantic 模型：Job/Character/Scene/Episode/Script | moderate |

### 2.3 AI 引擎层 (`layer:ai-agent`)
> 3 个文件 — GPT-4o 客户端、提示词模板、JSON 解析

| 文件 | 说明 | 复杂度 |
|------|------|--------|
| `backend/agents/engine.py` | OpenAI 客户端、带重试的 Agent 调用、鲁棒 JSON 解析（截断修复）| **complex** |
| `backend/agents/prompts.py` | 五阶段 LLM 提示词模板 | moderate |

### 2.4 业务服务层 (`layer:service`)
> 7 个文件 — 五阶段管线 + 编排器

| 文件 | 说明 | 复杂度 |
|------|------|--------|
| `backend/pipeline/orchestrator.py` | **核心编排器（546 行）**：状态机驱动五阶段推进、断点重试、CRUD | **complex** |
| `backend/pipeline/splitter.py` | 章节拆分：正则 + LLM 双轨 | moderate |
| `backend/pipeline/characters.py` | 角色提取：并行 + 去重合并 | moderate |
| `backend/pipeline/scenes.py` | 场景分析：并行分析每章场景 | simple |
| `backend/pipeline/episodes.py` | 剧集结构化：场景 → 剧集 | simple |
| `backend/pipeline/assembler.py` | 剧本组装：人物表 + 编号 + 改编说明 | moderate |

### 2.5 API 路由层 (`layer:api`)
> 6 个文件 — FastAPI 端点

| 文件 | 说明 | 复杂度 |
|------|------|--------|
| `backend/routes/jobs.py` | 作业 CRUD（列表/创建/状态/删除/继续/重试）| moderate |
| `backend/routes/characters.py` | 角色列表 + 批量保存 | simple |
| `backend/routes/scenes.py` | 场景列表 + 批量保存 | simple |
| `backend/routes/episodes.py` | 剧集列表 + 批量保存 | simple |
| `backend/routes/ai_assist.py` | AI 辅助自然语言编辑 | simple |

### 2.6 前端层 (`layer:frontend`)
> 28 个文件 — React 18 单页面应用

| 文件 | 说明 |
|------|------|
| `src/App.tsx` | 根组件：`<JobProvider><PipelineView/>` |
| `src/context/JobContext.tsx` | useReducer 全局状态，2s 自动轮询 |
| `src/context/reducer.ts` | 9 种 Action 的状态转换 |
| `src/components/PipelineView.tsx` | 流水线主视图（Sidebar + StagePanel + StatusBar）|
| `src/components/Sidebar.tsx` | 作业列表（搜索/筛选/选择/删除/新建）|
| `src/components/StagePanel.tsx` | 可折叠阶段面板（4 种状态指示器）|
| `src/components/StatusBar.tsx` | 底部进度条（N/5 + 状态徽章）|
| `src/components/stages/*.tsx` | 6 个阶段面板组件（Upload/Chapter/Character/Scene/Episode/Script）|

### 2.7 测试层 (`layer:tests`)
> 10 个文件 — pytest + TestClient

| 文件 | 说明 |
|------|------|
| `tests/test_agent_engine.py` | Agent JSON 解析 + 重试 + 并发 |
| `tests/test_splitter.py` | 章节拆分准确性 |
| `tests/test_characters.py` | 并行提取 + 去重 |
| `tests/test_scenes.py` | 场景分析 |
| `tests/test_episodes.py` | 剧集结构化 |
| `tests/test_assembler.py` | 剧本组装完整性 |
| `tests/test_orchestrator.py` | 管线状态机推进 |
| `tests/test_database.py` | 库初始化 + 表结构 |
| `tests/test_integration.py` | 端到端 API 完整流程 |
| `tests/sample_novel.txt` | 4 章中文测试样本 |

### 2.8 文档层 (`layer:documentation`)
> 9 个文件

- `README.md` — 快速开始指南
- `docs/script-yaml-schema.md` — YAML Schema v1 定义
- `docs/plans/2026-06-05-novel-to-script.md` — 原始实施计划（26 任务）
- `docs/plans/2026-06-07-pipeline-rebuild.md` — 前端重构计划（1524 行）
- `docs/designs/` — 架构设计文档
- `.superpowers/brainstorm/` — 方案对比 + 布局原型

---

## 3. 关键设计概念

### 3.1 五阶段流水线

```
小说 TXT → 分章 → 角色提取 → 场景分析 → 剧集结构化 → 剧本组装 → JSON/YAML
```

### 3.2 阶段状态追踪

新增的 `stage_status` 表为每个 Job 的 5 个阶段提供独立状态：
`pending` → `running` → `awaiting_review` / `completed` / `failed`

### 3.3 断点重试（Checkpoint Retry）

- 从任意阶段重新运行
- 自动级联清理下游数据（`_cleanup_downstream`）
- 重置受影响阶段为 `pending`

### 3.4 前端全局状态管理

- React Context + useReducer（非 Redux）
- 9 种 Action 类型
- 2 秒自动轮询（`running` → `awaiting_review` 自动停止）

### 3.5 AI 引擎核心设计

- 延迟初始化 AsyncOpenAI 客户端
- JSON 响应多层容错：markdown fence 剥离 → 栈平衡截断修复 → 逐前缀回退
- 指数退避重试 + 自动扩展 completion token

---

## 4. 导览路径（11 步）

| # | 步骤 | 重点 |
|---|------|------|
| 1 | **项目概览** | 阅读 `README.md`，了解整体定位 |
| 2 | **服务入口与配置** | `main.py` + `backend/main.py` + `backend/config.py` + `.env` |
| 3 | **数据模型层** | `backend/models.py`（15 个 Pydantic 模型） |
| 4 | **数据库层** | `backend/database.py`（SQLite WAL + 8 表） |
| 5 | **AI 引擎核心** | `backend/agents/engine.py` + `prompts.py` |
| 6 | **流水线一、二阶段** | `splitter.py`（正则+LLM）+ `characters.py`（并行+去重）|
| 7 | **流水线三至五阶段** | `scenes.py` + `episodes.py` + `assembler.py` |
| 8 | **编排器状态机** | `orchestrator.py`（546 行核心） |
| 9 | **API 路由层** | `routes/jobs.py` + `characters.py` + `scenes.py` + `episodes.py` + `ai_assist.py` |
| 10 | **前端 Pipeline 界面** | `App.tsx` → `JobContext` → `PipelineView` → 6 个 Stage 组件 |
| 11 | **测试体系** | 9 个测试文件 + 样本数据 |

---

## 5. 复杂度热点

以下模块需要特别注意，建议有经验后再深入修改：

| 热度 | 文件 | 原因 |
|------|------|------|
| 🔴 **极高** | `backend/pipeline/orchestrator.py` | 546 行核心编排器，包含 20+ 复杂函数，所有模块通过它间接协作 |
| 🔴 **极高** | `backend/agents/engine.py` | JSON 截断修复（栈平衡+前缀回退）、指数退避重试、并发控制 |
| 🟡 **较高** | `frontend/src/context/JobContext.tsx` | useReducer + 2s 轮询 + 多 Action 协同 |
| 🟡 **较高** | `frontend/src/components/PipelineView.tsx` | 组合 3 个子组件 + 6 个阶段面板 + 状态协调 |
| 🟡 **较高** | `backend/routes/jobs.py` | 81 行，包含 10+ CRUD 端点 |
| 🟢 **中等** | `backend/pipeline/characters.py` | 并行 Agent + 姓名去重合并 |
| 🟢 **中等** | `backend/pipeline/splitter.py` | 正则+LLM 双轨策略 |
| 🟢 **中等** | `backend/database.py` | 线程安全 + WAL 模式 |

---

## 6. 项目结构速查

```
novel2scenario/
├── main.py                          # uvicorn 启动入口
├── .env / .env.example              # 环境配置
├── pyproject.toml                   # Python 项目配置
├── backend/
│   ├── __init__.py
│   ├── main.py                      # FastAPI 应用工厂
│   ├── config.py                    # 环境变量加载
│   ├── database.py                  # SQLite 连接 (moderate)
│   ├── models.py                    # Pydantic 模型 (moderate)
│   ├── agents/
│   │   ├── engine.py                # GPT-4o 引擎 (complex)
│   │   └── prompts.py              # LLM 提示词模板 (moderate)
│   ├── pipeline/
│   │   ├── orchestrator.py          # 核心编排器 (complex)
│   │   ├── splitter.py             # 章节拆分 (moderate)
│   │   ├── characters.py           # 角色提取 (moderate)
│   │   ├── scenes.py               # 场景分析 (simple)
│   │   ├── episodes.py             # 剧集结构化 (simple)
│   │   └── assembler.py            # 剧本组装 (moderate)
│   └── routes/
│       ├── jobs.py                  # 作业 CRUD (moderate)
│       ├── characters.py            # 角色 API (simple)
│       ├── scenes.py                # 场景 API (simple)
│       ├── episodes.py              # 剧集 API (simple)
│       └── ai_assist.py             # AI 辅助编辑 (simple)
├── frontend/
│   ├── index.html                   # SPA 入口
│   ├── vite.config.ts               # Vite 配置（代理 /api → 8000）
│   └── src/
│       ├── main.tsx                 # React 入口
│       ├── App.tsx                  # 根组件
│       ├── api.ts                   # API 客户端 + 类型定义
│       ├── index.css                # 全局样式
│       ├── context/
│       │   ├── JobContext.tsx        # 全局状态 Context
│       │   └── reducer.ts           # useReducer + Action 定义
│       └── components/
│           ├── PipelineView.tsx      # 主视图
│           ├── Sidebar.tsx           # 作业侧栏
│           ├── StagePanel.tsx        # 阶段面板
│           ├── StatusBar.tsx         # 状态栏
│           └── stages/
│               ├── UploadStage.tsx   # 上传阶段
│               ├── ChapterStage.tsx  # 分章展示
│               ├── CharacterStage.tsx # 角色编辑
│               ├── SceneStage.tsx     # 场景编辑
│               ├── EpisodeStage.tsx   # 剧集编辑
│               └── ScriptStage.tsx    # 剧本预览
├── tests/
│   ├── sample_novel.txt             # 测试样本（4章）
│   ├── test_integration.py          # 端到端测试
│   ├── test_agent_engine.py
│   ├── test_splitter.py
│   ├── test_characters.py
│   ├── test_scenes.py
│   ├── test_episodes.py
│   ├── test_assembler.py
│   ├── test_orchestrator.py
│   └── test_database.py
├── docs/
│   ├── ONBOARDING.md                # 本文档
│   ├── script-yaml-schema.md
│   ├── plans/
│   │   ├── 2026-06-05-novel-to-script.md
│   │   └── 2026-06-07-pipeline-rebuild.md
│   └── designs/
│       ├── 2026-06-05-novel-to-script-design.md
│       └── 2026-06-07-pipeline-rebuild-design.md
└── README.md
```

---

## 7. 快速上手

```bash
# 1. 安装依赖
pip install -e .                    # Python 后端
cd frontend && npm install          # 前端

# 2. 配置环境
cp .env.example .env                # 填入 API Key

# 3. 启动后端
python main.py                      # uvicorn --reload, 端口 8000

# 4. 启动前端（新终端）
cd frontend && npm run dev          # Vite, 端口 5173

# 5. 运行测试
pytest tests/ -v
```

---

*本指南由 Understand Anything 知识图谱自动生成，建议提交到仓库供团队参考。*
