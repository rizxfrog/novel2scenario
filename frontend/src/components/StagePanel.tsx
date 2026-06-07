import { type ReactNode, useState } from 'react';
import type { StageStatus } from '../api';
import styles from './StagePanel.module.css';

interface StagePanelProps {
  stage: StageStatus;
  label: string;
  index: number;
  children: ReactNode;
  onRetry?: () => void;
  onSaveAndContinue?: (rerunStages: string[]) => void;
  canRetryFrom?: boolean;
}

const ALL_STAGES = [
  'chapter_splitting', 'character_extraction', 'scene_analysis',
  'episode_structuring', 'script_assembly',
];

const STAGE_NAMES: Record<string, string> = {
  chapter_splitting: '章节拆分',
  character_extraction: '角色提取',
  scene_analysis: '场景分析',
  episode_structuring: '分集组织',
  script_assembly: '剧本生成',
};

export function StagePanel({ stage, label, index, children, onRetry, onSaveAndContinue, canRetryFrom }: StagePanelProps) {
  const [expanded, setExpanded] = useState(stage.status === 'awaiting_review' || stage.status === 'failed');
  const [rerunStages, setRerunStages] = useState<string[]>([]);
  const isLocked = stage.status === 'pending' && index > 1;

  const toggleExpanded = () => {
    if (!isLocked) setExpanded(!expanded);
  };

  const statusIndicator = () => {
    switch (stage.status) {
      case 'completed':
        return (
          <span className={styles.indicator} style={{ background: '#4ecca3', color: '#1a1a2e' }}>
            ✓
          </span>
        );
      case 'running':
        return <span className={`${styles.indicator} ${styles.spinner}`} />;
      case 'awaiting_review':
        return (
          <span className={styles.indicator} style={{ background: '#e94560', color: 'white' }}>
            !
          </span>
        );
      case 'failed':
        return (
          <span className={styles.indicator} style={{ background: '#ff6b6b', color: 'white' }}>
            ✕
          </span>
        );
      default:
        return (
          <span className={styles.indicator} style={{ background: '#333', color: '#666' }}>
            {index}
          </span>
        );
    }
  };

  const statusMeta = () => {
    if (stage.status === 'running') return '运行中...';
    if (stage.status === 'awaiting_review') return '等待审核';
    if (stage.status === 'completed') return stage.output_summary || '完成';
    if (stage.status === 'failed') return '失败';
    return '等待中';
  };

  const downstreamStages = ALL_STAGES.slice(index);

  return (
    <div
      className={`${styles.panel} ${isLocked ? styles.locked : ''} ${
        stage.status === 'failed' ? styles.failed : ''
      } ${stage.status === 'awaiting_review' ? styles.activeReview : ''}`}
    >
      <div className={styles.header} onClick={toggleExpanded}>
        {statusIndicator()}
        <span className={styles.label}>{label}</span>
        <span className={styles.meta}>{statusMeta()}</span>
        <span className={styles.chevron}>{expanded ? '▼' : '▶'}</span>
      </div>

      {expanded && (
        <div className={styles.body}>
          {stage.status === 'failed' && stage.error_message && (
            <div className={styles.error}>
              <span className={styles.errorText}>{stage.error_message}</span>
              {onRetry && (
                <button className={styles.retryBtn} onClick={onRetry}>重试</button>
              )}
            </div>
          )}
          {children}

          {stage.status === 'awaiting_review' && onSaveAndContinue && (
            <div className={styles.actions}>
              <div className={styles.checkboxes}>
                {downstreamStages.map(s => (
                  <label key={s} className={styles.checkbox}>
                    <input
                      type="checkbox"
                      checked={rerunStages.includes(s)}
                      onChange={e => {
                        if (e.target.checked) {
                          setRerunStages([...rerunStages, s]);
                        } else {
                          setRerunStages(rerunStages.filter(rs => rs !== s));
                        }
                      }}
                    />
                    {STAGE_NAMES[s] || s}
                  </label>
                ))}
              </div>
              <button
                className={styles.continueBtn}
                onClick={() => onSaveAndContinue(rerunStages)}
              >
                保存并继续
              </button>
            </div>
          )}

          {canRetryFrom && stage.status === 'completed' && onRetry && (
            <div className={styles.actions}>
              <button className={styles.retryFromBtn} onClick={onRetry}>
                从此重新运行
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
