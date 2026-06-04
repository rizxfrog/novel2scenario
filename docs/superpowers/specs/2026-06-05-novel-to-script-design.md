# AI 小说转剧本工具 — 设计文档

> Date: 2026-06-05  
> Status: Approved

## Overview

一个 AI 辅助剧本创作工具，能将 3 个章节以上的小说文本自动转换为结构化剧本（YAML 格式），让作者快速获得可编辑、可进一步打磨的剧本初稿。

### Key Decisions

| Decision | Choice |
|----------|--------|
| LLM Provider | OpenAI GPT-4o |
| Script Type | TV Drama (多集) |
| Interaction | Interactive + editable (分阶段审核编辑) |
| Input Scale | 50K-200K words |
| Backend | FastAPI + Python 3.14 |
| Frontend | React SPA (Vite) |
| Database | SQLite |
| Auth | None (单用户工具) |

---

## 1. High-Level Architecture

系统分为三层，通过明确的接口通信：

```
┌─────────────────────────────────────────────────────┐
│                  React Frontend (SPA)                │
│  Upload │ Pipeline Dashboard │ Editors │ YAML Preview │
└─────────────────────┬───────────────────────────────┘
                      │ REST API (JSON)
┌─────────────────────▼───────────────────────────────┐
│              FastAPI Backend (Python 3.14)           │
│                                                      │
│  Pipeline Orchestrator ── Agent Engine (OpenAI)      │
│       │                    │          │              │
│  ┌────▼────┐  ┌──────▼──┐  ┌────▼─────┐            │
│  │Chapter  │  │Character│  │Scene     │ ...          │
│  │Splitter │  │Extractor│  │Analyzer  │              │
│  └─────────┘  └─────────┘  └──────────┘              │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│                 SQLite Database                       │
│  jobs │ chapters │ characters │ scenes │ episodes    │
└─────────────────────────────────────────────────────┘
```

**Key Design Principles:**
- **FastAPI** — async native, Pydantic validation, auto-generated OpenAPI docs
- **React SPA** (no Next.js) — purely client-side, talks to FastAPI via fetch, keeps it simple
- **SQLite** — file-based, zero setup, sufficient for single-user desktop tool
- **Pipeline Orchestrator** — state machine managing job lifecycle and agent dispatch
- **Agent Engine** — thin wrapper around OpenAI API, handles prompt templates, retries, and parallel dispatch

---

## 2. Pipeline & Agent Engine

### 2.1 Pipeline Stages

The pipeline runs through 5 sequential stages. Within each stage, agents work on chapters in parallel:

```
STAGE 1: CHAPTER SPLITTING (sequential)
   Novel text → Split by delimiter/LLM → N chapters stored in DB

STAGE 2: CHARACTER EXTRACTION (parallel)
   Chapter 1 ──→ Character Extractor ──→ characters₁
   Chapter 2 ──→ Character Extractor ──→ characters₂   } all run in parallel
   Chapter N ──→ Character Extractor ──→ charactersₙ
   ↓
   Merge + deduplicate → unified character list → USER REVIEW GATE

STAGE 3: SCENE ANALYSIS (parallel)
   Chapter 1 ──→ Scene Analyzer ──→ scenes₁
   Chapter 2 ──→ Scene Analyzer ──→ scenes₂             } all run in parallel
   Chapter N ──→ Scene Analyzer ──→ scenesₙ
   ↓
   Merge scenes → USER REVIEW GATE

STAGE 4: EPISODE STRUCTURING (sequential)
   All scenes → Episode Structurer → episode breakdown → USER REVIEW GATE

STAGE 5: SCRIPT ASSEMBLY (sequential)
   Characters + Scenes + Episodes → Script Assembler → YAML output
```

### 2.2 Agent Engine API

```python
async def run_agent(prompt_template: str, context: dict, model: str = "gpt-4o") -> dict:
    """Single OpenAI call, returns parsed Pydantic model."""
    pass

async def run_parallel(agent_func: Callable, items: list, concurrency: int = 5) -> list:
    """Dispatches multiple agents concurrently with semaphore control."""
    pass
```

- Each agent returns structured JSON (parsed via Pydantic), not free text
- Retries: max 3 attempts on failure
- Streaming: optional SSE for progress updates to frontend

### 2.3 Pipeline Orchestrator

- Database-driven state machine: `queued → running_stage → awaiting_review → ... → completed`
- After each review gate, user must explicitly "continue" to advance
- If user edits data (e.g., removes a character), only downstream stages are recalculated

---

## 3. YAML Script Schema

```yaml
# novel2scenario output schema v1
meta:
  title: "小说标题"
  author: "原作者"
  total_episodes: 24
  total_chapters_in_novel: 42
  generated_at: "2026-06-05T12:00:00Z"

dramatis_personae:
  - name: "主角名"
    role: protagonist           # protagonist | antagonist | supporting | minor
    traits: ["勇敢", "聪明"]     # 3-5 key personality traits
    description: "外貌与性格描述"
    first_appearance: 1         # chapter where introduced
    relationships:
      - with: "另一角色名"
        relation: "朋友"
        dynamic: "互相扶持"

episodes:
  - number: 1
    title: "第一集标题"
    summary: "本集概要和主线情节"
    novel_chapters: [1, 2]      # chapters this episode adapts from
    scenes:
      - id: "S01E01-01"         # Season01Episode01-Scene01
        heading: "INT. 宫殿大厅 - 日"
        setting:
          location: "宫殿大厅"
          time_of_day: "日"
          description: "金碧辉煌的大殿，龙椅居中"
        characters_present: ["主角名", "配角名"]
        summary: "主角向国王请战，获得御赐宝剑"
        beats:
          - type: dialogue
            speaker: "主角名"
            line: "陛下，臣愿领兵出征！"
          - type: action
            description: "主角单膝跪地，双手抱拳"
          - type: dialogue
            speaker: "配角名"
            line: "这是否太鲁莽了？"
          - type: direction
            description: "镜头从高处俯拍，展现大殿全貌"

adaptation_notes:
  - type: restructured
    description: "第5-7章的内容合并为第3集，以加强节奏"
  - type: omitted
    description: "省略了第12章中关于次要角色的支线"
  - type: original
    description: "第3集的宴会场景为编剧原创，用于建立人物关系"
```

### 3.1 Schema Design Rationale

1. **Flat hierarchy (episodes → scenes → beats)** — mirrors industry-standard screenplay structure; editors and scriptwriters expect this format.
2. **`beats` array with typed entries** — dialogue, action, and direction are fundamentally different types of content. Mixing them into a text blob loses editability. Typed beats allow per-type rendering and editing.
3. **`dramatis_personae` up front** — standard script convention; gives immediate overview of all characters before diving into scenes.
4. **`adaptation_notes` at end** — provides transparency. Authors can see what the AI changed, added, or removed from the source novel, enabling informed revision decisions.
5. **Scene IDs (`SxxExx-scene`)** — familiar to editors, sortable, globally unique. Matches standard TV episode numbering.
6. **`novel_chapters` per episode** — traces script back to source chapters, enabling authors to verify fidelity.
7. **`relationships` on characters** — captures character dynamics that may not be obvious from dialogue alone, helping with scene planning and consistency.

---

## 4. Frontend Design

### 4.1 Page Flow

```
Upload → Character Editor → Scene Editor → Episode Planner → Script Preview
          ^ review gate       ^ review gate    ^ review gate      ^ final output
```

### 4.2 Component Tree

```
App
├── UploadPage          ← text area + delimiter config + submit button
│   States: empty, submitted, error
├── PipelinePage        ← wraps all editing pages, shows progress bar
│   ├── ProgressBar     ← 5-stage indicator with check/cross/loading
│   ├── CharacterTable  ← sortable, filterable, "merge duplicates" action
│   │   States: loading, loaded, empty, error, edited (unsaved)
│   ├── ScenePanel      ← collapsible chapter groups, inline beat editor
│   │   States: loading, loaded, empty, error, edited (unsaved)
│   ├── EpisodePlanner  ← two-column: scene pool + episode drop zones
│   │   States: loading, loaded, empty, error, edited (unsaved)
│   └── ScriptPreview   ← read-only YAML with copy/download
│       States: loading, loaded, error
└── NotFound
```

### 4.3 API Endpoints (Frontend Perspective)

```
POST   /api/jobs                         ← create job, upload novel text
GET    /api/jobs/{id}                    ← get job status + pipeline stage
POST   /api/jobs/{id}/continue           ← advance to next stage

GET    /api/jobs/{id}/characters         ← get character list
PUT    /api/jobs/{id}/characters         ← save edited characters

GET    /api/jobs/{id}/scenes             ← get scene list
PUT    /api/jobs/{id}/scenes             ← save edited scenes

GET    /api/jobs/{id}/episodes           ← get episodes with scene mapping
PUT    /api/jobs/{id}/episodes           ← save episode assignments

GET    /api/jobs/{id}/script             ← get final YAML
```

### 4.4 Tech Choices

- **Vite + React** — fast dev, no SSR needed
- **React Router** — client-side routing
- **Fetch API** — no extra library overhead
- **CSS Modules** — scoped styles without framework
- **No state library** — `useState`/`useReducer` sufficient for single-user tool

---

## 5. Database Schema

```sql
-- Jobs track overall conversion progress
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT NOT NULL DEFAULT 'queued',  -- queued|running|awaiting_review|completed|failed
    pipeline_stage TEXT NOT NULL DEFAULT 'chapter_splitting',
    novel_text TEXT NOT NULL,
    title TEXT,
    author TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    number INTEGER NOT NULL,
    title TEXT,
    content TEXT NOT NULL
);

CREATE TABLE characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    name TEXT NOT NULL,
    role TEXT,  -- protagonist|antagonist|supporting|minor
    traits TEXT,  -- JSON array
    description TEXT,
    first_appearance INTEGER  -- chapter number
);

CREATE TABLE character_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL REFERENCES characters(id),
    related_id INTEGER NOT NULL REFERENCES characters(id),
    relation TEXT,
    dynamic TEXT
);

CREATE TABLE scenes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    chapter_id INTEGER NOT NULL REFERENCES chapters(id),
    number INTEGER NOT NULL,
    heading TEXT,
    setting_json TEXT,  -- JSON: {location, time_of_day, description}
    summary TEXT,
    characters_present TEXT  -- JSON array of names
);

CREATE TABLE scene_beats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scene_id INTEGER NOT NULL REFERENCES scenes(id),
    number INTEGER NOT NULL,  -- order within scene
    type TEXT NOT NULL,  -- dialogue|action|direction
    speaker TEXT,  -- for dialogue
    line TEXT,     -- for dialogue
    description TEXT  -- for action/direction
);

CREATE TABLE episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    number INTEGER NOT NULL,
    title TEXT,
    summary TEXT,
    novel_chapters TEXT  -- JSON array of chapter numbers
);

CREATE TABLE episode_scenes (
    episode_id INTEGER NOT NULL REFERENCES episodes(id),
    scene_id INTEGER NOT NULL REFERENCES scenes(id),
    scene_order INTEGER NOT NULL,
    PRIMARY KEY (episode_id, scene_id)
);

CREATE TABLE adaptation_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    type TEXT,  -- restructured|omitted|original
    description TEXT
);
```

---

## 6. Project Structure

```
novel2scenario/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── models.py            # Pydantic + SQLAlchemy models
│   ├── database.py          # SQLite connection + init
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── orchestrator.py  # Pipeline state machine
│   │   ├── splitter.py      # Chapter splitting
│   │   ├── characters.py    # Character extraction (parallel)
│   │   ├── scenes.py        # Scene analysis (parallel)
│   │   ├── episodes.py      # Episode structuring
│   │   └── assembler.py     # Final script assembly
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── engine.py        # Agent dispatch + OpenAI calls
│   │   └── prompts.py       # Prompt templates
│   └── routes/
│       ├── __init__.py
│       ├── jobs.py          # CRUD for jobs
│       ├── characters.py    # CRUD for characters
│       ├── scenes.py        # CRUD for scenes
│       └── episodes.py      # CRUD for episodes
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── pages/
│   │   │   ├── UploadPage.tsx
│   │   │   ├── CharacterEditor.tsx
│   │   │   ├── SceneEditor.tsx
│   │   │   ├── EpisodePlanner.tsx
│   │   │   └── ScriptPreview.tsx
│   │   ├── components/
│   │   │   ├── ProgressBar.tsx
│   │   │   ├── BeatEditor.tsx
│   │   │   └── Layout.tsx
│   │   └── api.ts           # fetch wrappers
│   └── ...
├── doc/
│   └── script-yaml-schema.md # YAML schema documentation (user-facing)
├── pyproject.toml
└── README.md
```

---

## 7. Error Handling Strategy

**Backend:**
- OpenAI API failures: retry 3x with exponential backoff, then mark stage as failed
- Invalid user edits: validate via Pydantic before saving, return 422 with details
- Pipeline stage failures: mark stage as `failed`, allow user to retry from that stage
- All errors logged with structured info for debugging

**Frontend:**
- API failures: show error banner with retry button, preserve local edits
- Network timeouts: show spinner indefinitely with cancel option
- Invalid data: highlight fields with validation errors inline
- Graceful degradation: if a stage fails, previous stages' data remains editable

---

## 8. Testing Strategy

- **Backend unit tests:** pytest for pipeline stages, agent engine mocks
- **Backend integration tests:** FastAPI TestClient for API routes
- **Frontend:** manual testing (single-user tool, minimal logic in frontend)
- **Smoke test:** end-to-end with a 3-chapter sample novel

---

## 9. Out of Scope

- User authentication / accounts
- Multiple concurrent users
- Real-time collaborative editing
- Export formats beyond YAML (PDF, FDX, etc.)
- Novel upload via file (paste text only, initially)
- Voice/audio input
- Translation features

---

## Change Log

| Date | Change |
|------|--------|
| 2026-06-05 | Initial design document |
