import { useEffect, useState } from 'react';
import { useJobs } from '../../context/JobContext';
import { api } from '../../api';
import type { Scene, SceneBeat } from '../../api';
import styles from './SceneStage.module.css';

const EMPTY_BEAT: SceneBeat = { id: 0, number: 1, type: 'action', description: '' };
const EMPTY_SCENE: Scene = {
  id: 0, job_id: 0, chapter_id: 1, number: 1,
  heading: '', summary: '', characters_present: [],
  beats: [EMPTY_BEAT], chapter_title: '',
};

export function SceneStage({ setData }: { setData?: (data: any) => void }) {
  const { state } = useJobs();
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [aiInstruction, setAiInstruction] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [showAiPanel, setShowAiPanel] = useState(false);

  useEffect(() => {
    if (state.activeJobId) {
      api.getScenes(state.activeJobId).then(setScenes).catch(() => {});
    }
  }, [state.activeJobId]);

  // Report data changes to PipelineView for save-and-continue
  useEffect(() => {
    setData?.(scenes);
  }, [scenes, setData]);

  const updateScene = (index: number, field: keyof Scene, value: unknown) => {
    setScenes(prev => prev.map((sc, i) => i === index ? { ...sc, [field]: value } : sc));
  };

  const updateBeat = (sceneIdx: number, beatIdx: number, field: keyof SceneBeat, value: unknown) => {
    setScenes(prev => prev.map((sc, si) => {
      if (si !== sceneIdx) return sc;
      return {
        ...sc,
        beats: sc.beats.map((b, bi) => bi === beatIdx ? { ...b, [field]: value } : b),
      };
    }));
  };

  const addScene = () => {
    setScenes(prev => [...prev, { ...EMPTY_SCENE, number: prev.length + 1 }]);
  };

  const deleteScene = (index: number) => {
    setScenes(prev => prev.filter((_, i) => i !== index));
  };

  const addBeat = (sceneIdx: number) => {
    setScenes(prev => prev.map((sc, si) => {
      if (si !== sceneIdx) return sc;
      const newNum = sc.beats.length + 1;
      return {
        ...sc,
        beats: [...sc.beats, { ...EMPTY_BEAT, number: newNum }],
      };
    }));
  };

  const deleteBeat = (sceneIdx: number, beatIdx: number) => {
    setScenes(prev => prev.map((sc, si) => {
      if (si !== sceneIdx) return sc;
      return { ...sc, beats: sc.beats.filter((_, bi) => bi !== beatIdx) };
    }));
  };

  const handleSave = async () => {
    if (!state.activeJobId) return;
    setLoading(true);
    try {
      await api.saveScenes(state.activeJobId, scenes);
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
        'scene_analysis',
        aiInstruction.trim(),
        { scenes },
      );
      if (result.data?.scenes) {
        setScenes(result.data.scenes);
      }
    } catch (e: any) {
      setAiError(e.message || 'AI 修改失败');
    } finally {
      setAiLoading(false);
    }
  };

  if (scenes.length === 0 && !showAiPanel) {
    return (
      <div>
        <p className={styles.empty}>暂无场景数据</p>
        <div className={styles.toolbar}>
          <button className={styles.addBtn} onClick={addScene}>+ 添加场景</button>
          <button className={styles.aiToggleBtn} onClick={() => setShowAiPanel(true)}>AI 辅助修改</button>
        </div>
      </div>
    );
  }

  return (
    <div>
      {scenes.map((sc, si) => (
        <div key={sc.id || si} className={styles.scene}>
          <div
            className={styles.header}
            onClick={() => setExpandedId(expandedId === (sc.id || si) ? null : (sc.id || si))}
          >
            <span className={styles.number}>场景 {sc.number}</span>
            <input
              className={styles.headingInput}
              value={sc.heading || ''}
              onChange={e => updateScene(si, 'heading', e.target.value)}
              onClick={e => e.stopPropagation()}
              placeholder="场景标题"
            />
            <span className={styles.chapter}>{sc.chapter_title}</span>
            <span className={styles.beatCount}>{sc.beats.length} 节拍</span>
            <button
              className={styles.deleteBtn}
              onClick={e => { e.stopPropagation(); deleteScene(si); }}
              title="删除场景"
            >x</button>
            <span className={styles.chevron}>{expandedId === (sc.id || si) ? 'v' : '>'}</span>
          </div>
          {expandedId === (sc.id || si) && (
            <div className={styles.body}>
              <textarea
                className={styles.summaryInput}
                value={sc.summary || ''}
                onChange={e => updateScene(si, 'summary', e.target.value)}
                placeholder="场景概要..."
                rows={2}
              />
              <div className={styles.beats}>
                {sc.beats.map((beat, bi) => (
                  <div key={beat.id || bi} className={styles.beat}>
                    <span className={styles.beatNum}>#{beat.number}</span>
                    <select
                      className={styles.beatType}
                      value={beat.type || ''}
                      onChange={e => updateBeat(si, bi, 'type', e.target.value)}
                    >
                      <option value="action">action</option>
                      <option value="dialogue">dialogue</option>
                      <option value="monologue">monologue</option>
                      <option value="description">description</option>
                      <option value="transition">transition</option>
                    </select>
                    {beat.speaker !== undefined && (
                      <input
                        className={styles.beatSpeaker}
                        value={beat.speaker || ''}
                        onChange={e => updateBeat(si, bi, 'speaker', e.target.value)}
                        placeholder="说话人"
                      />
                    )}
                    {beat.line !== undefined && (
                      <input
                        className={styles.beatLine}
                        value={beat.line || ''}
                        onChange={e => updateBeat(si, bi, 'line', e.target.value)}
                        placeholder="台词"
                      />
                    )}
                    <input
                      className={styles.beatDesc}
                      value={beat.description || ''}
                      onChange={e => updateBeat(si, bi, 'description', e.target.value)}
                      placeholder="描述"
                    />
                    <button
                      className={styles.beatDeleteBtn}
                      onClick={() => deleteBeat(si, bi)}
                      title="删除节拍"
                    >x</button>
                  </div>
                ))}
                <button className={styles.addBeatBtn} onClick={() => addBeat(si)}>+ 添加节拍</button>
              </div>
            </div>
          )}
        </div>
      ))}

      <div className={styles.toolbar}>
        <button className={styles.addBtn} onClick={addScene}>+ 添加场景</button>
        <button className={styles.saveBtn} onClick={handleSave} disabled={loading}>
          {loading ? '保存中...' : '保存场景'}
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
              placeholder="描述你想要的修改，例如：'请给场景3添加一段追逐戏' 或 '合并场景4和场景5'"
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
