import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { UploadPage } from './pages/UploadPage';
import { CharacterEditor } from './pages/CharacterEditor';
import { SceneEditor } from './pages/SceneEditor';
import { EpisodePlanner } from './pages/EpisodePlanner';
import { ScriptPreview } from './pages/ScriptPreview';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<UploadPage />} />
          <Route path="job/:jobId/characters" element={<CharacterEditor />} />
          <Route path="job/:jobId/scenes" element={<SceneEditor />} />
          <Route path="job/:jobId/episodes" element={<EpisodePlanner />} />
          <Route path="job/:jobId/script" element={<ScriptPreview />} />
          <Route path="*" element={<div style={{ padding: 48, textAlign: 'center' }}>Page not found</div>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
