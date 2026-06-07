import { useEffect, useState } from 'react';
import { useJobs } from '../../context/JobContext';
import { api } from '../../api';
import type { Character } from '../../api';
import styles from './CharacterStage.module.css';

const EMPTY_CHARACTER: Character = {
  id: 0,
  job_id: 0,
  name: '',
  role: '',
  traits: [],
  description: '',
  relationships: [],
};

export function CharacterStage({ setData }: { setData?: (data: any) => void }) {
  const { state } = useJobs();
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(false);
  const [aiInstruction, setAiInstruction] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [showAiPanel, setShowAiPanel] = useState(false);

  useEffect(() => {
    if (state.activeJobId) {
      api.getCharacters(state.activeJobId).then(setCharacters).catch(() => {});
    }
  }, [state.activeJobId]);

  // Report data changes to PipelineView for save-and-continue
  useEffect(() => {
    setData?.(characters);
  }, [characters, setData]);

  const updateField = (index: number, field: keyof Character, value: unknown) => {
    setCharacters(prev => prev.map((ch, i) => i === index ? { ...ch, [field]: value } : ch));
  };

  const addCharacter = () => {
    setCharacters(prev => [...prev, { ...EMPTY_CHARACTER }]);
  };

  const deleteCharacter = (index: number) => {
    setCharacters(prev => prev.filter((_, i) => i !== index));
  };

  const handleSave = async () => {
    if (!state.activeJobId) return;
    setLoading(true);
    try {
      await api.saveCharacters(state.activeJobId, characters);
    } finally {
      setLoading(false);
    }
  };

  const handleAiAssist = async () => {
    if (!state.activeJobId || !aiInstruction.trim()) return;
    setAiLoading(true);
    setAiError(null);
    try {
      const result = await api.aiAssist(
        state.activeJobId,
        'character_extraction',
        aiInstruction.trim(),
        { characters },
      );
      if (result.data?.characters) {
        setCharacters(result.data.characters);
      }
    } catch (e: any) {
      setAiError(e.message || 'AI 修改失败');
    } finally {
      setAiLoading(false);
    }
  };

  if (characters.length === 0 && !showAiPanel) {
    return (
      <div>
        <p className={styles.empty}>暂无角色数据</p>
        <div className={styles.toolbar}>
          <button className={styles.addBtn} onClick={addCharacter}>+ 添加角色</button>
          <button className={styles.aiToggleBtn} onClick={() => setShowAiPanel(true)}>AI 辅助修改</button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className={styles.grid}>
        {characters.map((ch, i) => (
          <div key={ch.id || i} className={styles.card}>
            <button className={styles.deleteBtn} onClick={() => deleteCharacter(i)} title="删除角色">x</button>
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

      <div className={styles.toolbar}>
        <button className={styles.addBtn} onClick={addCharacter}>+ 添加角色</button>
        <button className={styles.saveBtn} onClick={handleSave} disabled={loading}>
          {loading ? '保存中...' : '保存角色'}
        </button>
      </div>

      {/* AI Assist Panel */}
      <div className={styles.aiPanel}>
        <button className={styles.aiToggleBtn} onClick={() => setShowAiPanel(!showAiPanel)}>
          {showAiPanel ? '收起 AI 面板' : 'AI 辅助修改'}
        </button>
        {showAiPanel && (
          <div className={styles.aiBody}>
            <textarea
              className={styles.aiInput}
              value={aiInstruction}
              onChange={e => setAiInstruction(e.target.value)}
              placeholder="描述你想要的修改，例如：'请把主角的性格改成更勇敢、更有领导力' 或 '添加一个反派角色叫黑影'"
              rows={3}
            />
            {aiError && <p className={styles.aiError}>{aiError}</p>}
            <button
              className={styles.aiBtn}
              onClick={handleAiAssist}
              disabled={aiLoading || !aiInstruction.trim()}
            >
              {aiLoading ? 'AI 思考中...' : 'AI 辅助修改'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
