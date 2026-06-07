import { useEffect, useState } from 'react';
import { useJobs } from '../../context/JobContext';
import { api } from '../../api';
import type { Character } from '../../api';
import styles from './CharacterStage.module.css';

export function CharacterStage() {
  const { state } = useJobs();
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (state.activeJobId) {
      api.getCharacters(state.activeJobId).then(setCharacters).catch(() => {});
    }
  }, [state.activeJobId]);

  const updateField = (index: number, field: keyof Character, value: unknown) => {
    setCharacters(prev => prev.map((ch, i) => i === index ? { ...ch, [field]: value } : ch));
  };

  const handleSave = async () => {
    if (!state.activeJobId) return;
    setLoading(true);
    try {
      await api.saveCharacters(state.activeJobId, characters);
    } catch {
      // error handled by context
    } finally {
      setLoading(false);
    }
  };

  if (characters.length === 0) {
    return <p className={styles.empty}>暂无角色数据</p>;
  }

  return (
    <div>
      <div className={styles.grid}>
        {characters.map((ch, i) => (
          <div key={ch.id || i} className={styles.card}>
            <input
              className={styles.name}
              value={ch.name}
              onChange={e => updateField(i, 'name', e.target.value)}
              placeholder="角色名"
            />
            <select
              className={styles.role}
              value={ch.role || ''}
              onChange={e => updateField(i, 'role', e.target.value)}
            >
              <option value="">选择角色</option>
              <option value="protagonist">主角</option>
              <option value="antagonist">反派</option>
              <option value="supporting">配角</option>
              <option value="minor">次要角色</option>
            </select>
            <input
              className={styles.traits}
              value={(ch.traits || []).join(', ')}
              onChange={e => updateField(i, 'traits', e.target.value.split(',').map(t => t.trim()).filter(Boolean))}
              placeholder="特质，用逗号分隔"
            />
            <textarea
              className={styles.description}
              value={ch.description || ''}
              onChange={e => updateField(i, 'description', e.target.value)}
              placeholder="角色描述..."
              rows={3}
            />
          </div>
        ))}
      </div>
      <button className={styles.saveBtn} onClick={handleSave} disabled={loading}>
        {loading ? '保存中...' : '保存角色'}
      </button>
    </div>
  );
}
