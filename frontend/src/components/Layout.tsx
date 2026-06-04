import { Outlet, Link } from 'react-router-dom';
import styles from './Layout.module.css';

export function Layout() {
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
