import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import styles from './UploadPage.module.css';

export function UploadPage() {
  const [text, setText] = useState('');
  const [title, setTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim()) {
      setError('请输入小说文本');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const job = await api.createJob(text, title || undefined);
      const updated = await api.continueJob(job.id);
      navigate(`/job/${updated.id}/characters`);
    } catch (err: any) {
      setError(err.message || '创建失败');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.page}>
      <h2>上传小说文本</h2>
      <p className={styles.desc}>
        将小说文本（3个章节以上）粘贴到下方，系统将自动识别章节分割。
      </p>

      <form onSubmit={handleSubmit} className={styles.form}>
        <input
          type="text"
          placeholder="小说标题（可选）"
          value={title}
          onChange={e => setTitle(e.target.value)}
          className={styles.input}
        />
        <textarea
          placeholder="在此粘贴小说全文..."
          value={text}
          onChange={e => setText(e.target.value)}
          className={styles.textarea}
          rows={20}
        />
        {error && <div className={styles.error}>{error}</div>}
        <button type="submit" disabled={loading} className={styles.button}>
          {loading ? '处理中...' : '开始转换'}
        </button>
      </form>
    </div>
  );
}
