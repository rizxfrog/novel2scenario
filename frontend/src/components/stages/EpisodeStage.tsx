import { useEffect, useState } from 'react';
import { useJobs } from '../../context/JobContext';
import { api } from '../../api';
import type { Episode } from '../../api';
import styles from './EpisodeStage.module.css';

export function EpisodeStage() {
  const { state } = useJobs();
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (state.activeJobId) {
      api.getEpisodes(state.activeJobId).then(setEpisodes).catch(() => {});
    }
  }, [state.activeJobId]);

  const updateField = (index: number, field: keyof Episode, value: unknown) => {
    setEpisodes(prev => prev.map((ep, i) => i === index ? { ...ep, [field]: value } : ep));
  };

  const handleSave = async () => {
    if (!state.activeJobId) return;
    setLoading(true);
    try {
      await api.saveEpisodes(state.activeJobId, episodes);
    } finally {
      setLoading(false);
    }
  };

  if (episodes.length === 0) {
    return <p className={styles.empty}>暂无分集数据</p>;
  }

  return (
    <div>
      {episodes.map((ep, i) => (
        <div key={ep.id} className={styles.episode}>
          <div className={styles.header}>
            <span className={styles.number}>第 {ep.number} 集</span>
          </div>
          <div className={styles.body}>
            <input
              className={styles.title}
              value={ep.title || ''}
              onChange={e => updateField(i, 'title', e.target.value)}
              placeholder="分集标题"
            />
            <textarea
              className={styles.summary}
              value={ep.summary || ''}
              onChange={e => updateField(i, 'summary', e.target.value)}
              placeholder="分集概要..."
              rows={3}
            />
            <div className={styles.meta}>
              <span>场景数: {ep.scene_ids.length}</span>
              <span>相关章节: {(ep.novel_chapters || []).join(', ')}</span>
            </div>
          </div>
        </div>
      ))}
      <button className={styles.saveBtn} onClick={handleSave} disabled={loading}>
        {loading ? '保存中...' : '保存分集'}
      </button>
    </div>
  );
}
