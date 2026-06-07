import { useEffect, useState } from 'react';
import { useJobs } from '../../context/JobContext';
import { api } from '../../api';
import type { Scene } from '../../api';
import styles from './SceneStage.module.css';

export function SceneStage() {
  const { state } = useJobs();
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (state.activeJobId) {
      api.getScenes(state.activeJobId).then(setScenes).catch(() => {});
    }
  }, [state.activeJobId]);

  const handleSave = async () => {
    if (!state.activeJobId) return;
    setLoading(true);
    try {
      await api.saveScenes(state.activeJobId, scenes);
    } finally {
      setLoading(false);
    }
  };

  if (scenes.length === 0) {
    return <p className={styles.empty}>暂无场景数据</p>;
  }

  return (
    <div>
      {scenes.map(sc => (
        <div key={sc.id} className={styles.scene}>
          <div
            className={styles.header}
            onClick={() => setExpandedId(expandedId === sc.id ? null : sc.id)}
          >
            <span className={styles.number}>场景 {sc.number}</span>
            <span className={styles.heading}>{sc.heading || '(无标题)'}</span>
            <span className={styles.chapter}>{sc.chapter_title}</span>
            <span className={styles.beatCount}>{sc.beats.length} 节拍</span>
          </div>
          {expandedId === sc.id && (
            <div className={styles.body}>
              <p className={styles.summary}>{sc.summary}</p>
              <div className={styles.beats}>
                {sc.beats.map(beat => (
                  <div key={beat.id} className={styles.beat}>
                    <span className={styles.beatNum}>#{beat.number}</span>
                    <span className={styles.beatType}>{beat.type}</span>
                    {beat.speaker && <span className={styles.beatSpeaker}>{beat.speaker}</span>}
                    {beat.line && <span className={styles.beatLine}>{beat.line}</span>}
                    {beat.description && <span className={styles.beatDesc}>{beat.description}</span>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
      <button className={styles.saveBtn} onClick={handleSave} disabled={loading}>
        {loading ? '保存中...' : '保存场景'}
      </button>
    </div>
  );
}
