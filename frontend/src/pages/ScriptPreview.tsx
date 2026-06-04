import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api, Job } from '../api';
import { ProgressBar } from '../components/ProgressBar';
import styles from './ScriptPreview.module.css';

export function ScriptPreview() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const id = Number(jobId);

  const [job, setJob] = useState<Job | null>(null);
  const [script, setScript] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const j = await api.getJob(id);
        setJob(j);
        if (j.status === 'completed' || j.pipeline_stage === 'script_assembly') {
          const s = await api.getScript(id);
          setScript(s);
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [jobId]);

  function downloadYaml() {
    if (!script) return;
    const yamlStr = JSON.stringify(script, null, 2);
    const blob = new Blob([yamlStr], { type: 'text/yaml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${script.meta?.title || 'script'}.yaml`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (loading) return <div className={styles.center}>Loading...</div>;
  if (!job) return <div className={styles.center}>Job not found</div>;

  if (job.status !== 'completed' && job.pipeline_stage !== 'script_assembly') {
    return (
      <div className={styles.center}>
        <p>Script not yet generated. Current stage: {job.pipeline_stage}</p>
      </div>
    );
  }

  return (
    <div>
      <ProgressBar currentStage={job.pipeline_stage} status={job.status} />
      <h2>剧本预览</h2>
      <p className={styles.desc}>
        以下是生成的剧本初稿。您可以下载 YAML 文件进行进一步编辑。
        {job.status === 'completed' && ' — 剧本已生成完成！'}
      </p>
      {error && <div className={styles.error}>{error}</div>}

      {script && (
        <>
          <div className={styles.meta}>
            <strong>{script.meta?.title || 'Untitled'}</strong>
            {script.meta?.author && ` by ${script.meta.author}`}
            {' · '}{script.episodes?.length || 0} episodes
            {' · '}{script.meta?.total_chapters_in_novel || 0} chapters in novel
          </div>

          <div className={styles.code}>
            <pre>{JSON.stringify(script, null, 2)}</pre>
          </div>

          <div className={styles.actions}>
            <button onClick={downloadYaml} className={styles.downloadBtn}>
              下载 YAML
            </button>
            <button onClick={() => navigate('/')} className={styles.newBtn}>
              创建新转换
            </button>
          </div>
        </>
      )}
    </div>
  );
}
