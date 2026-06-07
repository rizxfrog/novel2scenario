#!/usr/bin/env python3
"""Update knowledge graph with new/changed/deleted files."""

import json
from datetime import datetime, timezone

# Load current knowledge graph
with open('.understand-anything/knowledge-graph.json', 'r', encoding='utf-8') as f:
    kg = json.load(f)

# Load scan result
with open('.understand-anything/intermediate/scan-result.json', 'r', encoding='utf-8') as f:
    scan = json.load(f)

# Load old fingerprints
with open('.understand-anything/fingerprints.json', 'r', encoding='utf-8') as f:
    fps = json.load(f)

# Current files from scan
current_files = {f['path'] for f in scan['files']}

# Old files from fingerprints  
old_files = set(fps['files'].keys())

# Files to remove (in old fingerprints but not in scan)
removed_files = old_files - current_files
print(f"Removed files: {len(removed_files)}")
for f in sorted(removed_files):
    print(f"  - {f}")

# Files to add (in scan but not in old fingerprints)
new_files = current_files - old_files
print(f"\nNew files: {len(new_files)}")
for f in sorted(new_files):
    print(f"  + {f}")

# ==============================
# 1. Remove nodes for deleted files
# ==============================
removed_ids = set()
for rp in removed_files:
    # Collect all possible node IDs that could reference this file
    removed_ids.add(f"file:{rp}")
    removed_ids.add(f"config:{rp}")
    removed_ids.add(f"document:{rp}")
    removed_ids.add(f"service:{rp}")

# Find all function/class nodes that belong to removed files
func_class_to_remove = set()
for node in kg['nodes']:
    if 'filePath' in node and node['filePath'] in removed_files:
        removed_ids.add(node['id'])
        func_class_to_remove.add(node['id'])

# Filter nodes
old_node_count = len(kg['nodes'])
kg['nodes'] = [n for n in kg['nodes'] if n['id'] not in removed_ids]
print(f"\nNodes removed: {old_node_count - len(kg['nodes'])}")

# Filter edges - remove edges referencing deleted nodes
old_edge_count = len(kg['edges'])
kg['edges'] = [e for e in kg['edges'] 
               if e['source'] not in removed_ids 
               and e['target'] not in removed_ids
               and not any(e['source'].endswith(f':{rp}') or e['target'].endswith(f':{rp}') for rp in removed_files)]
print(f"Edges removed: {old_edge_count - len(kg['edges'])}")

# ==============================
# 2. Update existing nodes for changed files
# ==============================

# Define node overrides for changed files
node_updates = {
    "frontend/src/App.tsx": {
        "summary": "应用程序根组件，通过 JobProvider 上下文包裹 PipelineView 主界面，从多页面路由架构重构为单页面流水线视图。",
        "tags": ["entry-point", "react-component", "app-shell", "provider"],
        "complexity": "simple",
        "languageNotes": "重构后不再使用 React Router，改为由全局 JobContext 驱动单页面流水线视图。"
    },
    "frontend/src/api.ts": {
        "summary": "API 客户端模块，封装与后端 /api 端点的所有 HTTP 通信，包括任务 CRUD、角色/场景/剧集/剧本的获取保存、阶段状态查询、重试和 AI 辅助编辑接口，并定义了完整的数据类型（Job, Character, Scene, Episode, SceneBeat, StageStatus, RetryRequest, JobState）。",
        "tags": ["api-client", "type-definition", "data-model", "service"],
        "complexity": "moderate",
        "languageNotes": "新增了 StageStatus、RetryRequest、JobState 接口和 listJobs、deleteJob、getStages、retryJob、aiAssist 方法，支持完整的管线状态管理。"
    },
    "backend/main.py": {
        "summary": "FastAPI 应用入口点，配置 CORS 中间件、注册所有路由模块（jobs、characters、scenes、episodes、ai_assist），并在启动时初始化数据库。",
        "tags": ["entry-point", "fastapi", "api-server", "cors", "tested"],
        "complexity": "simple"
    },
    "backend/pipeline/orchestrator.py": {
        "summary": "小说到剧本转换管线的核心编排器，管理分章、角色提取、场景分析、剧集结构化和剧本组装五个阶段的完整生命周期，支持阶段状态持久化、重试回退和下游数据清理。",
        "tags": ["orchestrator", "pipeline", "state-machine", "service", "core", "tested"],
        "complexity": "complex",
        "languageNotes": "新增阶段状态表（stage_status）实现细粒度进度追踪，支持 retry_pipeline 从任意阶段重新运行并清理下游数据，list_jobs/delete_job 提供完整的作业管理。"
    },
    "backend/routes/jobs.py": {
        "summary": "作业管理 API 路由，提供作业列表查询、创建、状态查询、删除、管线继续/重试、阶段状态和章节数据查询等完整 CRUD 接口。",
        "tags": ["api-handler", "fastapi", "route", "job-management"],
        "complexity": "moderate"
    },
    "frontend/src/main.tsx": {
        "summary": "应用入口文件，使用 ReactDOM.createRoot 挂载 React 根组件到 DOM，启用 StrictMode 并导入全局 CSS 样式（重构后不再需要 react-router-dom）。",
        "tags": ["entry-point", "bootstrap"],
        "complexity": "simple"
    },
}

# Apply node updates
for node in kg['nodes']:
    fp = node.get('filePath', '')
    if fp in node_updates:
        updates = node_updates[fp]
        for key, value in updates.items():
            node[key] = value

# ==============================
# 3. Add new nodes for new files
# ==============================

new_nodes = [
    # === Backend: ai_assist route ===
    {
        "id": "file:backend/routes/ai_assist.py",
        "type": "file",
        "name": "ai_assist.py",
        "filePath": "backend/routes/ai_assist.py",
        "summary": "AI 辅助编辑 API 路由，接收自然语言修改指令，通过 Agent 引擎对管线阶段数据进行智能编辑并返回修改后的完整数据。",
        "tags": ["api-handler", "fastapi", "route", "ai-assist", "editing"],
        "complexity": "simple",
        "languageNotes": "基于 run_agent 调用，使用专门的 AI_ASSIST_PROMPT 引导 LLM 执行局部修改而非整体重生成。"
    },
    {
        "id": "function:backend/routes/ai_assist.py:ai_assist_edit",
        "type": "function",
        "name": "ai_assist_edit",
        "filePath": "backend/routes/ai_assist.py",
        "lineRange": [21, 32],
        "summary": "AI 辅助编辑端点，接收阶段名称、修改指令和当前数据，通过 run_agent 调用 LLM 执行智能编辑并返回 AIAssistResponse。",
        "tags": ["api-handler", "ai-assist", "editing", "fastapi"],
        "complexity": "simple"
    },
    
    # === Frontend: Context ===
    {
        "id": "file:frontend/src/context/JobContext.tsx",
        "type": "file",
        "name": "JobContext.tsx",
        "filePath": "frontend/src/context/JobContext.tsx",
        "summary": "全局作业状态管理 Context，基于 useReducer 提供作业列表 CRUD、阶段状态自动轮询、管线继续/重试和阶段数据加载等核心业务逻辑。",
        "tags": ["state-management", "react-context", "provider", "core", "pipeline"],
        "complexity": "moderate",
        "languageNotes": "使用 useReducer + Context 模式管理全局状态，2 秒轮询间隔自动刷新运行中的阶段状态，STAGE_DATA_LOADERS 映射表驱动阶段数据懒加载。"
    },
    {
        "id": "function:frontend/src/context/JobContext.tsx:JobProvider",
        "type": "function",
        "name": "JobProvider",
        "filePath": "frontend/src/context/JobContext.tsx",
        "lineRange": [28, 154],
        "summary": "全局 Context Provider 组件，封装 useReducer 状态管理、自动轮询、作业 CRUD 和管线操作等全部业务方法。",
        "tags": ["provider", "state-management", "polling", "context"],
        "complexity": "moderate"
    },
    {
        "id": "function:frontend/src/context/JobContext.tsx:useJobs",
        "type": "function",
        "name": "useJobs",
        "filePath": "frontend/src/context/JobContext.tsx",
        "lineRange": [156, 160],
        "summary": "自定义 Hook，获取 JobContext 值并验证 Provider 包裹，未包裹时抛出错误。",
        "tags": ["hook", "context-consumer", "validation"],
        "complexity": "simple"
    },
    {
        "id": "file:frontend/src/context/reducer.ts",
        "type": "file",
        "name": "reducer.ts",
        "filePath": "frontend/src/context/reducer.ts",
        "summary": "全局状态 reducer 和 Action 类型定义，管理作业列表、活跃作业、阶段状态、阶段数据、加载标志和错误信息的统一状态转换。",
        "tags": ["state-management", "reducer", "type-definition", "data-model"],
        "complexity": "simple",
        "languageNotes": "使用 TypeScript 联合类型定义 8 种 Action 变体，immutable 状态更新模式确保可预测的状态变更。"
    },
    {
        "id": "function:frontend/src/context/reducer.ts:reducer",
        "type": "function",
        "name": "reducer",
        "filePath": "frontend/src/context/reducer.ts",
        "lineRange": [23, 53],
        "summary": "全局状态 reducer 函数，处理 SET_JOBS/SET_ACTIVE_JOB/ADD_JOB/REMOVE_JOB/SET_STAGES/UPDATE_STAGE/SET_STAGE_DATA/SET_LOADING/SET_ERROR 共 9 种 Action。",
        "tags": ["reducer", "state-transition", "immutable"],
        "complexity": "simple"
    },
    
    # === Frontend: PipelineView ===
    {
        "id": "file:frontend/src/components/PipelineView.tsx",
        "type": "file",
        "name": "PipelineView.tsx",
        "filePath": "frontend/src/components/PipelineView.tsx",
        "summary": "流水线主视图组件，组合侧边栏、阶段面板和状态栏，根据当前作业状态渲染五阶段流水线界面，管理阶段间的数据保存和继续推进逻辑。",
        "tags": ["main-view", "pipeline", "orchestration", "react-component", "layout"],
        "complexity": "moderate",
        "languageNotes": "使用 STAGE_COMPONENTS 和 SAVE_APIS 映射表驱动阶段组件选择和保存行为，ref 机制传递阶段编辑数据。"
    },
    {
        "id": "function:frontend/src/components/PipelineView.tsx:PipelineView",
        "type": "function",
        "name": "PipelineView",
        "filePath": "frontend/src/components/PipelineView.tsx",
        "lineRange": [37, 129],
        "summary": "流水线主视图组件，无作业时显示上传界面，有作业时渲染阶段面板列表，协调阶段数据保存和管线继续/重试。",
        "tags": ["main-view", "pipeline", "orchestration", "react-component"],
        "complexity": "moderate"
    },
    
    # === Frontend: Sidebar ===
    {
        "id": "file:frontend/src/components/Sidebar.tsx",
        "type": "file",
        "name": "Sidebar.tsx",
        "filePath": "frontend/src/components/Sidebar.tsx",
        "summary": "作业列表侧边栏组件，提供搜索框、状态筛选下拉菜单和作业列表，支持选择作业、删除作业和新建作业操作。",
        "tags": ["sidebar", "job-list", "navigation", "react-component"],
        "complexity": "simple"
    },
    {
        "id": "function:frontend/src/components/Sidebar.tsx:Sidebar",
        "type": "function",
        "name": "Sidebar",
        "filePath": "frontend/src/components/Sidebar.tsx",
        "lineRange": [21, 97],
        "summary": "侧边栏组件，渲染搜索输入、状态筛选下拉和可选择的作业列表，作业项显示状态图标和删除按钮。",
        "tags": ["sidebar", "job-list", "filtering", "react-component"],
        "complexity": "simple"
    },
    
    # === Frontend: StagePanel ===
    {
        "id": "file:frontend/src/components/StagePanel.tsx",
        "type": "file",
        "name": "StagePanel.tsx",
        "filePath": "frontend/src/components/StagePanel.tsx",
        "summary": "可折叠阶段面板组件，支持四种状态（完成/运行中/等待审核/失败）的可视化指示，提供保存并继续、下游阶段重跑复选框和从此重新运行等操作。",
        "tags": ["panel", "collapsible", "pipeline-stage", "react-component", "ui-component"],
        "complexity": "moderate"
    },
    {
        "id": "function:frontend/src/components/StagePanel.tsx:StagePanel",
        "type": "function",
        "name": "StagePanel",
        "filePath": "frontend/src/components/StagePanel.tsx",
        "lineRange": [28, 143],
        "summary": "阶段面板组件，根据 status 渲染不同状态指示器（完成✓/运行中旋转/等待审核!/失败✕），展开时显示编辑内容和操作按钮。",
        "tags": ["panel", "collapsible", "pipeline-stage", "react-component"],
        "complexity": "moderate"
    },
    
    # === Frontend: StatusBar ===
    {
        "id": "file:frontend/src/components/StatusBar.tsx",
        "type": "file",
        "name": "StatusBar.tsx",
        "filePath": "frontend/src/components/StatusBar.tsx",
        "summary": "底部状态栏组件，显示当前作业标题、阶段进度（N/5）和运行状态徽章（运行中/等待审核/完成/失败/全部完成）。",
        "tags": ["status-bar", "progress", "react-component", "ui-component"],
        "complexity": "simple"
    },
    {
        "id": "function:frontend/src/components/StatusBar.tsx:StatusBar",
        "type": "function",
        "name": "StatusBar",
        "filePath": "frontend/src/components/StatusBar.tsx",
        "lineRange": [20, 75],
        "summary": "状态栏组件，智能检测当前活跃阶段并显示对应的状态徽章和进度信息，失败时显示错误详情。",
        "tags": ["status-bar", "progress", "react-component"],
        "complexity": "simple"
    },
    
    # === Frontend: Stage components ===
    {
        "id": "file:frontend/src/components/stages/UploadStage.tsx",
        "type": "file",
        "name": "UploadStage.tsx",
        "filePath": "frontend/src/components/stages/UploadStage.tsx",
        "summary": "小说上传阶段组件，支持标题/作者输入、TXT 文件拖拽上传和文本粘贴，提交后自动创建作业并启动管线。",
        "tags": ["upload", "stage", "form", "file-input", "react-component"],
        "complexity": "simple"
    },
    {
        "id": "function:frontend/src/components/stages/UploadStage.tsx:UploadStage",
        "type": "function",
        "name": "UploadStage",
        "filePath": "frontend/src/components/stages/UploadStage.tsx",
        "lineRange": [5, 117],
        "summary": "上传阶段组件，支持文件拖拽上传（UTF-8 编码 TXT）、文件选择器和文本粘贴三种输入方式，自动从文件名提取标题。",
        "tags": ["upload", "stage", "form", "drag-and-drop", "react-component"],
        "complexity": "simple"
    },
    {
        "id": "file:frontend/src/components/stages/ChapterStage.tsx",
        "type": "file",
        "name": "ChapterStage.tsx",
        "filePath": "frontend/src/components/stages/ChapterStage.tsx",
        "summary": "章节展示阶段组件，从后端获取并展示分章结果，支持折叠展开查看每章标题、内容和字数统计。",
        "tags": ["chapter", "stage", "display", "collapsible", "react-component"],
        "complexity": "simple"
    },
    {
        "id": "function:frontend/src/components/stages/ChapterStage.tsx:ChapterStage",
        "type": "function",
        "name": "ChapterStage",
        "filePath": "frontend/src/components/stages/ChapterStage.tsx",
        "lineRange": [12, 49],
        "summary": "章节展示组件，获取并渲染分章结果列表，每章可折叠展开查看完整内容。",
        "tags": ["chapter", "stage", "display", "collapsible", "react-component"],
        "complexity": "simple"
    },
    {
        "id": "file:frontend/src/components/stages/CharacterStage.tsx",
        "type": "file",
        "name": "CharacterStage.tsx",
        "filePath": "frontend/src/components/stages/CharacterStage.tsx",
        "summary": "角色编辑阶段组件，展示 AI 提取的角色列表并支持手动编辑和 AI 辅助修改，数据变更自动上报给 PipelineView 用于保存。",
        "tags": ["character", "stage", "editor", "ai-assist", "react-component"],
        "complexity": "moderate"
    },
    {
        "id": "function:frontend/src/components/stages/CharacterStage.tsx:CharacterStage",
        "type": "function",
        "name": "CharacterStage",
        "filePath": "frontend/src/components/stages/CharacterStage.tsx",
        "lineRange": [17, 166],
        "summary": "角色编辑组件，支持内联编辑角色属性（名称、角色类型、特征、描述、关系），集成 AI 辅助面板支持自然语言批量修改。",
        "tags": ["character", "stage", "editor", "inline-editing", "ai-assist", "react-component"],
        "complexity": "moderate"
    },
    {
        "id": "file:frontend/src/components/stages/SceneStage.tsx",
        "type": "file",
        "name": "SceneStage.tsx",
        "filePath": "frontend/src/components/stages/SceneStage.tsx",
        "summary": "场景编辑阶段组件，展示 AI 分析的场景列表，支持折叠展开的节拍编辑和 AI 辅助修改。",
        "tags": ["scene", "stage", "editor", "ai-assist", "react-component"],
        "complexity": "moderate"
    },
    {
        "id": "function:frontend/src/components/stages/SceneStage.tsx:SceneStage",
        "type": "function",
        "name": "SceneStage",
        "filePath": "frontend/src/components/stages/SceneStage.tsx",
        "lineRange": [14, 237],
        "summary": "场景编辑组件，支持按章节分组的场景列表展示、可折叠场景详情和节拍编辑，集成 AI 辅助面板。",
        "tags": ["scene", "stage", "editor", "collapsible", "beat-editing", "ai-assist", "react-component"],
        "complexity": "moderate"
    },
    {
        "id": "file:frontend/src/components/stages/EpisodeStage.tsx",
        "type": "file",
        "name": "EpisodeStage.tsx",
        "filePath": "frontend/src/components/stages/EpisodeStage.tsx",
        "summary": "剧集编辑阶段组件，展示 AI 生成的剧集结构，支持编辑每集标题、摘要和场景分配，集成 AI 辅助修改。",
        "tags": ["episode", "stage", "editor", "ai-assist", "react-component"],
        "complexity": "moderate"
    },
    {
        "id": "function:frontend/src/components/stages/EpisodeStage.tsx:EpisodeStage",
        "type": "function",
        "name": "EpisodeStage",
        "filePath": "frontend/src/components/stages/EpisodeStage.tsx",
        "lineRange": [12, 155],
        "summary": "剧集编辑组件，支持剧集标题/摘要编辑和场景 ID 分配，集成 AI 辅助面板支持自然语言修改。",
        "tags": ["episode", "stage", "editor", "ai-assist", "react-component"],
        "complexity": "moderate"
    },
    {
        "id": "file:frontend/src/components/stages/ScriptStage.tsx",
        "type": "file",
        "name": "ScriptStage.tsx",
        "filePath": "frontend/src/components/stages/ScriptStage.tsx",
        "summary": "剧本预览阶段组件，展示最终生成的剧本 JSON/YAML 数据，提供客户端 YAML 导出下载功能。",
        "tags": ["script", "stage", "preview", "export", "react-component"],
        "complexity": "moderate"
    },
    {
        "id": "function:frontend/src/components/stages/ScriptStage.tsx:ScriptStage",
        "type": "function",
        "name": "ScriptStage",
        "filePath": "frontend/src/components/stages/ScriptStage.tsx",
        "lineRange": [57, 111],
        "summary": "剧本预览组件，获取并展示完整剧本 JSON，内置客户端 toYaml 序列化器生成 YAML 并支持 Blob 下载。",
        "tags": ["script", "stage", "preview", "yaml-export", "react-component"],
        "complexity": "moderate"
    },
    
    # === CSS Module files ===
    {
        "id": "file:frontend/src/components/PipelineView.module.css",
        "type": "file",
        "name": "PipelineView.module.css",
        "filePath": "frontend/src/components/PipelineView.module.css",
        "summary": "PipelineView 组件的 CSS Module 样式，定义全高布局（侧栏 + 右栏）、空状态标题和上传区域样式。",
        "tags": ["styling", "layout", "css-module", "pipeline-view"],
        "complexity": "simple"
    },
    {
        "id": "file:frontend/src/components/Sidebar.module.css",
        "type": "file",
        "name": "Sidebar.module.css",
        "filePath": "frontend/src/components/Sidebar.module.css",
        "summary": "Sidebar 组件的 CSS Module 样式，定义深色侧边栏（搜索、筛选、作业列表、删除按钮、新建按钮）。",
        "tags": ["styling", "sidebar", "css-module", "job-list"],
        "complexity": "simple"
    },
    {
        "id": "file:frontend/src/components/StagePanel.module.css",
        "type": "file",
        "name": "StagePanel.module.css",
        "filePath": "frontend/src/components/StagePanel.module.css",
        "summary": "StagePanel 组件的 CSS Module 样式，定义可折叠面板的头/体区域、四种状态指示器颜色和操作按钮布局。",
        "tags": ["styling", "panel", "collapsible", "css-module", "stage-indicator"],
        "complexity": "moderate"
    },
    {
        "id": "file:frontend/src/components/StatusBar.module.css",
        "type": "file",
        "name": "StatusBar.module.css",
        "filePath": "frontend/src/components/StatusBar.module.css",
        "summary": "StatusBar 组件的 CSS Module 样式，定义底部固定栏、状态徽章颜色方案和进度信息布局。",
        "tags": ["styling", "status-bar", "css-module", "badge"],
        "complexity": "simple"
    },
    {
        "id": "file:frontend/src/components/stages/UploadStage.module.css",
        "type": "file",
        "name": "UploadStage.module.css",
        "filePath": "frontend/src/components/stages/UploadStage.module.css",
        "summary": "UploadStage 组件的 CSS Module 样式，定义文件上传区域、拖拽高亮和表单控件布局。",
        "tags": ["styling", "upload", "css-module", "form"],
        "complexity": "simple"
    },
    {
        "id": "file:frontend/src/components/stages/ChapterStage.module.css",
        "type": "file",
        "name": "ChapterStage.module.css",
        "filePath": "frontend/src/components/stages/ChapterStage.module.css",
        "summary": "ChapterStage 组件的 CSS Module 样式，定义章节列表的可折叠卡片、字数统计和内容预览区域。",
        "tags": ["styling", "chapter", "css-module", "collapsible-card"],
        "complexity": "simple"
    },
    {
        "id": "file:frontend/src/components/stages/CharacterStage.module.css",
        "type": "file",
        "name": "CharacterStage.module.css",
        "filePath": "frontend/src/components/stages/CharacterStage.module.css",
        "summary": "CharacterStage 组件的 CSS Module 样式，定义角色卡片编辑器的内联编辑表单、AI 面板和网格布局。",
        "tags": ["styling", "character", "css-module", "editor", "card-grid"],
        "complexity": "simple"
    },
    {
        "id": "file:frontend/src/components/stages/SceneStage.module.css",
        "type": "file",
        "name": "SceneStage.module.css",
        "filePath": "frontend/src/components/stages/SceneStage.module.css",
        "summary": "SceneStage 组件的 CSS Module 样式，定义场景可折叠面板、节拍子编辑器和 AI 辅助面板的完整布局。",
        "tags": ["styling", "scene", "css-module", "editor", "beat-editor"],
        "complexity": "moderate"
    },
    {
        "id": "file:frontend/src/components/stages/EpisodeStage.module.css",
        "type": "file",
        "name": "EpisodeStage.module.css",
        "filePath": "frontend/src/components/stages/EpisodeStage.module.css",
        "summary": "EpisodeStage 组件的 CSS Module 样式，定义剧集编辑器卡片、摘要输入和场景分配区域布局。",
        "tags": ["styling", "episode", "css-module", "editor"],
        "complexity": "simple"
    },
    {
        "id": "file:frontend/src/components/stages/ScriptStage.module.css",
        "type": "file",
        "name": "ScriptStage.module.css",
        "filePath": "frontend/src/components/stages/ScriptStage.module.css",
        "summary": "ScriptStage 组件的 CSS Module 样式，定义剧本预览代码块、暗色主题和下载按钮布局。",
        "tags": ["styling", "script", "css-module", "preview", "code-display"],
        "complexity": "simple"
    },
    
    # === New Docs ===
    {
        "id": "document:docs/plans/2026-06-07-pipeline-rebuild.md",
        "type": "document",
        "name": "2026-06-07-pipeline-rebuild.md",
        "filePath": "docs/plans/2026-06-07-pipeline-rebuild.md",
        "summary": "前端管线重建实施计划文档（1524 行），详细规划从前端路由器架构重构为管线视图架构的完整方案，涵盖上下文管理、组件拆分、阶段面板和状态轮询等任务。",
        "tags": ["documentation", "planning", "refactoring", "frontend"],
        "complexity": "complex"
    },
    {
        "id": "document:docs/superpowers/specs/2026-06-07-pipeline-rebuild-design.md",
        "type": "document",
        "name": "2026-06-07-pipeline-rebuild-design.md",
        "filePath": "docs/superpowers/specs/2026-06-07-pipeline-rebuild-design.md",
        "summary": "前端管线重建的设计文档（204 行），定义新架构的组件树、状态管理方案和交互流程。",
        "tags": ["documentation", "design", "architecture", "specification"],
        "complexity": "moderate"
    },
    
    # === Brainstorm files (minimal representation) ===
    {
        "id": "file:.superpowers/brainstorm/2238-1780817272/content/approaches.html",
        "type": "file",
        "name": "approaches.html",
        "filePath": ".superpowers/brainstorm/2238-1780817272/content/approaches.html",
        "summary": "Brainstorm 会话输出：技术方案对比 HTML 页面，记录前端管线重构的多方案比较。",
        "tags": ["brainstorm", "html", "design-exploration"],
        "complexity": "simple"
    },
    {
        "id": "file:.superpowers/brainstorm/2238-1780817272/content/layout-mockup.html",
        "type": "file",
        "name": "layout-mockup.html",
        "filePath": ".superpowers/brainstorm/2238-1780817272/content/layout-mockup.html",
        "summary": "Brainstorm 会话输出：前端布局原型 HTML 页面（375 行），展示管线视图的 UI 布局方案。",
        "tags": ["brainstorm", "html", "mockup", "layout"],
        "complexity": "moderate"
    },
    {
        "id": "file:.superpowers/brainstorm/2238-1780817272/content/waiting.html",
        "type": "file",
        "name": "waiting.html",
        "filePath": ".superpowers/brainstorm/2238-1780817272/content/waiting.html",
        "summary": "Brainstorm 会话状态页：等待中提示页面。",
        "tags": ["brainstorm", "html", "status"],
        "complexity": "simple"
    },
]

# Add new nodes
kg['nodes'].extend(new_nodes)
print(f"New nodes added: {len(new_nodes)}")

# ==============================
# 4. Add new edges
# ==============================

new_edges = [
    # === Backend: ai_assist ===
    {"source": "file:backend/routes/ai_assist.py", "target": "file:backend/agents/engine.py", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:backend/routes/ai_assist.py", "target": "file:backend/models.py", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:backend/routes/ai_assist.py", "target": "function:backend/routes/ai_assist.py:ai_assist_edit", "type": "contains", "direction": "forward", "weight": 1.0},
    {"source": "file:backend/routes/ai_assist.py", "target": "function:backend/routes/ai_assist.py:ai_assist_edit", "type": "exports", "direction": "forward", "weight": 0.8},
    {"source": "function:backend/routes/ai_assist.py:ai_assist_edit", "target": "function:backend/agents/engine.py:run_agent", "type": "calls", "direction": "forward", "weight": 0.8},
    {"source": "file:backend/main.py", "target": "file:backend/routes/ai_assist.py", "type": "imports", "direction": "forward", "weight": 0.7},
    
    # === Frontend: App.tsx new imports ===
    {"source": "file:frontend/src/App.tsx", "target": "file:frontend/src/context/JobContext.tsx", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/App.tsx", "target": "file:frontend/src/components/PipelineView.tsx", "type": "imports", "direction": "forward", "weight": 0.7},
    
    # === Frontend: Context ===
    {"source": "file:frontend/src/context/JobContext.tsx", "target": "file:frontend/src/context/reducer.ts", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/context/JobContext.tsx", "target": "file:frontend/src/api.ts", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/context/JobContext.tsx", "target": "function:frontend/src/context/JobContext.tsx:JobProvider", "type": "contains", "direction": "forward", "weight": 1.0},
    {"source": "file:frontend/src/context/JobContext.tsx", "target": "function:frontend/src/context/JobContext.tsx:useJobs", "type": "contains", "direction": "forward", "weight": 1.0},
    {"source": "file:frontend/src/context/JobContext.tsx", "target": "function:frontend/src/context/JobContext.tsx:JobProvider", "type": "exports", "direction": "forward", "weight": 0.8},
    {"source": "file:frontend/src/context/JobContext.tsx", "target": "function:frontend/src/context/JobContext.tsx:useJobs", "type": "exports", "direction": "forward", "weight": 0.8},
    {"source": "function:frontend/src/context/JobContext.tsx:JobProvider", "target": "function:frontend/src/context/reducer.ts:reducer", "type": "calls", "direction": "forward", "weight": 0.8},
    
    {"source": "file:frontend/src/context/reducer.ts", "target": "file:frontend/src/api.ts", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/context/reducer.ts", "target": "function:frontend/src/context/reducer.ts:reducer", "type": "contains", "direction": "forward", "weight": 1.0},
    {"source": "file:frontend/src/context/reducer.ts", "target": "function:frontend/src/context/reducer.ts:reducer", "type": "exports", "direction": "forward", "weight": 0.8},
    
    # === Frontend: PipelineView ===
    {"source": "file:frontend/src/components/PipelineView.tsx", "target": "file:frontend/src/context/JobContext.tsx", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/PipelineView.tsx", "target": "file:frontend/src/api.ts", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/PipelineView.tsx", "target": "file:frontend/src/components/StagePanel.tsx", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/PipelineView.tsx", "target": "file:frontend/src/components/StatusBar.tsx", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/PipelineView.tsx", "target": "file:frontend/src/components/Sidebar.tsx", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/PipelineView.tsx", "target": "file:frontend/src/components/stages/UploadStage.tsx", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/PipelineView.tsx", "target": "file:frontend/src/components/stages/ChapterStage.tsx", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/PipelineView.tsx", "target": "file:frontend/src/components/stages/CharacterStage.tsx", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/PipelineView.tsx", "target": "file:frontend/src/components/stages/SceneStage.tsx", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/PipelineView.tsx", "target": "file:frontend/src/components/stages/EpisodeStage.tsx", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/PipelineView.tsx", "target": "file:frontend/src/components/stages/ScriptStage.tsx", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/PipelineView.tsx", "target": "file:frontend/src/components/PipelineView.module.css", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/PipelineView.tsx", "target": "function:frontend/src/components/PipelineView.tsx:PipelineView", "type": "contains", "direction": "forward", "weight": 1.0},
    {"source": "file:frontend/src/components/PipelineView.tsx", "target": "function:frontend/src/components/PipelineView.tsx:PipelineView", "type": "exports", "direction": "forward", "weight": 0.8},
    
    # === Frontend: Sidebar ===
    {"source": "file:frontend/src/components/Sidebar.tsx", "target": "file:frontend/src/context/JobContext.tsx", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/Sidebar.tsx", "target": "file:frontend/src/components/Sidebar.module.css", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/Sidebar.tsx", "target": "function:frontend/src/components/Sidebar.tsx:Sidebar", "type": "contains", "direction": "forward", "weight": 1.0},
    {"source": "file:frontend/src/components/Sidebar.tsx", "target": "function:frontend/src/components/Sidebar.tsx:Sidebar", "type": "exports", "direction": "forward", "weight": 0.8},
    
    # === Frontend: StagePanel ===
    {"source": "file:frontend/src/components/StagePanel.tsx", "target": "file:frontend/src/api.ts", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/StagePanel.tsx", "target": "file:frontend/src/components/StagePanel.module.css", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/StagePanel.tsx", "target": "function:frontend/src/components/StagePanel.tsx:StagePanel", "type": "contains", "direction": "forward", "weight": 1.0},
    {"source": "file:frontend/src/components/StagePanel.tsx", "target": "function:frontend/src/components/StagePanel.tsx:StagePanel", "type": "exports", "direction": "forward", "weight": 0.8},
    
    # === Frontend: StatusBar ===
    {"source": "file:frontend/src/components/StatusBar.tsx", "target": "file:frontend/src/context/JobContext.tsx", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/StatusBar.tsx", "target": "file:frontend/src/components/StatusBar.module.css", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/StatusBar.tsx", "target": "function:frontend/src/components/StatusBar.tsx:StatusBar", "type": "contains", "direction": "forward", "weight": 1.0},
    {"source": "file:frontend/src/components/StatusBar.tsx", "target": "function:frontend/src/components/StatusBar.tsx:StatusBar", "type": "exports", "direction": "forward", "weight": 0.8},
    
    # === Frontend: UploadStage ===
    {"source": "file:frontend/src/components/stages/UploadStage.tsx", "target": "file:frontend/src/context/JobContext.tsx", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/stages/UploadStage.tsx", "target": "file:frontend/src/components/stages/UploadStage.module.css", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/stages/UploadStage.tsx", "target": "function:frontend/src/components/stages/UploadStage.tsx:UploadStage", "type": "contains", "direction": "forward", "weight": 1.0},
    {"source": "file:frontend/src/components/stages/UploadStage.tsx", "target": "function:frontend/src/components/stages/UploadStage.tsx:UploadStage", "type": "exports", "direction": "forward", "weight": 0.8},
    
    # === Frontend: ChapterStage ===
    {"source": "file:frontend/src/components/stages/ChapterStage.tsx", "target": "file:frontend/src/context/JobContext.tsx", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/stages/ChapterStage.tsx", "target": "file:frontend/src/components/stages/ChapterStage.module.css", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/stages/ChapterStage.tsx", "target": "function:frontend/src/components/stages/ChapterStage.tsx:ChapterStage", "type": "contains", "direction": "forward", "weight": 1.0},
    {"source": "file:frontend/src/components/stages/ChapterStage.tsx", "target": "function:frontend/src/components/stages/ChapterStage.tsx:ChapterStage", "type": "exports", "direction": "forward", "weight": 0.8},
    
    # === Frontend: CharacterStage ===
    {"source": "file:frontend/src/components/stages/CharacterStage.tsx", "target": "file:frontend/src/context/JobContext.tsx", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/stages/CharacterStage.tsx", "target": "file:frontend/src/api.ts", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/stages/CharacterStage.tsx", "target": "file:frontend/src/components/stages/CharacterStage.module.css", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/stages/CharacterStage.tsx", "target": "function:frontend/src/components/stages/CharacterStage.tsx:CharacterStage", "type": "contains", "direction": "forward", "weight": 1.0},
    {"source": "file:frontend/src/components/stages/CharacterStage.tsx", "target": "function:frontend/src/components/stages/CharacterStage.tsx:CharacterStage", "type": "exports", "direction": "forward", "weight": 0.8},
    
    # === Frontend: SceneStage ===
    {"source": "file:frontend/src/components/stages/SceneStage.tsx", "target": "file:frontend/src/context/JobContext.tsx", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/stages/SceneStage.tsx", "target": "file:frontend/src/api.ts", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/stages/SceneStage.tsx", "target": "file:frontend/src/components/stages/SceneStage.module.css", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/stages/SceneStage.tsx", "target": "function:frontend/src/components/stages/SceneStage.tsx:SceneStage", "type": "contains", "direction": "forward", "weight": 1.0},
    {"source": "file:frontend/src/components/stages/SceneStage.tsx", "target": "function:frontend/src/components/stages/SceneStage.tsx:SceneStage", "type": "exports", "direction": "forward", "weight": 0.8},
    
    # === Frontend: EpisodeStage ===
    {"source": "file:frontend/src/components/stages/EpisodeStage.tsx", "target": "file:frontend/src/context/JobContext.tsx", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/stages/EpisodeStage.tsx", "target": "file:frontend/src/api.ts", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/stages/EpisodeStage.tsx", "target": "file:frontend/src/components/stages/EpisodeStage.module.css", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/stages/EpisodeStage.tsx", "target": "function:frontend/src/components/stages/EpisodeStage.tsx:EpisodeStage", "type": "contains", "direction": "forward", "weight": 1.0},
    {"source": "file:frontend/src/components/stages/EpisodeStage.tsx", "target": "function:frontend/src/components/stages/EpisodeStage.tsx:EpisodeStage", "type": "exports", "direction": "forward", "weight": 0.8},
    
    # === Frontend: ScriptStage ===
    {"source": "file:frontend/src/components/stages/ScriptStage.tsx", "target": "file:frontend/src/context/JobContext.tsx", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/stages/ScriptStage.tsx", "target": "file:frontend/src/api.ts", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/stages/ScriptStage.tsx", "target": "file:frontend/src/components/stages/ScriptStage.module.css", "type": "imports", "direction": "forward", "weight": 0.7},
    {"source": "file:frontend/src/components/stages/ScriptStage.tsx", "target": "function:frontend/src/components/stages/ScriptStage.tsx:ScriptStage", "type": "contains", "direction": "forward", "weight": 1.0},
    {"source": "file:frontend/src/components/stages/ScriptStage.tsx", "target": "function:frontend/src/components/stages/ScriptStage.tsx:ScriptStage", "type": "exports", "direction": "forward", "weight": 0.8},
    
    # === Frontend: Context dep graph ===
    {"source": "file:frontend/src/context/JobContext.tsx", "target": "file:frontend/src/context/reducer.ts", "type": "depends_on", "direction": "forward", "weight": 0.6},
    {"source": "file:frontend/src/components/PipelineView.tsx", "target": "file:frontend/src/context/JobContext.tsx", "type": "depends_on", "direction": "forward", "weight": 0.6},
    {"source": "file:frontend/src/components/Sidebar.tsx", "target": "file:frontend/src/context/JobContext.tsx", "type": "depends_on", "direction": "forward", "weight": 0.6},
    {"source": "file:frontend/src/components/StatusBar.tsx", "target": "file:frontend/src/context/JobContext.tsx", "type": "depends_on", "direction": "forward", "weight": 0.6},
    
    # === Docs ===
    {"source": "document:docs/plans/2026-06-07-pipeline-rebuild.md", "target": "file:frontend/src/components/PipelineView.tsx", "type": "documents", "direction": "forward", "weight": 0.5},
    {"source": "document:docs/plans/2026-06-07-pipeline-rebuild.md", "target": "file:frontend/src/context/JobContext.tsx", "type": "documents", "direction": "forward", "weight": 0.5},
    {"source": "document:docs/superpowers/specs/2026-06-07-pipeline-rebuild-design.md", "target": "file:frontend/src/components/PipelineView.tsx", "type": "documents", "direction": "forward", "weight": 0.5},
    {"source": "document:docs/superpowers/specs/2026-06-07-pipeline-rebuild-design.md", "target": "file:frontend/src/context/JobContext.tsx", "type": "documents", "direction": "forward", "weight": 0.5},
    
    # === Brainstorm layout-mockup related ===
    {"source": "file:.superpowers/brainstorm/2238-1780817272/content/layout-mockup.html", "target": "file:frontend/src/components/PipelineView.tsx", "type": "related", "direction": "forward", "weight": 0.5},
    {"source": "file:.superpowers/brainstorm/2238-1780817272/content/approaches.html", "target": "file:frontend/src/components/PipelineView.tsx", "type": "related", "direction": "forward", "weight": 0.5},
    
    # === Updated backend: jobs.py new endpoints ===
    {"source": "function:backend/routes/jobs.py:list_all_jobs", "target": "function:backend/pipeline/orchestrator.py:list_jobs", "type": "calls", "direction": "forward", "weight": 0.8},
    {"source": "function:backend/routes/jobs.py:delete_job_endpoint", "target": "function:backend/pipeline/orchestrator.py:get_job", "type": "calls", "direction": "forward", "weight": 0.8},
    {"source": "function:backend/routes/jobs.py:delete_job_endpoint", "target": "function:backend/pipeline/orchestrator.py:delete_job", "type": "calls", "direction": "forward", "weight": 0.8},
    {"source": "function:backend/routes/jobs.py:get_stages", "target": "function:backend/pipeline/orchestrator.py:get_stage_statuses", "type": "calls", "direction": "forward", "weight": 0.8},
    {"source": "function:backend/routes/jobs.py:get_chapters_endpoint", "target": "function:backend/pipeline/orchestrator.py:get_chapters", "type": "calls", "direction": "forward", "weight": 0.8},
    {"source": "function:backend/routes/jobs.py:retry_job", "target": "function:backend/pipeline/orchestrator.py:retry_pipeline", "type": "calls", "direction": "forward", "weight": 0.8},
    {"source": "function:backend/routes/jobs.py:list_all_jobs", "target": "class:backend/models.py:JobResponse", "type": "calls", "direction": "forward", "weight": 0.8},
    {"source": "function:backend/routes/jobs.py:retry_job", "target": "class:backend/models.py:JobResponse", "type": "calls", "direction": "forward", "weight": 0.8},
]

# Add new edges
kg['edges'].extend(new_edges)
print(f"New edges added: {len(new_edges)}")

# ==============================
# 5. Update orchestrator nodes (line ranges changed)
# ==============================

# Update orchestrator node description and line ranges for changed functions
for node in kg['nodes']:
    if node['id'] == 'file:backend/pipeline/orchestrator.py':
        node['summary'] = "小说到剧本转换管线的核心编排器，基于阶段状态表驱动五阶段流水线（分章/角色/场景/剧集/剧本），支持细粒度阶段追踪、任意阶段重试回退和完整的作业 CRUD 管理。"
        node['tags'] = ["orchestrator", "pipeline", "state-machine", "service", "core", "tested"]
        node['complexity'] = "complex"
        node['languageNotes'] = "新增 stage_status 表实现阶段级状态持久化，retry_pipeline 支持从任意阶段重新运行并级联清理下游数据，管线段落从 391 行扩展至 546 行。"
    
    if node['id'] == 'file:backend/routes/jobs.py':
        node['summary'] = "作业管理 API 路由，提供完整的作业 CRUD 接口（列表查询/创建/状态/删除/继续/重试）、阶段状态查询和章节数据查询。"
        node['complexity'] = "moderate"

# Add new orchestrator functions as nodes (for newly added functions in orchestrator.py)
new_orch_functions = [
    {
        "id": "function:backend/pipeline/orchestrator.py:list_jobs",
        "type": "function",
        "name": "list_jobs",
        "filePath": "backend/pipeline/orchestrator.py",
        "lineRange": [50, 68],
        "summary": "作业列表查询函数，支持按标题/作者模糊搜索和状态筛选，按更新时间降序返回。",
        "tags": ["pipeline", "query", "job", "filtering"],
        "complexity": "simple"
    },
    {
        "id": "function:backend/pipeline/orchestrator.py:delete_job",
        "type": "function",
        "name": "delete_job",
        "filePath": "backend/pipeline/orchestrator.py",
        "lineRange": [71, 74],
        "summary": "删除指定作业及其关联数据。",
        "tags": ["pipeline", "mutation", "job", "delete"],
        "complexity": "simple"
    },
    {
        "id": "function:backend/pipeline/orchestrator.py:init_stage_statuses",
        "type": "function",
        "name": "init_stage_statuses",
        "filePath": "backend/pipeline/orchestrator.py",
        "lineRange": [92, 99],
        "summary": "初始化作业的所有阶段状态记录，为每个阶段（5 个）创建 pending 状态行。",
        "tags": ["pipeline", "stage", "initialization", "internal"],
        "complexity": "simple"
    },
    {
        "id": "function:backend/pipeline/orchestrator.py:get_stage_statuses",
        "type": "function",
        "name": "get_stage_statuses",
        "filePath": "backend/pipeline/orchestrator.py",
        "lineRange": [102, 108],
        "summary": "查询指定作业的所有阶段状态记录。",
        "tags": ["pipeline", "stage", "query", "read"],
        "complexity": "simple"
    },
    {
        "id": "function:backend/pipeline/orchestrator.py:update_stage_status",
        "type": "function",
        "name": "update_stage_status",
        "filePath": "backend/pipeline/orchestrator.py",
        "lineRange": [111, 135],
        "summary": "更新单个阶段的状态，根据运行/完成/失败状态设置不同的时间戳和元数据（started_at/completed_at/output_summary/error_message）。",
        "tags": ["pipeline", "stage", "mutation", "write"],
        "complexity": "simple"
    },
    {
        "id": "function:backend/pipeline/orchestrator.py:_cleanup_downstream",
        "type": "function",
        "name": "_cleanup_downstream",
        "filePath": "backend/pipeline/orchestrator.py",
        "lineRange": [327, 353],
        "summary": "级联清理指定阶段之后的所有下游数据（角色/场景/场景节拍/剧集/剧集场景关联/改编备注），用于重试场景的数据一致性维护。",
        "tags": ["pipeline", "cleanup", "data-integrity", "internal"],
        "complexity": "moderate",
        "languageNotes": "使用阶段序号映射表确定清理边界，按依赖关系逆序删除关联数据（先子表后主表）。"
    },
    {
        "id": "function:backend/pipeline/orchestrator.py:retry_pipeline",
        "type": "function",
        "name": "retry_pipeline",
        "filePath": "backend/pipeline/orchestrator.py",
        "lineRange": [356, 377],
        "summary": "从指定阶段重新运行管线，先清理下游数据，重置受影响阶段为 pending，然后执行目标阶段运行器。",
        "tags": ["pipeline", "retry", "orchestration", "entry-point"],
        "complexity": "moderate"
    },
    {
        "id": "function:backend/pipeline/orchestrator.py:get_chapters",
        "type": "function",
        "name": "get_chapters",
        "filePath": "backend/pipeline/orchestrator.py",
        "lineRange": [382, 388],
        "summary": "查询指定作业的所有章节数据（排除 novel_text 列），按章节编号排序。",
        "tags": ["pipeline", "query", "chapter", "read"],
        "complexity": "simple"
    },
]

# Add existing orchestrator function updates 
for i, node in enumerate(kg['nodes']):
    if node['id'] == 'function:backend/pipeline/orchestrator.py:advance_pipeline':
        kg['nodes'][i]['lineRange'] = [269, 324]
        kg['nodes'][i]['summary'] = "管线推进核心函数，基于状态机模式处理 queued/awaiting_review 两种初始状态，自动调用对应阶段运行器，设置阶段状态并生成输出摘要。"
    if node['id'] == 'function:backend/pipeline/orchestrator.py:get_script':
        kg['nodes'][i]['lineRange'] = [486, 546]

# Add new orchestrator function nodes
kg['nodes'].extend(new_orch_functions)

# Add edges for new orchestrator functions
new_orch_edges = [
    {"source": "file:backend/pipeline/orchestrator.py", "target": "function:backend/pipeline/orchestrator.py:list_jobs", "type": "contains", "direction": "forward", "weight": 1.0},
    {"source": "file:backend/pipeline/orchestrator.py", "target": "function:backend/pipeline/orchestrator.py:delete_job", "type": "contains", "direction": "forward", "weight": 1.0},
    {"source": "file:backend/pipeline/orchestrator.py", "target": "function:backend/pipeline/orchestrator.py:init_stage_statuses", "type": "contains", "direction": "forward", "weight": 1.0},
    {"source": "file:backend/pipeline/orchestrator.py", "target": "function:backend/pipeline/orchestrator.py:get_stage_statuses", "type": "contains", "direction": "forward", "weight": 1.0},
    {"source": "file:backend/pipeline/orchestrator.py", "target": "function:backend/pipeline/orchestrator.py:update_stage_status", "type": "contains", "direction": "forward", "weight": 1.0},
    {"source": "file:backend/pipeline/orchestrator.py", "target": "function:backend/pipeline/orchestrator.py:_cleanup_downstream", "type": "contains", "direction": "forward", "weight": 1.0},
    {"source": "file:backend/pipeline/orchestrator.py", "target": "function:backend/pipeline/orchestrator.py:retry_pipeline", "type": "contains", "direction": "forward", "weight": 1.0},
    {"source": "file:backend/pipeline/orchestrator.py", "target": "function:backend/pipeline/orchestrator.py:get_chapters", "type": "contains", "direction": "forward", "weight": 1.0},
    {"source": "file:backend/pipeline/orchestrator.py", "target": "function:backend/pipeline/orchestrator.py:list_jobs", "type": "exports", "direction": "forward", "weight": 0.8},
    {"source": "file:backend/pipeline/orchestrator.py", "target": "function:backend/pipeline/orchestrator.py:delete_job", "type": "exports", "direction": "forward", "weight": 0.8},
    {"source": "file:backend/pipeline/orchestrator.py", "target": "function:backend/pipeline/orchestrator.py:init_stage_statuses", "type": "exports", "direction": "forward", "weight": 0.8},
    {"source": "file:backend/pipeline/orchestrator.py", "target": "function:backend/pipeline/orchestrator.py:get_stage_statuses", "type": "exports", "direction": "forward", "weight": 0.8},
    {"source": "file:backend/pipeline/orchestrator.py", "target": "function:backend/pipeline/orchestrator.py:update_stage_status", "type": "exports", "direction": "forward", "weight": 0.8},
    {"source": "file:backend/pipeline/orchestrator.py", "target": "function:backend/pipeline/orchestrator.py:_cleanup_downstream", "type": "exports", "direction": "forward", "weight": 0.8},
    {"source": "file:backend/pipeline/orchestrator.py", "target": "function:backend/pipeline/orchestrator.py:retry_pipeline", "type": "exports", "direction": "forward", "weight": 0.8},
    {"source": "file:backend/pipeline/orchestrator.py", "target": "function:backend/pipeline/orchestrator.py:get_chapters", "type": "exports", "direction": "forward", "weight": 0.8},
    # calls
    {"source": "function:backend/pipeline/orchestrator.py:retry_pipeline", "target": "function:backend/pipeline/orchestrator.py:_cleanup_downstream", "type": "calls", "direction": "forward", "weight": 0.8},
    {"source": "function:backend/pipeline/orchestrator.py:retry_pipeline", "target": "function:backend/pipeline/orchestrator.py:update_stage_status", "type": "calls", "direction": "forward", "weight": 0.8},
    {"source": "function:backend/pipeline/orchestrator.py:advance_pipeline", "target": "function:backend/pipeline/orchestrator.py:update_stage_status", "type": "calls", "direction": "forward", "weight": 0.8},
    {"source": "function:backend/pipeline/orchestrator.py:create_job", "target": "function:backend/pipeline/orchestrator.py:init_stage_statuses", "type": "calls", "direction": "forward", "weight": 0.8},
]

kg['edges'].extend(new_orch_edges)
print(f"Orchestrator edges added: {len(new_orch_edges)}")

# Add new jobs.py endpoints nodes
new_jobs_nodes = [
    {
        "id": "function:backend/routes/jobs.py:list_all_jobs",
        "type": "function",
        "name": "list_all_jobs",
        "filePath": "backend/routes/jobs.py",
        "lineRange": [8, 11],
        "summary": "作业列表查询 API 端点，支持按标题/作者搜索和状态筛选，返回 JobResponse 列表。",
        "tags": ["api-handler", "fastapi", "job", "list", "read"],
        "complexity": "simple"
    },
    {
        "id": "function:backend/routes/jobs.py:delete_job_endpoint",
        "type": "function",
        "name": "delete_job_endpoint",
        "filePath": "backend/routes/jobs.py",
        "lineRange": [44, 50],
        "summary": "作业删除 API 端点，先验证作业存在（404），再调用 delete_job 执行删除。",
        "tags": ["api-handler", "fastapi", "job", "delete"],
        "complexity": "simple"
    },
    {
        "id": "function:backend/routes/jobs.py:get_stages",
        "type": "function",
        "name": "get_stages",
        "filePath": "backend/routes/jobs.py",
        "lineRange": [53, 58],
        "summary": "阶段状态查询 API 端点，返回指定作业所有阶段的详细状态列表。",
        "tags": ["api-handler", "fastapi", "stage", "read"],
        "complexity": "simple"
    },
    {
        "id": "function:backend/routes/jobs.py:get_chapters_endpoint",
        "type": "function",
        "name": "get_chapters_endpoint",
        "filePath": "backend/routes/jobs.py",
        "lineRange": [62, 68],
        "summary": "章节数据查询 API 端点，返回指定作业的分章结果。",
        "tags": ["api-handler", "fastapi", "chapter", "read"],
        "complexity": "simple"
    },
    {
        "id": "function:backend/routes/jobs.py:retry_job",
        "type": "function",
        "name": "retry_job",
        "filePath": "backend/routes/jobs.py",
        "lineRange": [71, 81],
        "summary": "管线重试 API 端点，接收 RetryRequest（起始阶段和重跑阶段列表），调用 retry_pipeline 重新执行。",
        "tags": ["api-handler", "fastapi", "job", "retry", "pipeline"],
        "complexity": "simple"
    },
]

kg['nodes'].extend(new_jobs_nodes)

new_jobs_edges = [
    {"source": "file:backend/routes/jobs.py", "target": "function:backend/routes/jobs.py:list_all_jobs", "type": "contains", "direction": "forward", "weight": 1.0},
    {"source": "file:backend/routes/jobs.py", "target": "function:backend/routes/jobs.py:delete_job_endpoint", "type": "contains", "direction": "forward", "weight": 1.0},
    {"source": "file:backend/routes/jobs.py", "target": "function:backend/routes/jobs.py:get_stages", "type": "contains", "direction": "forward", "weight": 1.0},
    {"source": "file:backend/routes/jobs.py", "target": "function:backend/routes/jobs.py:get_chapters_endpoint", "type": "contains", "direction": "forward", "weight": 1.0},
    {"source": "file:backend/routes/jobs.py", "target": "function:backend/routes/jobs.py:retry_job", "type": "contains", "direction": "forward", "weight": 1.0},
    {"source": "file:backend/routes/jobs.py", "target": "function:backend/routes/jobs.py:list_all_jobs", "type": "exports", "direction": "forward", "weight": 0.8},
    {"source": "file:backend/routes/jobs.py", "target": "function:backend/routes/jobs.py:delete_job_endpoint", "type": "exports", "direction": "forward", "weight": 0.8},
    {"source": "file:backend/routes/jobs.py", "target": "function:backend/routes/jobs.py:get_stages", "type": "exports", "direction": "forward", "weight": 0.8},
    {"source": "file:backend/routes/jobs.py", "target": "function:backend/routes/jobs.py:get_chapters_endpoint", "type": "exports", "direction": "forward", "weight": 0.8},
    {"source": "file:backend/routes/jobs.py", "target": "function:backend/routes/jobs.py:retry_job", "type": "exports", "direction": "forward", "weight": 0.8},
]

kg['edges'].extend(new_jobs_edges)
print(f"Jobs edges added: {len(new_jobs_edges)}")

# ==============================
# 6. Update meta
# ==============================
kg['project']['analyzedAt'] = datetime.now(timezone.utc).isoformat()
kg['project']['gitCommitHash'] = '88ad0d2c035a122bf6621ca8d408da7a27063590'
kg['project']['languages'] = scan['languages']
kg['project']['frameworks'] = scan['frameworks']
kg['project']['description'] = scan['description']

# ==============================
# 7. Remove edge for main.tsx - no more react-router-dom
# main.tsx no longer imports react-router-dom, but it still imports App and index.css
# The old edges were already present; the main.tsx still needs edges to App.tsx and index.css
# Those were kept (they are in the original).

print(f"\nFinal node count: {len(kg['nodes'])}")
print(f"Final edge count: {len(kg['edges'])}")

# ==============================
# 8. Write updated knowledge graph
# ==============================
with open('.understand-anything/knowledge-graph.json', 'w', encoding='utf-8') as f:
    json.dump(kg, f, ensure_ascii=False, indent=2)

print("\nKnowledge graph updated successfully!")
