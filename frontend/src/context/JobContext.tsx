import React, { createContext, useContext, useReducer, useCallback, useEffect, useRef } from 'react';
import type { ReactNode } from 'react';
import { reducer, initialState, type State, type Action } from './reducer';
import { api, type Job, type StageStatus } from '../api';

interface JobContextValue {
  state: State;
  dispatch: React.Dispatch<Action>;
  loadJobs: (search?: string, status?: string) => Promise<void>;
  removeJob: (jobId: number) => Promise<void>;
  selectJob: (jobId: number) => Promise<void>;
  createNewJob: (novelText: string, title?: string, author?: string) => Promise<Job>;
  continuePipeline: (jobId: number, rerunStages?: string[]) => Promise<Job>;
  retryFromStage: (jobId: number, fromStage: string, rerunStages: string[]) => Promise<Job>;
  loadStageData: (jobId: number, stage: string) => Promise<void>;
}

const JobContext = createContext<JobContextValue | null>(null);

const STAGE_DATA_LOADERS: Record<string, (jobId: number) => Promise<any>> = {
  chapter_splitting: () => Promise.resolve(null),
  character_extraction: (jobId: number) => api.getCharacters(jobId),
  scene_analysis: (jobId: number) => api.getScenes(jobId),
  episode_structuring: (jobId: number) => api.getEpisodes(jobId),
  script_assembly: (jobId: number) => api.getScript(jobId),
};

export function JobProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Auto-poll stages when a stage is running
  useEffect(() => {
    if (state.stages.some(s => s.status === 'running')) {
      pollingRef.current = setInterval(async () => {
        if (state.activeJobId) {
          try {
            const stages = await api.getStages(state.activeJobId);
            dispatch({ type: 'SET_STAGES', stages });
          } catch { /* ignore poll errors */ }
        }
      }, 2000);
    }
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [state.stages, state.activeJobId]);

  const loadJobs = useCallback(async (search?: string, status?: string) => {
    dispatch({ type: 'SET_LOADING', loading: true });
    try {
      const jobs = await api.listJobs(search, status);
      dispatch({ type: 'SET_JOBS', jobs });
    } catch (e: any) {
      dispatch({ type: 'SET_ERROR', error: e.message });
    } finally {
      dispatch({ type: 'SET_LOADING', loading: false });
    }
  }, []);

  const removeJob = useCallback(async (jobId: number) => {
    try {
      await api.deleteJob(jobId);
      dispatch({ type: 'REMOVE_JOB', jobId });
    } catch (e: any) {
      dispatch({ type: 'SET_ERROR', error: e.message });
    }
  }, []);

  const selectJob = useCallback(async (jobId: number) => {
    dispatch({ type: 'SET_ACTIVE_JOB', jobId: jobId });
    dispatch({ type: 'SET_STAGES', stages: [] });
    dispatch({ type: 'SET_STAGE_DATA', stage: '__reset__', data: {} });
    try {
      const stages = await api.getStages(jobId);
      dispatch({ type: 'SET_STAGES', stages });
    } catch (e: any) {
      dispatch({ type: 'SET_ERROR', error: e.message });
    }
  }, []);

  const createNewJob = useCallback(async (novelText: string, title?: string, author?: string) => {
    dispatch({ type: 'SET_LOADING', loading: true });
    try {
      const job = await api.createJob(novelText, title, author);
      dispatch({ type: 'ADD_JOB', job });
      dispatch({ type: 'SET_ACTIVE_JOB', jobId: job.id });
      // Auto-start the pipeline: run chapter_splitting
      await api.continueJob(job.id);
      const stages = await api.getStages(job.id);
      dispatch({ type: 'SET_STAGES', stages });
      return job;
    } catch (e: any) {
      dispatch({ type: 'SET_ERROR', error: e.message });
      throw e;
    } finally {
      dispatch({ type: 'SET_LOADING', loading: false });
    }
  }, []);

  const continuePipeline = useCallback(async (jobId: number, rerunStages?: string[]) => {
    dispatch({ type: 'SET_LOADING', loading: true });
    try {
      const job = await api.continueJob(jobId);
      // After continuing, refresh stages
      const stages = await api.getStages(jobId);
      dispatch({ type: 'SET_STAGES', stages });
      return job;
    } catch (e: any) {
      dispatch({ type: 'SET_ERROR', error: e.message });
      throw e;
    } finally {
      dispatch({ type: 'SET_LOADING', loading: false });
    }
  }, []);

  const retryFromStage = useCallback(async (jobId: number, fromStage: string, rerunStages: string[]) => {
    dispatch({ type: 'SET_LOADING', loading: true });
    try {
      const job = await api.retryJob(jobId, fromStage, rerunStages);
      const stages = await api.getStages(jobId);
      dispatch({ type: 'SET_STAGES', stages });
      return job;
    } catch (e: any) {
      dispatch({ type: 'SET_ERROR', error: e.message });
      throw e;
    } finally {
      dispatch({ type: 'SET_LOADING', loading: false });
    }
  }, []);

  const loadStageData = useCallback(async (jobId: number, stage: string) => {
    const loader = STAGE_DATA_LOADERS[stage];
    if (!loader) return;
    try {
      const data = await loader(jobId);
      dispatch({ type: 'SET_STAGE_DATA', stage, data });
    } catch (e: any) {
      dispatch({ type: 'SET_ERROR', error: e.message });
    }
  }, []);

  return (
    <JobContext.Provider value={{
      state, dispatch, loadJobs, removeJob, selectJob,
      createNewJob, continuePipeline, retryFromStage, loadStageData,
    }}>
      {children}
    </JobContext.Provider>
  );
}

export function useJobs() {
  const ctx = useContext(JobContext);
  if (!ctx) throw new Error('useJobs must be inside JobProvider');
  return ctx;
}
