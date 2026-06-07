const BASE = '/api';

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

export interface Job {
  id: number;
  status: string;
  pipeline_stage: string;
  title?: string;
  author?: string;
  created_at: string;
  updated_at: string;
}

export interface Character {
  id: number;
  job_id: number;
  name: string;
  role?: string;
  traits: string[];
  description?: string;
  first_appearance?: number;
  relationships: { with: string; relation: string; dynamic: string }[];
}

export interface SceneBeat {
  id: number;
  number: number;
  type: string;
  speaker?: string;
  line?: string;
  description?: string;
}

export interface Scene {
  id: number;
  job_id: number;
  chapter_id: number;
  number: number;
  heading?: string;
  setting?: { location: string; time_of_day: string; description: string };
  summary?: string;
  characters_present: string[];
  beats: SceneBeat[];
  chapter_title?: string;
}

export interface Episode {
  id: number;
  job_id: number;
  number: number;
  title?: string;
  summary?: string;
  novel_chapters: number[];
  scene_ids: number[];
}

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

export interface RetryRequest {
  from_stage: string;
  rerun_stages: string[];
}

export interface JobState {
  jobs: Job[];
  activeJobId: number | null;
  stages: StageStatus[];
  stageData: Record<string, any>;
  loading: boolean;
  error: string | null;
}

export const api = {
  createJob: (novel_text: string, title?: string, author?: string) =>
    request<Job>('/jobs', {
      method: 'POST',
      body: JSON.stringify({ novel_text, title, author }),
    }),

  getJob: (id: number) => request<Job>(`/jobs/${id}`),

  continueJob: (id: number) =>
    request<Job>(`/jobs/${id}/continue`, { method: 'POST' }),

  getCharacters: (jobId: number) =>
    request<Character[]>(`/jobs/${jobId}/characters`),

  saveCharacters: (jobId: number, characters: Partial<Character>[]) =>
    request<Character[]>(`/jobs/${jobId}/characters`, {
      method: 'PUT',
      body: JSON.stringify(characters),
    }),

  getScenes: (jobId: number) =>
    request<Scene[]>(`/jobs/${jobId}/scenes`),

  saveScenes: (jobId: number, scenes: Partial<Scene>[]) =>
    request<Scene[]>(`/jobs/${jobId}/scenes`, {
      method: 'PUT',
      body: JSON.stringify(scenes),
    }),

  getEpisodes: (jobId: number) =>
    request<Episode[]>(`/jobs/${jobId}/episodes`),

  saveEpisodes: (jobId: number, episodes: Partial<Episode>[]) =>
    request<Episode[]>(`/jobs/${jobId}/episodes`, {
      method: 'PUT',
      body: JSON.stringify(episodes),
    }),

  getScript: (jobId: number) => request<any>(`/jobs/${jobId}/script`),

  listJobs: (search?: string, status?: string) => {
    const params = new URLSearchParams();
    if (search) params.set('q', search);
    if (status) params.set('status', status);
    return request<Job[]>(`/jobs?${params}`);
  },

  deleteJob: (id: number) =>
    fetch(`${BASE}/jobs/${id}`, { method: 'DELETE' }),

  getStages: (jobId: number) =>
    request<StageStatus[]>(`/jobs/${jobId}/stages`),

  retryJob: (jobId: number, fromStage: string, rerunStages: string[]) =>
    request<Job>('/jobs/' + jobId + '/retry', {
      method: 'POST',
      body: JSON.stringify({ from_stage: fromStage, rerun_stages: rerunStages }),
    }),

  aiAssist: (jobId: number, stage: string, instruction: string, currentData: any) =>
    request<any>(`/jobs/${jobId}/ai-assist`, {
      method: 'POST',
      body: JSON.stringify({ stage, instruction, current_data: currentData }),
    }),
};
