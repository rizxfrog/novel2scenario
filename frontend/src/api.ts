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

export const api = {
  createJob: (novel_text: string, title?: string) =>
    request<Job>('/jobs', {
      method: 'POST',
      body: JSON.stringify({ novel_text, title }),
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
};
