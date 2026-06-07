import { useState, useEffect, useCallback } from 'react';
import { useJobs } from '../context/JobContext';
import styles from './Sidebar.module.css';

const STATUS_ICONS: Record<string, string> = {
  queued: '\u25CB',
  running: '\u23F3',
  awaiting_review: '\u25CB',
  completed: '\u2714',
  failed: '\u2715',
};

const STATUS_CLASS: Record<string, string> = {
  running: 'statusRunning',
  awaiting_review: 'statusReview',
  completed: 'statusDone',
  failed: 'statusFailed',
  queued: 'statusQueued',
};

export function Sidebar() {
  const { state, loadJobs, removeJob, selectJob, dispatch } = useJobs();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    loadJobs(search || undefined, statusFilter || undefined);
  }, [search, statusFilter]);

  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value);
  }, []);

  const handleFilterChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setStatusFilter(e.target.value);
  }, []);

  return (
    <aside className={styles.sidebar}>
      <div className={styles.header}>Jobs</div>

      <input
        className={styles.search}
        type="text"
        placeholder="搜索..."
        value={search}
        onChange={handleSearchChange}
      />

      <select
        className={styles.filter}
        value={statusFilter}
        onChange={handleFilterChange}
      >
        <option value="">全部状态</option>
        <option value="completed">已完成</option>
        <option value="awaiting_review">等待审核</option>
        <option value="running">运行中</option>
        <option value="failed">失败</option>
        <option value="queued">排队中</option>
      </select>

      <div className={styles.list}>
        {state.jobs.map(job => (
          <div
            key={job.id}
            className={`${styles.item} ${job.id === state.activeJobId ? styles.active : ''}`}
            onClick={() => selectJob(job.id)}
          >
            <div className={styles.jobTitle}>{job.title || `Job #${job.id}`}</div>
            <div className={`${styles.jobStatus} ${styles[STATUS_CLASS[job.status] || 'statusQueued']}`}>
              <span>{STATUS_ICONS[job.status] || '\u25CB'}</span>
              <span>{job.pipeline_stage || job.status}</span>
            </div>
            <button
              className={styles.deleteBtn}
              onClick={e => {
                e.stopPropagation();
                if (confirm('确定删除此 Job？')) removeJob(job.id);
              }}
              title="删除"
            >&times;</button>
          </div>
        ))}
        {state.jobs.length === 0 && (
          <div className={styles.empty}>暂无任务</div>
        )}
      </div>
      <button
        className={styles.newBtn}
        onClick={() => dispatch({ type: 'SET_ACTIVE_JOB', jobId: null })}
      >
        + 新建 Job
      </button>
    </aside>
  );
}
