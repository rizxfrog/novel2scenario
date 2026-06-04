import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api, Job, Episode } from '../api';
import { ProgressBar } from '../components/ProgressBar';
import styles from './EpisodePlanner.module.css';

export function EpisodePlanner() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const id = Number(jobId);

  const [job, setJob] = useState<Job | null>(null);
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const [j, eps] = await Promise.all([api.getJob(id), api.getEpisodes(id)]);
        setJob(j);
        setEpisodes(eps);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [jobId]);

  async function handleFinish() {
    setSaving(true);
    try {
      await api.saveEpisodes(id, episodes as any);
      const updated = await api.continueJob(id);
      navigate(`/job/${id}/script`);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  function updateEpisode(index: number, field: string, value: any) {
    setEpisodes(prev => {
      const next = [...prev];
      next[index] = { ...next[index], [field]: value };
      return next;
    });
  }

  if (loading) return <div className={styles.center}>Loading...</div>;
  if (!job) return <div className={styles.center}>Job not found</div>;

  return (
    <div>
      <ProgressBar currentStage={job.pipeline_stage} status={job.status} />
      <h2>剧集规划</h2>
      <p className={styles.desc}>确认和编辑 AI 生成的剧集结构。每集包含若干场景。</p>
      {error && <div className={styles.error}>{error}</div>}

      <div className={styles.episodes}>
        {episodes.map((ep, i) => (
          <div key={ep.id} className={styles.episode}>
            <div className={styles.epHeader}>
              <span className={styles.epNum}>Episode {ep.number}</span>
              <input
                value={ep.title || ''}
                onChange={e => updateEpisode(i, 'title', e.target.value)}
                className={styles.epTitle}
                placeholder="Episode title"
              />
              <span className={styles.sceneCount}>{ep.scene_ids.length} scenes</span>
            </div>
            <textarea
              value={ep.summary || ''}
              onChange={e => updateEpisode(i, 'summary', e.target.value)}
              className={styles.epSummary}
              rows={3}
              placeholder="Episode summary"
            />
            <div className={styles.chapterInfo}>
              Chapters: {ep.novel_chapters.join(', ')}
            </div>
            <div className={styles.sceneIds}>
              Scenes: [{ep.scene_ids.join(', ')}]
            </div>
          </div>
        ))}
      </div>

      <div className={styles.actions}>
        <button onClick={handleFinish} disabled={saving} className={styles.continueBtn}>
          {saving ? '生成中...' : '生成剧本 →'}
        </button>
      </div>
    </div>
  );
}
