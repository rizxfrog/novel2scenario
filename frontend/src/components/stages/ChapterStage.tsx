import { useEffect, useState } from 'react';
import { useJobs } from '../../context/JobContext';
import styles from './ChapterStage.module.css';

interface Chapter {
  id: number;
  number: number;
  title: string;
  content: string;
}

export function ChapterStage() {
  const { state } = useJobs();
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  useEffect(() => {
    if (state.activeJobId) {
      fetch(`/api/jobs/${state.activeJobId}/chapters`)
        .then(r => r.json())
        .then(setChapters)
        .catch(() => {});
    }
  }, [state.activeJobId]);

  if (chapters.length === 0) {
    return <p className={styles.empty}>暂无章节数据</p>;
  }

  return (
    <div className={styles.container}>
      {chapters.map(ch => (
        <div key={ch.id} className={styles.chapter}>
          <div
            className={styles.header}
            onClick={() => setExpandedId(expandedId === ch.id ? null : ch.id)}
          >
            <span className={styles.number}>第{ch.number}章</span>
            <span className={styles.title}>{ch.title || '(无标题)'}</span>
            <span className={styles.wordCount}>{ch.content.length} 字</span>
          </div>
          {expandedId === ch.id && (
            <div className={styles.content}>{ch.content}</div>
          )}
        </div>
      ))}
    </div>
  );
}
