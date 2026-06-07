import { useEffect, useState } from 'react';
import { useJobs } from '../../context/JobContext';
import { api } from '../../api';
import type { Episode } from '../../api';
import styles from './EpisodeStage.module.css';

const EMPTY_EPISODE: Episode = {
  id: 0, job_id: 0, number: 1,
  title: '', summary: '', novel_chapters: [], scene_ids: [],
};

export function EpisodeStage({ setData }: { setData?: (data: any) => void }) {
  const { state } = useJobs();
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [loading, setLoading] = useState(false);
  const [aiInstruction, setAiInstruction] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [showAiPanel, setShowAiPanel] = useState(false);

  useEffect(() => {
    if (state.activeJobId) {
      api.getEpisodes(state.activeJobId).then(setEpisodes).catch(() => {});
    }
  }, [state.activeJobId]);

  // Report data changes to PipelineView for save-and-continue
  useEffect(() => {
    setData?.(episodes);
  }, [episodes, setData]);

  const updateField = (index: number, field: keyof Episode, value: unknown) => {
    setEpisodes(prev => prev.map((ep, i) => i === index ? { ...ep, [field]: value } : ep));
  };

  const addEpisode = () => {
    setEpisodes(prev => [...prev, { ...EMPTY_EPISODE, number: prev.length + 1 }]);
  };

  const deleteEpisode = (index: number) => {
    setEpisodes(prev => prev.filter((_, i) => i !== index));
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

  const handleAiAssist = async () => {
    if (!state.activeJobId || !aiInstruction.trim()) return;
    setAiLoading(true);
    setAiError(null);
    try {
      const result = await api.aiAssist(
        state.activeJobId,
        'episode_structuring',
        aiInstruction.trim(),
        { episodes },
      );
      if (result.data?.episodes) {
        setEpisodes(result.data.episodes);
      }
    } catch (e: any) {
      setAiError(e.message || 'AI 修改失败');
    } finally {
      setAiLoading(false);
    }
  };

  if (episodes.length === 0 && !showAiPanel) {
    return (
      <div>
        <p className={styles.empty}>暂无分集数据</p>
        <div className={styles.toolbar}>
          <button className={styles.addBtn} onClick={addEpisode}>+ 添加分集</button>
          <button className={styles.aiToggleBtn} onClick={() => setShowAiPanel(true)}>AI 辅助修改</button>
        </div>
      </div>
    );
  }

  return (
    <div>
      {episodes.map((ep, i) => (
        <div key={ep.id || i} className={styles.episode}>
          <div className={styles.header}>
            <span className={styles.number}>第 {ep.number} 集</span>
            <button
              className={styles.deleteBtn}
              onClick={() => deleteEpisode(i)}
              title="删除分集"
            >x</button>
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

      <div className={styles.toolbar}>
        <button className={styles.addBtn} onClick={addEpisode}>+ 添加分集</button>
        <button className={styles.saveBtn} onClick={handleSave} disabled={loading}>
          {loading ? '保存中...' : '保存分集'}
        </button>
      </div>

      {/* AI Assist Panel */}
      <div className={styles.aiPanel}>
        <button className={styles.aiToggleBtn} onClick={() => setShowAiPanel(!showAiPanel)}>
          {showAiPanel ? '收起 AI 面板' : 'AI 辅助修改'}
        </button>
        {showAiPanel && (
          <div className={styles.aiBody}>
            <textarea
              className={styles.aiInput}
              value={aiInstruction}
              onChange={e => setAiInstruction(e.target.value)}
              placeholder="描述你想要的修改，例如：'请把第1集拆分成两集' 或 '调整第3集的场景顺序'"
              rows={3}
            />
            {aiError && <p className={styles.aiError}>{aiError}</p>}
            <button
              className={styles.aiBtn}
              onClick={handleAiAssist}
              disabled={aiLoading || !aiInstruction.trim()}
            >
              {aiLoading ? 'AI 思考中...' : 'AI 辅助修改'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
