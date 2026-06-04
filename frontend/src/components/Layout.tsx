import { Outlet, Link, useLocation } from 'react-router-dom';
import styles from './Layout.module.css';

const STAGES = [
  { key: 'chapter_splitting', label: 'Upload' },
  { key: 'character_extraction', label: 'Characters' },
  { key: 'scene_analysis', label: 'Scenes' },
  { key: 'episode_structuring', label: 'Episodes' },
  { key: 'script_assembly', label: 'Script' },
];

export function Layout() {
  const location = useLocation();

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <Link to="/" className={styles.logo}>Novel2Scenario</Link>
        <span className={styles.subtitle}>AI 小说转剧本工具</span>
      </header>
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  );
}
