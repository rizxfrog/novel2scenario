import { useState } from 'react';
import { useJobs } from '../../context/JobContext';
import styles from './UploadStage.module.css';

export function UploadStage() {
  const { createNewJob } = useJobs();
  const [text, setText] = useState('');
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!text.trim()) return;
    setLoading(true);
    try {
      await createNewJob(text, title || undefined, author || undefined);
      setText('');
      setTitle('');
      setAuthor('');
    } catch {
      // error already handled by context
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <input
        className={styles.input}
        placeholder="小说标题（可选）"
        value={title}
        onChange={e => setTitle(e.target.value)}
      />
      <input
        className={styles.input}
        placeholder="作者（可选）"
        value={author}
        onChange={e => setAuthor(e.target.value)}
      />
      <textarea
        className={styles.textarea}
        placeholder="在此粘贴小说原文..."
        value={text}
        onChange={e => setText(e.target.value)}
        rows={14}
      />
      <button
        className={styles.submit}
        onClick={handleSubmit}
        disabled={!text.trim() || loading}
      >
        {loading ? '正在创建...' : '开始转换'}
      </button>
    </div>
  );
}
