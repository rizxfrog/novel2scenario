import { useJobs } from '../context/JobContext';
import styles from './StatusBar.module.css';

const STAGE_NAMES: Record<string, string> = {
  chapter_splitting: '章节拆分',
  character_extraction: '角色提取',
  scene_analysis: '场景分析',
  episode_structuring: '分集组织',
  script_assembly: '剧本生成',
};

const STATUS_LABELS: Record<string, string> = {
  running: '运行中',
  awaiting_review: '等待审核',
  completed: '完成',
  failed: '失败',
  pending: '等待中',
};

export function StatusBar() {
  const { state } = useJobs();
  const job = state.jobs.find(j => j.id === state.activeJobId);
  if (!job) return null;

  const currentStage = state.stages.find(
    s => s.status === 'running' || s.status === 'awaiting_review' || s.status === 'failed'
  );

  // If no active stage, check if all are completed
  const allDone = !currentStage && state.stages.length > 0
    && state.stages.every(s => s.status === 'completed');

  const isFailed = currentStage?.status === 'failed';

  // Find the display stage: current active one, or last one if all done
  const displayStage = currentStage || (allDone ? state.stages[state.stages.length - 1] : null);
  const stageIndex = displayStage ? state.stages.findIndex(s => s.stage === displayStage.stage) + 1 : 0;

  return (
    <div className={`${styles.bar} ${isFailed ? styles.failed : ''}`}>
      <div className={styles.left}>
        <span className={styles.label}>Job:</span>
        <span>{job.title || `Job #${job.id}`}</span>
        {displayStage && (
          <>
            <span className={styles.separator}>|</span>
            <span className={styles.label}>阶段:</span>
            <span>{stageIndex}/5 {STAGE_NAMES[displayStage.stage] || displayStage.stage}</span>
          </>
        )}
      </div>
      <div className={styles.right}>
        {isFailed && (
          <>
            <span className={`${styles.badge} ${styles.badge_failed}`}>失败</span>
            {currentStage?.error_message && (
              <span className={styles.error}>{currentStage.error_message}</span>
            )}
          </>
        )}
        {currentStage && !isFailed && (
          <span className={`${styles.badge} ${styles['badge_' + currentStage.status]}`}>
            {STATUS_LABELS[currentStage.status] || currentStage.status}
          </span>
        )}
        {allDone && (
          <span className={`${styles.badge} ${styles.badge_completed}`}>全部完成</span>
        )}
        {!displayStage && (
          <span className={`${styles.badge} ${styles.badge_pending}`}>等待开始</span>
        )}
      </div>
    </div>
  );
}
