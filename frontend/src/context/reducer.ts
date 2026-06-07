import type { Job, StageStatus } from '../api';

export type Action =
  | { type: 'SET_JOBS'; jobs: Job[] }
  | { type: 'SET_ACTIVE_JOB'; jobId: number | null }
  | { type: 'ADD_JOB'; job: Job }
  | { type: 'REMOVE_JOB'; jobId: number }
  | { type: 'SET_STAGES'; stages: StageStatus[] }
  | { type: 'UPDATE_STAGE'; stage: StageStatus }
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
        stages: state.stages.map(s => (s.id === action.stage.id ? action.stage : s)),
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
