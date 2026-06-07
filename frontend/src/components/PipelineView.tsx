import { useEffect, useCallback, useRef } from 'react';
import { useJobs } from '../context/JobContext';
import { api } from '../api';
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

const STAGE_LABELS: Record<string, string> = {
  chapter_splitting: '章节拆分',
  character_extraction: '角色提取',
  scene_analysis: '场景分析',
  episode_structuring: '分集组织',
  script_assembly: '剧本生成',
};

const STAGE_COMPONENTS: Record<string, React.ComponentType<any>> = {
  chapter_splitting: ChapterStage,
  character_extraction: CharacterStage,
  scene_analysis: SceneStage,
  episode_structuring: EpisodeStage,
  script_assembly: ScriptStage,
};

const SAVE_APIS: Record<string, (jobId: number, data: any) => Promise<any>> = {
  character_extraction: (jobId, data) => api.saveCharacters(jobId, data),
  scene_analysis: (jobId, data) => api.saveScenes(jobId, data),
  episode_structuring: (jobId, data) => api.saveEpisodes(jobId, data),
};

export function PipelineView() {
  const { state, continuePipeline, retryFromStage, loadJobs } = useJobs();
  const job = state.jobs.find(j => j.id === state.activeJobId);
  const stageDataRef = useRef<Record<string, any>>({});

  useEffect(() => {
    loadJobs();
  }, []);

  const handleSaveAndContinue = useCallback(async (stageName: string, rerunStages: string[]) => {
    if (!state.activeJobId) return;

    try {
      // Call the appropriate save API
      const saveApi = SAVE_APIS[stageName];
      const currentData = stageDataRef.current[stageName];
      if (saveApi && currentData) {
        await saveApi(state.activeJobId, currentData);
      }
    } catch {
      // Continue even if save fails
    }

    if (rerunStages.length > 0) {
      retryFromStage(state.activeJobId, stageName, rerunStages);
    } else {
      continuePipeline(state.activeJobId);
    }
  }, [state.activeJobId, continuePipeline, retryFromStage]);

  const handleRetry = useCallback((stage: string) => {
    if (state.activeJobId) {
      const afterIdx = state.stages.findIndex(s => s.stage === stage) + 1;
      const downstream = state.stages.slice(afterIdx).map(s => s.stage).filter(s => s !== 'completed');
      retryFromStage(state.activeJobId, stage, downstream);
    }
  }, [state.activeJobId, state.stages, retryFromStage]);

  const renderStageContent = useCallback((stageName: string) => {
    const Component = STAGE_COMPONENTS[stageName];
    if (!Component) return null;
    return (
      <Component
        setData={(data: any) => { stageDataRef.current[stageName] = data; }}
      />
    );
  }, []);

  if (!job) {
    return (
      <div className={styles.layout}>
        <Sidebar />
        <main className={styles.main}>
          <div className={styles.emptyHeader}>
            <h2 className={styles.emptyTitle}>Novel2Scenario</h2>
            <p className={styles.emptySubtitle}>AI 小说转剧本工具</p>
          </div>
          <div className={styles.uploadSection}>
            <UploadStage />
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className={styles.layout}>
      <Sidebar />
      <div className={styles.rightColumn}>
        <main className={styles.main}>
          <div className={styles.title}>
            {job.title || `Job #${job.id}`}
          </div>

          {state.stages.map((s, i) => (
            <StagePanel
              key={s.stage}
              stage={s}
              label={STAGE_LABELS[s.stage] || s.stage}
              index={i + 1}
              canRetryFrom={s.status === 'completed'}
              onRetry={() => handleRetry(s.stage)}
              onSaveAndContinue={(rerun) => handleSaveAndContinue(s.stage, rerun)}
            >
              {s.status !== 'pending' && renderStageContent(s.stage)}
            </StagePanel>
          ))}
        </main>
        <StatusBar />
      </div>
    </div>
  );
}
