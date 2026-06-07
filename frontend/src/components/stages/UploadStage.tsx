import { useState, useRef } from 'react';
import { useJobs } from '../../context/JobContext';
import styles from './UploadStage.module.css';

export function UploadStage() {
  const { createNewJob } = useJobs();
  const [text, setText] = useState('');
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [loading, setLoading] = useState(false);
  const [fileName, setFileName] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setFileName(file.name);

    // Auto-detect title from filename (strip extension)
    const baseName = file.name.replace(/\.(txt|text)$/i, '');
    if (!title) setTitle(baseName);

    const reader = new FileReader();
    reader.onload = (ev) => {
      const content = ev.target?.result;
      if (typeof content === 'string') {
        setText(content);
      }
    };
    reader.readAsText(file, 'UTF-8');
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (!file || !file.name.match(/\.(txt|text)$/i)) return;

    setFileName(file.name);
    const baseName = file.name.replace(/\.(txt|text)$/i, '');
    if (!title) setTitle(baseName);

    const reader = new FileReader();
    reader.onload = (ev) => {
      const content = ev.target?.result;
      if (typeof content === 'string') {
        setText(content);
      }
    };
    reader.readAsText(file, 'UTF-8');
  };

  const handleSubmit = async () => {
    if (!text.trim()) return;
    setLoading(true);
    try {
      await createNewJob(text, title || undefined, author || undefined);
      setText('');
      setTitle('');
      setAuthor('');
      setFileName('');
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

      <div className={styles.uploadRow}>
        <input
          ref={fileInputRef}
          type="file"
          accept=".txt,.text"
          onChange={handleFileUpload}
          className={styles.fileInput}
          id="novel-file-upload"
        />
        <label htmlFor="novel-file-upload" className={styles.fileLabel}>
          上传 TXT 文件
        </label>
        {fileName && <span className={styles.fileName}>{fileName}</span>}
      </div>

      <textarea
        className={styles.textarea}
        placeholder="在此粘贴小说原文，或拖拽 TXT 文件到此处..."
        value={text}
        onChange={e => setText(e.target.value)}
        onDragOver={e => e.preventDefault()}
        onDrop={handleDrop}
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
