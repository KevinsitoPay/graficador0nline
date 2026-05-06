import { useState } from 'react';

const API_URL = import.meta.env.PUBLIC_API_URL || 'http://localhost:8000';

export default function UploadForm({ onResults }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    const selected = e.target.files[0];

    if (
      selected &&
      (
        selected.name.toLowerCase().endsWith('.xlsx') ||
        selected.name.toLowerCase().endsWith('.xls')
      )
    ) {
      setFile(selected);
      setError(null);
    } else {
      setFile(null);
      setError('Por favor selecciona un archivo .xlsx o .xls');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!file) {
      setError('Selecciona un archivo');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (data.success) {
        onResults(data.results);
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError('Error de conexión. ¿Está ejecutándose el backend?');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="upload-form">
      <form onSubmit={handleSubmit}>
        <div className="file-input">
          <input
            type="file"
            accept=".xlsx,.xls"
            onChange={handleFileChange}
            id="file-upload"
          />
          <label htmlFor="file-upload" className="file-label">
            {file ? file.name : 'Seleccionar archivo Excel (.xlsx o .xls)'}
          </label>
        </div>

        <button type="submit" disabled={loading || !file}>
          {loading ? 'Procesando...' : 'Procesar'}
        </button>
      </form>

      {error && <div className="error">{error}</div>}
    </div>
  );
}
