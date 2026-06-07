import { useEffect, useState } from 'react';
import { useJobs } from '../../context/JobContext';
import { api } from '../../api';
import styles from './ScriptStage.module.css';

export function ScriptStage() {
  const { state } = useJobs();
  const [script, setScript] = useState<any>(null);

  useEffect(() => {
    if (state.activeJobId) {
      api.getScript(state.activeJobId).then(setScript).catch(() => {});
    }
  }, [state.activeJobId]);

  if (!script) {
    return <p className={styles.empty}>暂无剧本数据</p>;
  }

  const handleDownload = () => {
    const blob = new Blob([JSON.stringify(script, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `script-job-${state.activeJobId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div>
      {script.meta && (
        <div className={styles.meta}>
          <span>{script.meta.title || '未命名'}</span>
          <span>共 {script.meta.total_episodes} 集</span>
          <span>{script.meta.total_chapters_in_novel} 章</span>
        </div>
      )}
      <pre className={styles.preview}>{JSON.stringify(script, null, 2)}</pre>
      <div className={styles.actions}>
        <button className={styles.downloadBtn} onClick={handleDownload}>下载剧本</button>
      </div>
    </div>
  );
}
