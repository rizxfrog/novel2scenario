# Pipeline Rebuild Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild frontend as single-page PipelineView with multi-job sidebar, checkpoint retry, inline editing, and status bar. Extend backend with stage_status table and retry API.

**Architecture:** Backend gains `stage_status` table for per-stage state tracking and retry endpoints. Frontend replaced with a single `PipelineView` using React Context for state, polling during running stages. Old pages removed.

**Tech Stack:** FastAPI, SQLite, React 18, TypeScript, CSS Modules, fetch-based API client

---

## Phase 1: Backend — Stage Status Foundation

### Task 1: Add stage_status table to database.py

**Files:**
- Modify: `backend/database.py`

**Step 1: Add CREATE TABLE statement**

Add to `init_db()` after the existing table creation statements:

```python
db.execute("""
    CREATE TABLE IF NOT EXISTS stage_status (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        stage TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        error_message TEXT,
        output_summary TEXT,
        started_at TEXT,
        completed_at TEXT,
        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
        UNIQUE(job_id, stage)
    )
""")
```

**Step 2: Run test to verify**

```bash
python -c "from backend.database import init_db; init_db(); print('OK')"
```

**Step 3: Commit**

```bash
git add backend/database.py
git commit -m "feat: add stage_status table for per-stage state tracking"
```

### Task 2: Add stage status helper functions to orchestrator.py

**Files:**
- Modify: `backend/pipeline/orchestrator.py`

**Step 1: Add init_stage_statuses function**

```python
STAGES = [
    "chapter_splitting", "character_extraction", "scene_analysis",
    "episode_structuring", "script_assembly",
]

def init_stage_statuses(job_id: int) -> None:
    db = get_db()
    for stage in STAGES:
        db.execute(
            "INSERT OR IGNORE INTO stage_status (job_id, stage) VALUES (?, ?)",
            (job_id, stage),
        )
    db.commit()
```

**Step 2: Add get_stage_statuses function**

```python
def get_stage_statuses(job_id: int) -> list[dict[str, Any]]:
    db = get_db()
    rows = db.execute(
        "SELECT * FROM stage_status WHERE job_id = ? ORDER BY id",
        (job_id,),
    ).fetchall()
    return [dict(r) for r in rows]
```

**Step 3: Add update_stage_status function**

```python
def update_stage_status(
    job_id: int,
    stage: str,
    status: str,
    error_message: str | None = None,
    output_summary: str | None = None,
) -> None:
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    if status == "running":
        db.execute(
            "UPDATE stage_status SET status = ?, started_at = ?, error_message = NULL WHERE job_id = ? AND stage = ?",
            (status, now, job_id, stage),
        )
    elif status in ("completed", "awaiting_review", "failed"):
        db.execute(
            "UPDATE stage_status SET status = ?, completed_at = ?, output_summary = ?, error_message = ? WHERE job_id = ? AND stage = ?",
            (status, now, output_summary, error_message, job_id, stage),
        )
    else:
        db.execute(
            "UPDATE stage_status SET status = ? WHERE job_id = ? AND stage = ?",
            (status, job_id, stage),
        )
    db.commit()
```

**Step 4: Commit**

```bash
git add backend/pipeline/orchestrator.py
git commit -m "feat: add stage_status helper functions to orchestrator"
```

### Task 3: Wire stage_status updates into pipeline stages

**Files:**
- Modify: `backend/pipeline/orchestrator.py`

**Step 1: Update create_job to init stage statuses**

In `create_job()`, after the INSERT INTO jobs, add:

```python
init_stage_statuses(cursor.lastrowid)
```

**Step 2: Update advance_pipeline — running state**

In the `if job["status"] == "queued":` block, before running chapter_splitting:

```python
update_stage_status(job_id, "chapter_splitting", "running")
```

After success (setting awaiting_review):

```python
update_stage_status(job_id, "chapter_splitting", "awaiting_review")
```

On failure:

```python
update_stage_status(job_id, "chapter_splitting", "failed", error_message=str(e))
```

**Step 3: Update advance_pipeline — awaiting_review state**

In the `if job["status"] == "awaiting_review":` block, for each stage transition:

```python
update_stage_status(job_id, next_stage, "running")
# ... run stage ...
update_stage_status(job_id, next_stage, "awaiting_review" if next_stage != "completed" else "completed")
# on failure:
update_stage_status(job_id, next_stage, "failed", error_message=str(e))
```

**Step 4: Set output_summary for completed stages**

After successful stage completion, set meaningful summaries:
- chapter_splitting: `f"{len(chapters)} 章"`
- character_extraction: `f"{len(characters)} 个角色"`
- Remaining stages can omit or use generic summaries

**Step 5: Commit**

```bash
git add backend/pipeline/orchestrator.py
git commit -m "feat: wire stage_status updates into pipeline stages"
```

---

## Phase 2: Backend — New API Endpoints

### Task 4: Add GET /api/jobs (list all jobs) endpoint

**Files:**
- Modify: `backend/routes/jobs.py`
- Modify: `backend/pipeline/orchestrator.py`

**Step 1: Add list_jobs to orchestrator**

```python
def list_jobs(search: str | None = None, status_filter: str | None = None) -> list[dict]:
    db = get_db()
    query = "SELECT * FROM jobs"
    params: list[Any] = []
    conditions: list[str] = []

    if search:
        conditions.append("(title LIKE ? OR author LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    if status_filter:
        conditions.append("status = ?")
        params.append(status_filter)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY updated_at DESC"

    rows = db.execute(query, tuple(params)).fetchall()
    return [{"id": r["id"], "status": r["status"], "pipeline_stage": r["pipeline_stage"],
             "title": r["title"], "author": r["author"],
             "created_at": r["created_at"], "updated_at": r["updated_at"]} for r in rows]
```

**Step 2: Add route handler**

```python
@router.get("", response_model=list[JobResponse])
async def list_all_jobs(q: str | None = None, status: str | None = None):
    jobs = list_jobs(search=q, status_filter=status)
    return [JobResponse(**j) for j in jobs]
```

**Step 3: Commit**

```bash
git add backend/pipeline/orchestrator.py backend/routes/jobs.py
git commit -m "feat: add GET /api/jobs list endpoint with search and filter"
```

### Task 5: Add DELETE /api/jobs/{job_id} endpoint

**Files:**
- Modify: `backend/routes/jobs.py`
- Modify: `backend/pipeline/orchestrator.py`

**Step 1: Add delete_job to orchestrator**

```python
def delete_job(job_id: int) -> None:
    db = get_db()
    db.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    db.commit()
```

**Step 2: Add route handler**

```python
@router.delete("/{job_id}", status_code=204)
async def delete_job_endpoint(job_id: int):
    try:
        get_job(job_id)  # verify exists
    except ValueError:
        raise HTTPException(status_code=404, detail="Job not found")
    delete_job(job_id)
```

**Step 3: Commit**

```bash
git add backend/pipeline/orchestrator.py backend/routes/jobs.py
git commit -m "feat: add DELETE /api/jobs/{job_id} endpoint"
```

### Task 6: Add GET /api/jobs/{job_id}/stages endpoint

**Files:**
- Modify: `backend/routes/jobs.py`

**Step 1: Add route handler**

```python
@router.get("/{job_id}/stages")
async def get_stages(job_id: int):
    try:
        get_job(job_id)  # verify exists
    except ValueError:
        raise HTTPException(status_code=404, detail="Job not found")
    return get_stage_statuses(job_id)
```

**Step 2: Commit**

```bash
git add backend/routes/jobs.py
git commit -m "feat: add GET /api/jobs/{job_id}/stages endpoint"
```

### Task 7: Add POST /api/jobs/{job_id}/retry endpoint

**Files:**
- Modify: `backend/routes/jobs.py`
- Modify: `backend/pipeline/orchestrator.py`
- Modify: `backend/models.py`

**Step 1: Add RetryRequest model**

```python
class RetryRequest(BaseModel):
    from_stage: str
    rerun_stages: list[str] = []
```

**Step 2: Add data cleanup helper**

```python
def _cleanup_downstream(job_id: int, from_stage: str) -> None:
    db = get_db()
    stage_order = {
        "chapter_splitting": 0, "character_extraction": 1,
        "scene_analysis": 2, "episode_structuring": 3, "script_assembly": 4,
    }
    cutoff = stage_order[from_stage]

    if cutoff <= 1:
        db.execute("DELETE FROM characters WHERE job_id = ?", (job_id,))
    if cutoff <= 2:
        scene_ids = [r[0] for r in db.execute(
            "SELECT id FROM scenes WHERE job_id = ?", (job_id,)
        ).fetchall()]
        for sid in scene_ids:
            db.execute("DELETE FROM scene_beats WHERE scene_id = ?", (sid,))
        db.execute("DELETE FROM scenes WHERE job_id = ?", (job_id,))
    if cutoff <= 3:
        ep_ids = [r[0] for r in db.execute(
            "SELECT id FROM episodes WHERE job_id = ?", (job_id,)
        ).fetchall()]
        for eid in ep_ids:
            db.execute("DELETE FROM episode_scenes WHERE episode_id = ?", (eid,))
        db.execute("DELETE FROM episodes WHERE job_id = ?", (job_id,))
    if cutoff <= 4:
        db.execute("DELETE FROM adaptation_notes WHERE job_id = ?", (job_id,))
    db.commit()
```

**Step 3: Add retry_pipeline function**

```python
async def retry_pipeline(job_id: int, from_stage: str, rerun_stages: list[str]) -> dict[str, Any]:
    _cleanup_downstream(job_id, from_stage)

    # Reset all affected stage statuses
    all_affected = [from_stage] + rerun_stages
    stage_order = {s: i for i, s in enumerate(STAGES)}
    ordered = sorted(all_affected, key=lambda s: stage_order.get(s, 99))

    for stage in ordered:
        update_stage_status(job_id, stage, "pending")

    update_job_status(job_id, "running", from_stage)
    update_stage_status(job_id, from_stage, "running")

    runner = STAGE_RUNNERS.get(from_stage)
    if not runner:
        raise ValueError(f"Unknown stage: {from_stage}")
    await runner(job_id)

    update_stage_status(job_id, from_stage, "awaiting_review")
    update_job_status(job_id, "awaiting_review", from_stage)

    return get_job(job_id)
```

**Step 4: Add route handler**

```python
@router.post("/{job_id}/retry", response_model=JobResponse)
async def retry_job(job_id: int, data: RetryRequest):
    try:
        get_job(job_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Job not found")
    try:
        job = await retry_pipeline(job_id, data.from_stage, data.rerun_stages)
        return JobResponse(**job)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 5: Commit**

```bash
git add backend/models.py backend/pipeline/orchestrator.py backend/routes/jobs.py
git commit -m "feat: add retry endpoint with downstream cleanup"
```

---

## Phase 3: Frontend — Foundation

### Task 8: Set up JobContext with reducer

**Files:**
- Create: `frontend/src/context/JobContext.tsx`
- Create: `frontend/src/context/reducer.ts`

**Step 1: Define types in api.ts (extend existing)**

Add to `frontend/src/api.ts`:

```typescript
export interface StageStatus {
  id: number;
  job_id: number;
  stage: string;
  status: 'pending' | 'running' | 'awaiting_review' | 'completed' | 'failed';
  error_message?: string;
  output_summary?: string;
  started_at?: string;
  completed_at?: string;
}

export interface JobState {
  jobs: Job[];
  activeJobId: number | null;
  stages: StageStatus[];
  stageData: Record<string, any>;
  loading: boolean;
  error: string | null;
}
```

**Step 2: Create API functions in api.ts**

```typescript
export async function fetchJobs(search?: string, status?: string): Promise<Job[]> {
  const params = new URLSearchParams();
  if (search) params.set('q', search);
  if (status) params.set('status', status);
  const res = await fetch(`/api/jobs?${params}`);
  if (!res.ok) throw new Error('Failed to fetch jobs');
  return res.json();
}

export async function deleteJob(jobId: number): Promise<void> {
  const res = await fetch(`/api/jobs/${jobId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete job');
}

export async function fetchStages(jobId: number): Promise<StageStatus[]> {
  const res = await fetch(`/api/jobs/${jobId}/stages`);
  if (!res.ok) throw new Error('Failed to fetch stages');
  return res.json();
}

export async function retryJob(jobId: number, fromStage: string, rerunStages: string[]): Promise<Job> {
  const res = await fetch(`/api/jobs/${jobId}/retry`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ from_stage: fromStage, rerun_stages: rerunStages }),
  });
  if (!res.ok) { const err = await res.json(); throw new Error(err.detail); }
  return res.json();
}
```

**Step 3: Write reducer**

In `frontend/src/context/reducer.ts`:

```typescript
import type { Job, StageStatus } from '../api';

export type Action =
  | { type: 'SET_JOBS'; jobs: Job[] }
  | { type: 'SET_ACTIVE_JOB'; jobId: number | null }
  | { type: 'ADD_JOB'; job: Job }
  | { type: 'REMOVE_JOB'; jobId: number }
  | { type: 'SET_STAGES'; stages: StageStatus[] }
  | { type: 'UPDATE_STAGE'; jobId: number; stage: StageStatus }
  | { type: 'SET_STAGE_DATA'; stage: string; data: any }
  | { type: 'SET_LOADING'; loading: boolean }
  | { type: 'SET_ERROR'; error: string | null };

export interface State {
  jobs: Job[];
  activeJobId: number | null;
  stages: StageStatus[];
  stageData: Record<string, any>;
  loading: boolean;
  error: string | null;
}

export function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'SET_JOBS':
      return { ...state, jobs: action.jobs };
    case 'SET_ACTIVE_JOB':
      return { ...state, activeJobId: action.jobId };
    case 'ADD_JOB':
      return { ...state, jobs: [action.job, ...state.jobs] };
    case 'REMOVE_JOB':
      return {
        ...state,
        jobs: state.jobs.filter(j => j.id !== action.jobId),
        activeJobId: state.activeJobId === action.jobId ? null : state.activeJobId,
      };
    case 'SET_STAGES':
      return { ...state, stages: action.stages };
    case 'UPDATE_STAGE':
      return {
        ...state,
        stages: state.stages.map(s =>
          s.id === action.stage.id ? action.stage : s
        ),
      };
    case 'SET_STAGE_DATA':
      return { ...state, stageData: { ...state.stageData, [action.stage]: action.data } };
    case 'SET_LOADING':
      return { ...state, loading: action.loading };
    case 'SET_ERROR':
      return { ...state, error: action.error };
    default:
      return state;
  }
}

export const initialState: State = {
  jobs: [],
  activeJobId: null,
  stages: [],
  stageData: {},
  loading: false,
  error: null,
};
```

**Step 4: Create context provider**

In `frontend/src/context/JobContext.tsx`:

```typescript
import React, { createContext, useContext, useReducer, useCallback, useEffect, useRef } from 'react';
import type { ReactNode } from 'react';
import { reducer, initialState, type State, type Action } from './reducer';
import { fetchJobs, deleteJob as apiDeleteJob, fetchStages, createJob, advancePipeline, fetchCharacters, fetchScenes, fetchEpisodes, getScript as apiGetScript } from '../api';
import type { Job } from '../api';

interface JobContextValue {
  state: State;
  dispatch: React.Dispatch<Action>;
  loadJobs: (search?: string, status?: string) => Promise<void>;
  removeJob: (jobId: number) => Promise<void>;
  selectJob: (jobId: number) => Promise<void>;
  createNewJob: (novelText: string, title?: string, author?: string) => Promise<Job>;
  continuePipeline: (jobId: number, rerunStages?: string[]) => Promise<void>;
  loadStageData: (jobId: number, stage: string) => Promise<void>;
}

const JobContext = createContext<JobContextValue | null>(null);

export function JobProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ... implementation of all methods

  return (
    <JobContext.Provider value={{ state, dispatch, loadJobs, removeJob, selectJob, createNewJob, continuePipeline, loadStageData }}>
      {children}
    </JobContext.Provider>
  );
}

export function useJobs() {
  const ctx = useContext(JobContext);
  if (!ctx) throw new Error('useJobs must be inside JobProvider');
  return ctx;
}
```

**Step 5: Commit**

```bash
git add frontend/src/api.ts frontend/src/context/reducer.ts frontend/src/context/JobContext.tsx
git commit -m "feat: add JobContext with reducer and API functions"
```

---

## Phase 4: Frontend — Components

### Task 9: Create StatusBar component

**Files:**
- Create: `frontend/src/components/StatusBar.tsx`
- Create: `frontend/src/components/StatusBar.module.css`

**Step 1: Write StatusBar component**

```tsx
import { useJobs } from '../context/JobContext';
import styles from './StatusBar.module.css';

export function StatusBar() {
  const { state } = useJobs();
  const job = state.jobs.find(j => j.id === state.activeJobId);
  if (!job) return null;

  const currentStage = state.stages.find(s => s.status === 'running' || s.status === 'awaiting_review' || s.status === 'failed');
  const stageNames: Record<string, string> = {
    chapter_splitting: '章节拆分',
    character_extraction: '角色提取',
    scene_analysis: '场景分析',
    episode_structuring: '分集组织',
    script_assembly: '剧本生成',
  };

  const completedCount = state.stages.filter(s => s.status === 'completed').length;
  const stageIndex = state.stages.findIndex(s => s.stage === currentStage?.stage) + 1;
  const isFailed = currentStage?.status === 'failed';

  return (
    <div className={`${styles.bar} ${isFailed ? styles.failed : ''}`}>
      <div className={styles.left}>
        <span className={styles.label}>Job:</span>
        <span>{job.title || `Job #${job.id}`}</span>
        {currentStage && (
          <>
            <span className={styles.separator}>|</span>
            <span className={styles.label}>阶段:</span>
            <span>{stageIndex}/5 {stageNames[currentStage.stage]}</span>
          </>
        )}
      </div>
      <div className={styles.right}>
        <span className={`${styles.badge} ${styles[`badge_${currentStage?.status || 'pending'}`]}`}>
          {currentStage?.status === 'running' ? '运行中' :
           currentStage?.status === 'awaiting_review' ? '等待审核' :
           currentStage?.status === 'completed' ? '完成' :
           currentStage?.status === 'failed' ? '失败' : '等待中'}
        </span>
        {isFailed && currentStage?.error_message && (
          <span className={styles.error}>{currentStage.error_message}</span>
        )}
      </div>
    </div>
  );
}
```

**Step 2: Write CSS module**

```css
.bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 36px;
  background: #0f3460;
  border-top: 1px solid #16213e;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  font-size: 12px;
  color: #ccc;
  z-index: 100;
}

.bar.failed {
  border-top-color: #ff6b6b;
}

.left, .right { display: flex; align-items: center; gap: 6px; }
.label { color: #888; }
.separator { color: #333; margin: 0 6px; }

.badge {
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 10px;
  color: white;
}

.badge_running { background: #e94560; }
.badge_awaiting_review { background: #e94560; }
.badge_completed { background: #4ecca3; color: #1a1a2e; }
.badge_failed { background: #ff6b6b; }
.badge_pending { background: #333; }

.error {
  color: #ff6b6b;
  max-width: 400px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
```

**Step 3: Commit**

```bash
git add frontend/src/components/StatusBar.tsx frontend/src/components/StatusBar.module.css
git commit -m "feat: add StatusBar component"
```

### Task 10: Create Sidebar component

**Files:**
- Create: `frontend/src/components/Sidebar.tsx`
- Create: `frontend/src/components/Sidebar.module.css`

**Step 1: Write Sidebar component**

```tsx
import { useState, useEffect } from 'react';
import { useJobs } from '../context/JobContext';
import styles from './Sidebar.module.css';

export function Sidebar() {
  const { state, loadJobs, removeJob, selectJob } = useJobs();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    loadJobs(search || undefined, statusFilter || undefined);
  }, [search, statusFilter]);

  const statusIcons: Record<string, string> = {
    running: '⏳',
    awaiting_review: '!',
    completed: '✓',
    failed: '✕',
    queued: '○',
  };

  return (
    <aside className={styles.sidebar}>
      <div className={styles.header}>Jobs</div>
      <input
        className={styles.search}
        placeholder="搜索..."
        value={search}
        onChange={e => setSearch(e.target.value)}
      />
      <select
        className={styles.filter}
        value={statusFilter}
        onChange={e => setStatusFilter(e.target.value)}
      >
        <option value="">全部状态</option>
        <option value="completed">已完成</option>
        <option value="awaiting_review">等待审核</option>
        <option value="running">运行中</option>
        <option value="failed">失败</option>
        <option value="queued">排队中</option>
      </select>
      <div className={styles.list}>
        {state.jobs.map(job => (
          <div
            key={job.id}
            className={`${styles.item} ${job.id === state.activeJobId ? styles.active : ''}`}
            onClick={() => selectJob(job.id)}
          >
            <div className={styles.jobTitle}>{job.title || `Job #${job.id}`}</div>
            <div className={styles.jobStatus}>
              <span>{statusIcons[job.status] || '○'}</span>
              <span>{job.pipeline_stage || job.status}</span>
            </div>
            <button
              className={styles.deleteBtn}
              onClick={e => {
                e.stopPropagation();
                if (confirm('确定删除此 Job?')) removeJob(job.id);
              }}
            >×</button>
          </div>
        ))}
      </div>
      <button className={styles.newBtn}>+ 新建 Job</button>
    </aside>
  );
}
```

**Step 2: Write CSS module**

```css
.sidebar {
  width: 250px;
  min-width: 250px;
  background: #16213e;
  border-right: 1px solid #0f3460;
  display: flex;
  flex-direction: column;
  padding: 12px;
  height: 100vh;
  box-sizing: border-box;
}

.header {
  color: #eee;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 10px;
}

.search, .filter {
  width: 100%;
  padding: 6px 8px;
  background: #1a1a2e;
  border: 1px solid #0f3460;
  color: #ccc;
  border-radius: 4px;
  font-size: 11px;
  margin-bottom: 8px;
  box-sizing: border-box;
}

.filter { cursor: pointer; }
.filter option { background: #1a1a2e; }

.list {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 10px;
}

.item {
  padding: 8px 10px;
  border-radius: 4px;
  cursor: pointer;
  margin-bottom: 4px;
  display: flex;
  flex-direction: column;
  position: relative;
}

.item:hover { background: #0f3460; }
.item.active {
  background: #0f3460;
  border-left: 3px solid #4ecca3;
}

.jobTitle { color: #eee; font-size: 12px; margin-bottom: 2px; }
.jobStatus { color: #888; font-size: 10px; display: flex; gap: 4px; align-items: center; }

.deleteBtn {
  position: absolute;
  top: 6px;
  right: 8px;
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 16px;
  padding: 0;
  line-height: 1;
}

.deleteBtn:hover { color: #ff6b6b; }

.newBtn {
  width: 100%;
  padding: 6px;
  background: #e94560;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.newBtn:hover { background: #d63850; }
```

**Step 3: Commit**

```bash
git add frontend/src/components/Sidebar.tsx frontend/src/components/Sidebar.module.css
git commit -m "feat: add Sidebar component with search and filter"
```

### Task 11: Create StagePanel framework component

**Files:**
- Create: `frontend/src/components/StagePanel.tsx`
- Create: `frontend/src/components/StagePanel.module.css`

**Step 1: Write StagePanel component**

```tsx
import { type ReactNode, useState } from 'react';
import type { StageStatus } from '../api';
import styles from './StagePanel.module.css';

interface StagePanelProps {
  stage: StageStatus;
  label: string;
  index: number;
  children: ReactNode;
  onRetry?: () => void;
  onContinue?: (rerunStages: string[]) => void;
  canRetryFrom?: boolean;
}

const STAGES = [
  'chapter_splitting', 'character_extraction', 'scene_analysis',
  'episode_structuring', 'script_assembly',
];

export function StagePanel({ stage, label, index, children, onRetry, onContinue, canRetryFrom }: StagePanelProps) {
  const [expanded, setExpanded] = useState(stage.status === 'awaiting_review' || stage.status === 'failed');
  const [rerunStages, setRerunStages] = useState<string[]>([]);
  const isLocked = stage.status === 'pending' && index > 1;

  const statusIcon = () => {
    switch (stage.status) {
      case 'completed': return <span className={styles.icon} style={{ background: '#4ecca3', color: '#1a1a2e' }}>✓</span>;
      case 'running': return <span className={`${styles.icon} ${styles.spinner}`} style={{ borderColor: '#e94560' }} />;
      case 'awaiting_review': return <span className={styles.icon} style={{ background: '#e94560', color: 'white' }}>!</span>;
      case 'failed': return <span className={styles.icon} style={{ background: '#ff6b6b', color: 'white' }}>✕</span>;
      default: return <span className={styles.icon} style={{ background: '#333', color: '#666' }}>{index}</span>;
    }
  };

  return (
    <div className={`${styles.panel} ${isLocked ? styles.locked : ''} ${stage.status === 'failed' ? styles.failedPanel : ''} ${stage.status === 'awaiting_review' ? styles.activePanel : ''}`}>
      <div className={styles.header} onClick={() => !isLocked && setExpanded(!expanded)}>
        {statusIcon()}
        <span className={styles.label}>{label}</span>
        <span className={styles.meta}>
          {stage.status === 'running' && '运行中...'}
          {stage.status === 'awaiting_review' && '等待审核'}
          {stage.status === 'completed' && (stage.output_summary || '完成')}
          {stage.status === 'failed' && '失败'}
          {stage.status === 'pending' && '等待中'}
        </span>
        <span className={styles.expand}>{expanded ? '▼' : '▶'}</span>
      </div>
      {expanded && (
        <div className={styles.body}>
          {stage.status === 'failed' && stage.error_message && (
            <div className={styles.error}>
              {stage.error_message}
              {onRetry && <button className={styles.retryBtn} onClick={onRetry}>重试</button>}
            </div>
          )}
          {children}
          {stage.status === 'awaiting_review' && onContinue && (
            <div className={styles.actions}>
              <div className={styles.checkboxes}>
                {STAGES.slice(index).map(s => (
                  <label key={s} className={styles.checkbox}>
                    <input
                      type="checkbox"
                      checked={rerunStages.includes(s)}
                      onChange={e => {
                        if (e.target.checked) setRerunStages([...rerunStages, s]);
                        else setRerunStages(rerunStages.filter(rs => rs !== s));
                      }}
                    /> {stageName(s)}
                  </label>
                ))}
              </div>
              <button className={styles.continueBtn} onClick={() => onContinue(rerunStages)}>
                保存并继续
              </button>
            </div>
          )}
          {canRetryFrom && stage.status === 'completed' && (
            <div className={styles.actions}>
              <button className={styles.retryFromBtn} onClick={onRetry}>从此重新运行</button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function stageName(s: string): string {
  const map: Record<string, string> = {
    chapter_splitting: '章节拆分',
    character_extraction: '角色提取',
    scene_analysis: '场景分析',
    episode_structuring: '分集组织',
    script_assembly: '剧本生成',
  };
  return map[s] || s;
}
```

**Step 2: Write CSS**

```css
.panel {
  border: 1px solid #0f3460;
  border-radius: 6px;
  background: #1a1a2e;
  overflow: hidden;
  margin-bottom: 8px;
}

.panel.locked { opacity: 0.4; border-color: #222; }
.panel.failedPanel { border-color: #ff6b6b; }
.panel.activePanel { border-color: #e94560; }

.header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 15px;
  cursor: pointer;
  user-select: none;
}

.header:hover { background: rgba(15, 52, 96, 0.3); }

.icon {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  flex-shrink: 0;
}

.spinner {
  border: 2px solid #333;
  border-top-color: transparent;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.label { color: #eee; font-weight: 500; font-size: 13px; }
.meta { margin-left: auto; font-size: 11px; color: #888; }
.expand { color: #555; font-size: 10px; }

.body { padding: 15px; border-top: 1px solid #0f3460; }

.error {
  padding: 8px 12px;
  background: rgba(255, 107, 107, 0.1);
  border-left: 3px solid #ff6b6b;
  color: #ff6b6b;
  font-size: 11px;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.retryBtn {
  padding: 3px 10px;
  background: #ff6b6b;
  color: white;
  border: none;
  border-radius: 3px;
  cursor: pointer;
  font-size: 11px;
  margin-left: auto;
}

.actions {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #0f3460;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.checkboxes { display: flex; gap: 12px; flex-wrap: wrap; }
.checkbox { color: #888; font-size: 11px; cursor: pointer; }
.checkbox input { margin-right: 3px; }

.continueBtn {
  padding: 6px 18px;
  background: #e94560;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.retryFromBtn {
  padding: 6px 18px;
  background: #e94560;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
```

**Step 3: Commit**

```bash
git add frontend/src/components/StagePanel.tsx frontend/src/components/StagePanel.module.css
git commit -m "feat: add StagePanel framework component"
```

### Task 12: Create UploadStage component

**Files:**
- Create: `frontend/src/components/stages/UploadStage.tsx`
- Create: `frontend/src/components/stages/UploadStage.module.css`

**Step 1: Write component (reuse logic from UploadPage)**

```tsx
import { useState } from 'react';
import { useJobs } from '../../context/JobContext';
import styles from './UploadStage.module.css';

export function UploadStage() {
  const { createNewJob } = useJobs();
  const [text, setText] = useState('');
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!text.trim()) return;
    setLoading(true);
    try {
      await createNewJob(text, title || undefined, author || undefined);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <input
        className={styles.input}
        placeholder="小说标题（可选）"
        value={title}
        onChange={e => setTitle(e.target.value)}
      />
      <input
        className={styles.input}
        placeholder="作者（可选）"
        value={author}
        onChange={e => setAuthor(e.target.value)}
      />
      <textarea
        className={styles.textarea}
        placeholder="在此粘贴小说原文..."
        value={text}
        onChange={e => setText(e.target.value)}
        rows={12}
      />
      <button
        className={styles.submit}
        onClick={handleSubmit}
        disabled={!text.trim() || loading}
      >
        {loading ? '正在创建...' : '开始转换'}
      </button>
    </div>
  );
}
```

**Step 2: Write CSS**

```css
.container { display: flex; flex-direction: column; gap: 10px; }

.input {
  padding: 8px 12px;
  background: #0f3460;
  border: 1px solid #16213e;
  color: #eee;
  border-radius: 4px;
  font-size: 13px;
}

.input::placeholder { color: #666; }

.textarea {
  padding: 12px;
  background: #0f3460;
  border: 1px solid #16213e;
  color: #eee;
  border-radius: 4px;
  font-size: 13px;
  resize: vertical;
  font-family: inherit;
  line-height: 1.6;
}

.textarea::placeholder { color: #666; }

.submit {
  padding: 10px;
  background: #e94560;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.submit:disabled { opacity: 0.5; cursor: not-allowed; }
.submit:hover:not(:disabled) { background: #d63850; }
```

**Step 3: Commit**

```bash
git add frontend/src/components/stages/UploadStage.tsx frontend/src/components/stages/UploadStage.module.css
git commit -m "feat: add UploadStage component"
```

### Task 13: Create ChapterStage component

**Files:**
- Create: `frontend/src/components/stages/ChapterStage.tsx`
- Create: `frontend/src/components/stages/ChapterStage.module.css`

**Step 1: Write component**

Minimal preview — shows chapter count and list. Expand individual chapters for full text.

```tsx
import { useEffect, useState } from 'react';
import { useJobs } from '../../context/JobContext';
import styles from './ChapterStage.module.css';

interface Chapter {
  id: number;
  number: number;
  title: string;
  content: string;
}

export function ChapterStage() {
  const { state } = useJobs();
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  useEffect(() => {
    if (state.activeJobId) {
      fetch(`/api/jobs/${state.activeJobId}/chapters`)
        .then(r => r.json())
        .then(setChapters)
        .catch(() => {});
    }
  }, [state.activeJobId]);

  return (
    <div className={styles.container}>
      {chapters.length === 0 && <p className={styles.empty}>暂无章节数据</p>}
      {chapters.map(ch => (
        <div key={ch.id} className={styles.chapter}>
          <div className={styles.header} onClick={() => setExpandedId(expandedId === ch.id ? null : ch.id)}>
            <span className={styles.number}>第{ch.number}章</span>
            <span className={styles.title}>{ch.title || '(无标题)'}</span>
            <span className={styles.wordCount}>{ch.content.length} 字</span>
          </div>
          {expandedId === ch.id && (
            <div className={styles.content}>{ch.content}</div>
          )}
        </div>
      ))}
    </div>
  );
}
```

**Step 2: Write CSS**

```css
.container { display: flex; flex-direction: column; gap: 6px; }
.empty { color: #666; font-size: 12px; text-align: center; padding: 20px; }

.chapter {
  border: 1px solid #0f3460;
  border-radius: 4px;
  overflow: hidden;
}

.header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  cursor: pointer;
  background: #0f3460;
}

.header:hover { background: #16213e; }

.number { color: #e94560; font-size: 12px; font-weight: 500; }
.title { color: #eee; font-size: 12px; flex: 1; }
.wordCount { color: #666; font-size: 11px; }

.content {
  padding: 12px;
  color: #ccc;
  font-size: 12px;
  line-height: 1.8;
  max-height: 300px;
  overflow-y: auto;
  white-space: pre-wrap;
}
```

**Step 3: Commit**

```bash
git add frontend/src/components/stages/ChapterStage.tsx frontend/src/components/stages/ChapterStage.module.css
git commit -m "feat: add ChapterStage component"
```

### Task 14: Create CharacterStage component

**Files:**
- Create: `frontend/src/components/stages/CharacterStage.tsx`
- Create: `frontend/src/components/stages/CharacterStage.module.css`

Reuse edit logic from existing CharacterEditor page, adapt to panel layout with card grid.

### Task 15: Create SceneStage component

**Files:**
- Create: `frontend/src/components/stages/SceneStage.tsx`
- Create: `frontend/src/components/stages/SceneStage.module.css`

Reuse edit logic from existing SceneEditor page, adapt to panel layout with accordion.

### Task 16: Create EpisodeStage component

**Files:**
- Create: `frontend/src/components/stages/EpisodeStage.tsx`
- Create: `frontend/src/components/stages/EpisodeStage.module.css`

Reuse edit logic from existing EpisodePlanner page, adapt to panel layout.

### Task 17: Create ScriptStage component

**Files:**
- Create: `frontend/src/components/stages/ScriptStage.tsx`
- Create: `frontend/src/components/stages/ScriptStage.module.css`

Reuse preview logic from ScriptPreview page.

---

## Phase 5: Frontend — Integration & Cleanup

### Task 18: Create PipelineView main page

**Files:**
- Create: `frontend/src/components/PipelineView.tsx`
- Create: `frontend/src/components/PipelineView.module.css`

**Step 1: Write PipelineView**

```tsx
import { useEffect, useRef, useCallback } from 'react';
import { useJobs } from '../context/JobContext';
import { StagePanel } from './StagePanel';
import { StatusBar } from './StatusBar';
import { Sidebar } from './Sidebar';
import { UploadStage } from './stages/UploadStage';
import { ChapterStage } from './stages/ChapterStage';
import { CharacterStage } from './stages/CharacterStage';
import { SceneStage } from './stages/SceneStage';
import { EpisodeStage } from './stages/EpisodeStage';
import { ScriptStage } from './stages/ScriptStage';
import styles from './PipelineView.module.css';

const stageLabels: Record<string, string> = {
  chapter_splitting: '章节拆分',
  character_extraction: '角色提取',
  scene_analysis: '场景分析',
  episode_structuring: '分集组织',
  script_assembly: '剧本生成',
};

export function PipelineView() {
  const { state, continuePipeline } = useJobs();
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Poll stages while running
  useEffect(() => {
    if (state.stages.some(s => s.status === 'running')) {
      pollingRef.current = setInterval(async () => {
        if (state.activeJobId) {
          const res = await fetch(`/api/jobs/${state.activeJobId}/stages`);
          const stages = await res.json();
          // dispatch update stages
        }
      }, 2000);
    }
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [state.stages, state.activeJobId]);

  const renderStageContent = (stage: string) => {
    switch (stage) {
      case 'chapter_splitting': return <ChapterStage />;
      case 'character_extraction': return <CharacterStage />;
      case 'scene_analysis': return <SceneStage />;
      case 'episode_structuring': return <EpisodeStage />;
      case 'script_assembly': return <ScriptStage />;
      default: return null;
    }
  };

  const handleContinue = (stage: string, rerunStages: string[]) => {
    if (state.activeJobId) continuePipeline(state.activeJobId, rerunStages);
  };

  if (!state.activeJobId) {
    return (
      <div className={styles.layout}>
        <Sidebar />
        <div className={styles.emptyState}>
          <h2>Novel2Scenario</h2>
          <p>选择一个 Job 或新建一个开始</p>
        </div>
        <StatusBar />
      </div>
    );
  }

  return (
    <div className={styles.layout}>
      <Sidebar />
      <main className={styles.main}>
        <div className={styles.title}>Job: {state.jobs.find(j => j.id === state.activeJobId)?.title || '未命名'}</div>
        {state.stages.map((s, i) => (
          <StagePanel
            key={s.stage}
            stage={s}
            label={stageLabels[s.stage]}
            index={i + 1}
            canRetryFrom={s.status !== 'pending'}
            onContinue={(rerun) => handleContinue(s.stage, rerun)}
          >
            {renderStageContent(s.stage)}
          </StagePanel>
        ))}
      </main>
      <StatusBar />
    </div>
  );
}
```

### Task 19: Update App.tsx and main.tsx

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/main.tsx`

Remove old routes, replace with PipelineView wrapped in JobProvider. Remove react-router-dom if no longer needed.

### Task 20: Remove old pages and components

**Files to delete:**
- `frontend/src/pages/UploadPage.tsx`
- `frontend/src/pages/UploadPage.module.css`
- `frontend/src/pages/CharacterEditor.tsx`
- `frontend/src/pages/CharacterEditor.module.css`
- `frontend/src/pages/SceneEditor.tsx`
- `frontend/src/pages/SceneEditor.module.css`
- `frontend/src/pages/EpisodePlanner.tsx`
- `frontend/src/pages/EpisodePlanner.module.css`
- `frontend/src/pages/ScriptPreview.tsx`
- `frontend/src/pages/ScriptPreview.module.css`
- `frontend/src/components/ProgressBar.tsx`
- `frontend/src/components/ProgressBar.module.css`
- `frontend/src/components/Layout.tsx`
- `frontend/src/components/Layout.module.css`

### Task 21: Final integration and testing

- Verify frontend builds: `cd frontend && npm run build`
- Start backend and test full pipeline
- Test multi-job switching
- Test retry from failed stage
- Test retry from completed stage with downstream re-run checkboxes
- Test search and filter in sidebar
- Test delete job from sidebar

---

## Summary of Commits

1. `feat: add stage_status table for per-stage state tracking`
2. `feat: add stage_status helper functions to orchestrator`
3. `feat: wire stage_status updates into pipeline stages`
4. `feat: add GET /api/jobs list endpoint with search and filter`
5. `feat: add DELETE /api/jobs/{job_id} endpoint`
6. `feat: add GET /api/jobs/{job_id}/stages endpoint`
7. `feat: add retry endpoint with downstream cleanup`
8. `feat: add JobContext with reducer and API functions`
9. `feat: add StatusBar component`
10. `feat: add Sidebar component with search and filter`
11. `feat: add StagePanel framework component`
12. `feat: add UploadStage component`
13. `feat: add ChapterStage component`
14. `feat: add CharacterStage component`
15. `feat: add SceneStage component`
16. `feat: add EpisodeStage component`
17. `feat: add ScriptStage component`
18. `feat: create PipelineView main page`
19. `feat: update App.tsx to use PipelineView with JobProvider`
20. `chore: remove old pages and components`
21. `test: end-to-end integration verification`
