import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api, Job, Scene } from '../api';
import { ProgressBar } from '../components/ProgressBar';
import styles from './SceneEditor.module.css';

export function SceneEditor() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const id = Number(jobId);

  const [job, setJob] = useState<Job | null>(null);
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [expandedScene, setExpandedScene] = useState<number | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [j, s] = await Promise.all([api.getJob(id), api.getScenes(id)]);
        setJob(j);
        setScenes(s);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [jobId]);

  async function handleContinue() {
    setSaving(true);
    try {
      await api.saveScenes(id, scenes as any);
      const updated = await api.continueJob(id);
      navigate(`/job/${id}/episodes`);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  function updateScene(index: number, field: string, value: any) {
    setScenes(prev => {
      const next = [...prev];
      next[index] = { ...next[index], [field]: value };
      return next;
    });
  }

  function updateBeat(sceneIndex: number, beatIndex: number, field: string, value: any) {
    setScenes(prev => {
      const next = [...prev];
      const beats = [...next[sceneIndex].beats];
      beats[beatIndex] = { ...beats[beatIndex], [field]: value };
      next[sceneIndex] = { ...next[sceneIndex], beats };
      return next;
    });
  }

  if (loading) return <div className={styles.center}>Loading...</div>;
  if (!job) return <div className={styles.center}>Job not found</div>;

  const chapterGroups = scenes.reduce<Record<string, Scene[]>>((acc, s) => {
    const key = s.chapter_title || `Chapter ${s.chapter_id}`;
    if (!acc[key]) acc[key] = [];
    acc[key].push(s);
    return acc;
  }, {});

  return (
    <div>
      <ProgressBar currentStage={job.pipeline_stage} status={job.status} />
      <h2>场景编辑</h2>
      <p className={styles.desc}>确认和编辑 AI 分析的场景。点击场景查看和编辑具体节拍（台词、动作、镜头）。</p>
      {error && <div className={styles.error}>{error}</div>}

      {Object.entries(chapterGroups).map(([chapter, chapterScenes]) => (
        <div key={chapter} className={styles.chapterGroup}>
          <h3 className={styles.chapterTitle}>{chapter}</h3>
          {chapterScenes.map(scene => {
            const sceneIndex = scenes.indexOf(scene);
            const isExpanded = expandedScene === scene.id;
            return (
              <div key={scene.id} className={styles.sceneCard}>
                <div className={styles.sceneHeader} onClick={() => setExpandedScene(isExpanded ? null : scene.id)}>
                  <span>{isExpanded ? '▼' : '▶'}</span>
                  <input
                    value={scene.heading || ''}
                    onChange={e => updateScene(sceneIndex, 'heading', e.target.value)}
                    className={styles.headingInput}
                    onClick={e => e.stopPropagation()}
                  />
                  <span className={styles.charCount}>{scene.beats.length} beats</span>
                </div>

                {isExpanded && (
                  <div className={styles.beatsContainer}>
                    <input
                      placeholder="Scene summary"
                      value={scene.summary || ''}
                      onChange={e => updateScene(sceneIndex, 'summary', e.target.value)}
                      className={styles.summaryInput}
                    />
                    {scene.beats.map((beat, bi) => (
                      <div key={beat.id} className={styles.beat}>
                        <select
                          value={beat.type}
                          onChange={e => updateBeat(sceneIndex, bi, 'type', e.target.value)}
                          className={styles.beatType}
                        >
                          <option value="dialogue">Dialogue</option>
                          <option value="action">Action</option>
                          <option value="direction">Direction</option>
                        </select>
                        {beat.type === 'dialogue' ? (
                          <>
                            <input
                              placeholder="Speaker"
                              value={beat.speaker || ''}
                              onChange={e => updateBeat(sceneIndex, bi, 'speaker', e.target.value)}
                              className={styles.beatSpeaker}
                            />
                            <input
                              placeholder="Line"
                              value={beat.line || ''}
                              onChange={e => updateBeat(sceneIndex, bi, 'line', e.target.value)}
                              className={styles.beatLine}
                            />
                          </>
                        ) : (
                          <input
                            placeholder="Description"
                            value={beat.description || ''}
                            onChange={e => updateBeat(sceneIndex, bi, 'description', e.target.value)}
                            className={styles.beatDesc}
                          />
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ))}

      <div className={styles.actions}>
        <button onClick={handleContinue} disabled={saving} className={styles.continueBtn}>
          {saving ? '保存中...' : '保存并继续 →'}
        </button>
      </div>
    </div>
  );
}
