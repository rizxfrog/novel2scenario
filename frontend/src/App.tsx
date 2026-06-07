import { JobProvider } from './context/JobContext';
import { PipelineView } from './components/PipelineView';

export function App() {
  return (
    <JobProvider>
      <PipelineView />
    </JobProvider>
  );
}
