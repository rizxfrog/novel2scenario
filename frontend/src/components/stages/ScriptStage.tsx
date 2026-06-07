import { useEffect, useState } from 'react';
import { useJobs } from '../../context/JobContext';
import { api } from '../../api';
import styles from './ScriptStage.module.css';

function toYaml(obj: any, indent = 0): string {
  const pad = '  '.repeat(indent);
  if (obj === null || obj === undefined) return `${pad}~`;
  if (typeof obj === 'string') {
    if (obj.includes('\n') || obj.includes(':') || obj.includes('#')) {
      return `${pad}|-\n${obj.split('\n').map(l => `  ${pad}${l}`).join('\n')}`;
    }
    return `${pad}'${obj}'`;
  }
  if (typeof obj === 'number' || typeof obj === 'boolean') return `${pad}${obj}`;
  if (Array.isArray(obj)) {
    if (obj.length === 0) return `${pad}[]`;
    return obj.map(item => `${pad}- ${toYaml(item, 0).replace(/^\s+/, '')}`).join('\n');
  }
  if (typeof obj === 'object') {
    const keys = Object.keys(obj);
    if (keys.length === 0) return `${pad}{}`;
    return keys.map(k => {
      const val = obj[k];
      if (val === null || val === undefined) return `${pad}${k}: ~`;
      if (Array.isArray(val)) {
        if (val.length === 0) return `${pad}${k}: []`;
        if (typeof val[0] === 'object') {
          return `${pad}${k}:\n${val.map((v: any) => {
            const inner = toYaml(v, indent + 1);
            if (inner.startsWith('  '.repeat(indent + 1))) return `${pad}  - \n${inner}`;
            return `${pad}  - ${inner.replace(/^\s+/, '')}`;
          }).join('\n')}`;
        }
        return `${pad}${k}:\n${val.map((v: any) => `${pad}  - ${toYaml(v, 0).replace(/^\s+/, '')}`).join('\n')}`;
      }
      if (typeof val === 'object') {
        return `${pad}${k}:\n${toYaml(val, indent + 1)}`;
      }
      return `${pad}${k}: ${toYaml(val, 0).replace(/^\s+/, '')}`;
    }).join('\n');
  }
  return `${pad}${obj}`;
}

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

  const downloadFile = (content: string, filename: string, mime: string) => {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
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
        <button
          className={styles.downloadBtn}
          onClick={() => downloadFile(JSON.stringify(script, null, 2), `script-job-${state.activeJobId}.json`, 'application/json')}
        >
          下载 JSON
        </button>
        <button
          className={styles.downloadYamlBtn}
          onClick={() => downloadFile(toYaml(script), `script-job-${state.activeJobId}.yaml`, 'text/yaml')}
        >
          下载 YAML
        </button>
      </div>
    </div>
  );
}
