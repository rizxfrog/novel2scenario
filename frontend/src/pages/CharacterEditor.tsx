import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api, Character, Job } from '../api';
import { ProgressBar } from '../components/ProgressBar';
import styles from './CharacterEditor.module.css';

export function CharacterEditor() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const id = Number(jobId);

  const [job, setJob] = useState<Job | null>(null);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadData();
  }, [jobId]);

  async function loadData() {
    try {
      const [j, chars] = await Promise.all([api.getJob(id), api.getCharacters(id)]);
      setJob(j);
      setCharacters(chars);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleContinue() {
    setSaving(true);
    try {
      await api.saveCharacters(id, characters);
      const updated = await api.continueJob(id);
      navigate(`/job/${id}/scenes`);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  function updateCharacter(index: number, field: string, value: any) {
    setCharacters(prev => {
      const next = [...prev];
      next[index] = { ...next[index], [field]: value };
      return next;
    });
  }

  function removeCharacter(index: number) {
    setCharacters(prev => prev.filter((_, i) => i !== index));
  }

  if (loading) return <div className={styles.center}>Loading...</div>;
  if (!job) return <div className={styles.center}>Job not found</div>;

  return (
    <div>
      <ProgressBar currentStage={job.pipeline_stage} status={job.status} />

      <h2>角色管理</h2>
      <p className={styles.desc}>
        确认和编辑 AI 提取的角色信息。您可以修改角色名字、特点、描述，合并重复角色，或删除不需要的角色。
      </p>

      {error && <div className={styles.error}>{error}</div>}

      <div className={styles.grid}>
        {characters.map((char, i) => (
          <div key={char.id} className={styles.card}>
            <div className={styles.cardHeader}>
              <input
                value={char.name}
                onChange={e => updateCharacter(i, 'name', e.target.value)}
                className={styles.nameInput}
              />
              <button onClick={() => removeCharacter(i)} className={styles.removeBtn}>✕</button>
            </div>
            <select
              value={char.role || ''}
              onChange={e => updateCharacter(i, 'role', e.target.value)}
              className={styles.select}
            >
              <option value="">Select role</option>
              <option value="protagonist">Protagonist</option>
              <option value="antagonist">Antagonist</option>
              <option value="supporting">Supporting</option>
              <option value="minor">Minor</option>
            </select>
            <input
              placeholder="Traits (comma-separated)"
              value={char.traits.join(', ')}
              onChange={e => updateCharacter(i, 'traits', e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
              className={styles.input}
            />
            <textarea
              placeholder="Description"
              value={char.description || ''}
              onChange={e => updateCharacter(i, 'description', e.target.value)}
              className={styles.textarea}
              rows={2}
            />
          </div>
        ))}
      </div>

      <div className={styles.actions}>
        <button onClick={handleContinue} disabled={saving} className={styles.continueBtn}>
          {saving ? '保存中...' : '保存并继续 →'}
        </button>
      </div>
    </div>
  );
}
