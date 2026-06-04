import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';

function UploadPage() {
  return (
    <div>
      <h2>Upload Novel</h2>
      <p>Upload page coming soon...</p>
    </div>
  );
}

function CharacterEditor() {
  return (
    <div>
      <h2>Character Editor</h2>
      <p>Character editor coming soon...</p>
    </div>
  );
}

function SceneEditor() {
  return (
    <div>
      <h2>Scene Editor</h2>
      <p>Scene editor coming soon...</p>
    </div>
  );
}

function EpisodePlanner() {
  return (
    <div>
      <h2>Episode Planner</h2>
      <p>Episode planner coming soon...</p>
    </div>
  );
}

function ScriptPreview() {
  return (
    <div>
      <h2>Script Preview</h2>
      <p>Script preview coming soon...</p>
    </div>
  );
}

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
          <Route path="*" element={<div>Page not found</div>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
