import { useState, useEffect } from 'react';
import UploadForm from './UploadForm';
import ResultsPanel from './ResultsPanel';

export default function App() {
  const [results, setResults] = useState(null);
  const [key, setKey] = useState(0);

  const handleResults = (data) => {
    setResults(data);
    setKey(k => k + 1);
  };

  return (
    <div className="app-wrapper">
      <UploadForm onResults={handleResults} />
      {results && <ResultsPanel key={key} initialResults={results} />}
      
      <style>{`
        .app-wrapper {
          margin-top: 24px;
        }
      `}</style>
    </div>
  );
}