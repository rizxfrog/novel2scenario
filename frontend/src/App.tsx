import { BrowserRouter, Routes, Route } from 'react-router-dom';

function Home() {
  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>Novel2Scenario</h1>
      <p>AI 小说转剧本工具 - Frontend scaffold ready</p>
    </div>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
      </Routes>
    </BrowserRouter>
  );
}
