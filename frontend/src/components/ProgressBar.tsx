import styles from './ProgressBar.module.css';

const STAGES = [
  { key: 'chapter_splitting', label: 'Chapters' },
  { key: 'character_extraction', label: 'Characters' },
  { key: 'scene_analysis', label: 'Scenes' },
  { key: 'episode_structuring', label: 'Episodes' },
  { key: 'script_assembly', label: 'Script' },
];

interface Props {
  currentStage: string;
  status: string;
}

export function ProgressBar({ currentStage, status }: Props) {
  const currentIndex = STAGES.findIndex(s => s.key === currentStage);
  const isComplete = status === 'completed';

  return (
    <div className={styles.bar}>
      {STAGES.map((stage, i) => {
        let cls = styles.step;
        if (i < currentIndex || isComplete) cls += ' ' + styles.done;
        else if (i === currentIndex && status === 'running') cls += ' ' + styles.active;
        else if (i === currentIndex && status === 'failed') cls += ' ' + styles.failed;

        return (
          <div key={stage.key} className={cls}>
            <div className={styles.dot}>{i < currentIndex || isComplete ? '✓' : i + 1}</div>
            <span className={styles.label}>{stage.label}</span>
          </div>
        );
      })}
    </div>
  );
}
