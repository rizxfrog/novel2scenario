import { useEffect, useCallback } from 'react';
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

const STAGE_LABELS: Record<string, string> = {
  chapter_splitting: '章节拆分',
  character_extraction: '角色提取',
  scene_analysis: '场景分析',
  episode_structuring: '分集组织',
  script_assembly: '剧本生成',
};

const STAGE_COMPONENTS: Record<string, React.ComponentType> = {
  chapter_splitting: ChapterStage,
  character_extraction: CharacterStage,
  scene_analysis: SceneStage,
  episode_structuring: EpisodeStage,
  script_assembly: ScriptStage,
};

export function PipelineView() {
  const { state, continuePipeline, retryFromStage, loadJobs } = useJobs();
  const job = state.jobs.find(j => j.id === state.activeJobId);

  // Load jobs on mount
  useEffect(() => {
    loadJobs();
  }, []);

  const handleContinue = useCallback((stage: string, rerunStages: string[]) => {
    if (state.activeJobId) {
      continuePipeline(state.activeJobId);
    }
    // Note: continuePipeline currently ignores rerunStages — API adjustment needed later
  }, [state.activeJobId, continuePipeline]);

  const handleRetry = useCallback((stage: string) => {
    if (state.activeJobId) {
      const afterIdx = state.stages.findIndex(s => s.stage === stage) + 1;
      const downstream = state.stages.slice(afterIdx).map(s => s.stage).filter(s => s !== 'completed');
      retryFromStage(state.activeJobId, stage, downstream);
    }
  }, [state.activeJobId, state.stages, retryFromStage]);

  const renderStageContent = useCallback((stageName: string) => {
    const Component = STAGE_COMPONENTS[stageName];
    if (Component) return <Component />;
    return null;
  }, []);

  // Empty state: no job selected — show upload form for new job creation
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

          {/* Pipeline stages */}
          {state.stages.map((s, i) => (
            <StagePanel
              key={s.stage}
              stage={s}
              label={STAGE_LABELS[s.stage] || s.stage}
              index={i + 1}
              canRetryFrom={s.status === 'completed'}
              onRetry={() => handleRetry(s.stage)}
              onContinue={(rerun) => handleContinue(s.stage, rerun)}
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
