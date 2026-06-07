# Pipeline Rebuild: Multi-Job, Checkpoint Retry, Pipeline View

**Status:** Draft  
**Date:** 2026-06-07  
**Scope:** Full frontend rebuild + backend API extensions

## Overview

Rebuild the frontend as a single-page PipelineView with sidebar-based multi-job management, checkpoint-aware retry, inline editing, and a persistent status bar. Backend gains checkpoint recovery APIs and stage-level state tracking.

## Goals

1. **Multi-job management** — Sidebar lists all jobs with search/filter; create/delete jobs inline
2. **Pipeline view** — Single scrollable page with 6 stage panels (upload + 5 pipeline stages), each expandable for inline editing
3. **Checkpoint retry** — Failed/completed stages can be retried; user selects which downstream stages to re-run
4. **Status bar** — Fixed bottom bar showing current job, stage, progress message, and error details
5. **Remove old pages** — UploadPage, CharacterEditor, SceneEditor, EpisodePlanner, ScriptPreview replaced by PipelineView

## Architecture

### Frontend: Component Tree

```
App
├── PipelineView (new, replaces all old pages)
│   ├── Sidebar
│   │   ├── SearchBar
│   │   ├── JobList
│   │   │   └── JobItem (highlight active, show status icon)
│   │   └── NewJobButton
│   ├── PipelinePanel (scrollable)
│   │   └── StagePanel × 6
│   │       ├── StageHeader (number, name, status, meta)
│   │       └── StageBody (expandable, varies by stage)
│   │           ├── UploadStage: textarea + title/author inputs
│   │           ├── ChapterStage: chapter list preview
│   │           ├── CharacterStage: card grid + inline edit
│   │           ├── SceneStage: accordion scene list + beat editor
│   │           ├── EpisodeStage: episode list + scene mapping
│   │           └── ScriptStage: JSON preview + download
│   └── StatusBar
│       ├── JobInfo (name, stage number)
│       ├── StageStatus (status badge + message)
│       └── ErrorDetail (collapsible, shown on failure)
├── JobProvider (Context + Reducer, global state)
└── API layer (api.ts, extended)
```

### State Management: JobContext

```typescript
// Central state
interface JobState {
  jobs: Job[];                    // All jobs for sidebar
  activeJobId: number | null;     // Currently selected job
  stages: Record<number, StageInfo>; // Stage states per job
  stageData: Record<string, any>; // Expanded stage data (characters, scenes, etc.)
  loading: boolean;
  error: string | null;
}

// Per-stage info (persisted by backend)
interface StageInfo {
  stage: string;           // "chapter_splitting" | "character_extraction" | ...
  status: StageStatus;     // "pending" | "running" | "awaiting_review" | "completed" | "failed"
  error_message?: string;  // Failure reason
  output_summary?: string; // e.g., "12 章", "8 个角色"
  updated_at?: string;
}

type StageStatus = "pending" | "running" | "awaiting_review" | "completed" | "failed";
```

### Polling Strategy

During `running` state, frontend polls `GET /api/jobs/{id}/stages` every 2 seconds. When status changes to `awaiting_review`, polling stops and the stage panel expands with data.

### Routing

Single route: `/` — renders PipelineView. Job selection is internal state, not URL. No need for react-router except maybe a bare `<BrowserRouter>` wrapper.

## Backend: API Extensions

### New Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/jobs` | List all jobs (supports `?q=search&status=filter`) |
| `DELETE` | `/api/jobs/{job_id}` | Delete a job and all associated data |
| `GET` | `/api/jobs/{job_id}/stages` | Get all stage statuses for a job |
| `POST` | `/api/jobs/{job_id}/retry` | Retry from a specific stage with downstream selection |

### Modified Endpoints

| Method | Endpoint | Change |
|--------|----------|--------|
| `POST` | `/api/jobs/{job_id}/continue` | Accept optional `from_stage` and `rerun_stages[]` body |

### Stage Status Table (new)

```sql
CREATE TABLE IF NOT EXISTS stage_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    stage TEXT NOT NULL,          -- "chapter_splitting", "character_extraction", ...
    status TEXT NOT NULL DEFAULT 'pending',  -- pending|running|awaiting_review|completed|failed
    error_message TEXT,
    output_summary TEXT,
    started_at TEXT,
    completed_at TEXT,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    UNIQUE(job_id, stage)
);
```

### Retry Logic (`POST /api/jobs/{job_id}/retry`)

Request body:
```json
{
  "from_stage": "character_extraction",
  "rerun_stages": ["scene_analysis", "episode_structuring", "script_assembly"]
}
```

1. Set `from_stage` status to `running`
2. Set all stages in `rerun_stages` to `pending`
3. Clear downstream data (delete characters/scenes/episodes/adaptation_notes from that point)
4. Run `from_stage` then advance through `rerun_stages` sequentially
5. After each stage: set `awaiting_review` and return control to frontend

### Data Cleanup on Retry

When retrying from stage N:
- Delete rows from tables that correspond to stage N and all downstream stages
- Reset stage_status entries for affected stages

| Retry from | Delete from tables |
|------------|-------------------|
| chapter_splitting | chapters, characters, scene_beats, scenes, episode_scenes, episodes, adaptation_notes |
| character_extraction | characters, scene_beats, scenes, episode_scenes, episodes, adaptation_notes |
| scene_analysis | scene_beats, scenes, episode_scenes, episodes, adaptation_notes |
| episode_structuring | episode_scenes, episodes, adaptation_notes |
| script_assembly | adaptation_notes |

## Stage Panel Design

Each stage panel has:
- **Collapsed**: Circle indicator + stage name + status badge
- **Expanded**: Full content area + action bar
- **Action bar**: Varies by stage status:

| Status | Actions |
|--------|---------|
| pending | (no actions, disabled) |
| running | (spinner, no actions) |
| awaiting_review | "Edit" + "Save & Continue" button + downstream re-run checkboxes |
| completed | "View" + "Retry from here" button |
| failed | "Retry" + "View Log" + error message |

### Stage-Specific Content

**Upload**: Title/author inputs + textarea. "Start" button creates job and advances to chapter_splitting.

**Chapter Splitting**: Scrollable chapter list preview (title + word count). Expandable to full text view.

**Character Extraction**: Card grid (name, role dropdown, traits chips, description textarea). Add/remove characters. Traits as editable chips.

**Scene Analysis**: Grouped by chapter. Each scene as accordion: heading, setting, characters_present, beats list. Beat editor: type selector (dialogue/action/direction), conditional speaker/line fields, description.

**Episode Structuring**: Episode cards with number, title input, summary textarea, novel_chapters reference, scene mapping (drag/drop or multi-select).

**Script Assembly**: Styled JSON preview with syntax highlighting. "Copy" and "Download YAML" buttons. Adaptation notes section.

## StatusBar

Fixed bottom bar, always visible:

```
[Job: 斗破苍穹]  [阶段: 3/6 角色提取]  |  [等待审核]  等待用户确认角色提取结果

On failure:
[Job: 庆余年]    [阶段: 3/6 角色提取]  |  [失败]  API 超时: 连接 OpenAI 服务失败  [重试] [日志]
```

## Migration Plan

1. Create `PipelineView.tsx` and all child components
2. Set up `JobContext` / `JobProvider`
3. Add new backend endpoints and `stage_status` table
4. Implement retry logic in orchestrator
5. Wire up PipelineView to replace old routes
6. Remove old pages (UploadPage, CharacterEditor, SceneEditor, EpisodePlanner, ScriptPreview)
7. Remove old ProgressBar component
8. Delete old Layout component (replaced by PipelineView's layout)
9. Test end-to-end

## Non-Goals

- Drag-and-drop scene reordering (keep existing order-based approach)
- Real-time collaboration
- User authentication / multi-tenant
- Export formats beyond YAML/JSON
- LLM cost estimation / token counting
``