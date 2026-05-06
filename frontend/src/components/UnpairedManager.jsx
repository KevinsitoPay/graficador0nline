import { useState, useEffect } from 'react';

export default function UnpairedManager({ initialData }) {
  const [brackets, setBrackets] = useState(initialData?.brackets || []);
  const [unpaired, setUnpaired] = useState(initialData?.unpaired || []);
  const [recommendations, setRecommendations] = useState([]);
  const [history, setHistory] = useState([]);
  const [selectedCompetitor, setSelectedCompetitor] = useState(null);
  const [loading, setLoading] = useState(false);
  const [draggedCompetitor, setDraggedCompetitor] = useState(null);
  const [dropTarget, setDropTarget] = useState(null);

  const fetchRecommendations = async (competitorId) => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/recommendations/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          brackets,
          unpaired
        })
      });

      const data = await response.json();
      if (data.success) {
        setRecommendations((data.recommendations || []).filter(r => r.competidor.id === competitorId));
      } else {
        console.error('Recommendation error:', data.message);
      }
    } catch (e) {
      console.error('Error fetching recommendations:', e);
    }
    setLoading(false);
  };

  const handleCompetitorClick = (competitor) => {
    setSelectedCompetitor(competitor);
    fetchRecommendations(competitor.id);
  };

  const applyRecommendation = async (rec) => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/recommendations/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recomendacion_id: rec.id,
          brackets,
          unpaired,
          usuario: 'colaborador'
        })
      });

      const data = await response.json();
      if (data.success) {
        setBrackets(data.brackets || []);
        setUnpaired(data.unpaired || []);
        setSelectedCompetitor(null);
        setRecommendations([]);
        fetchHistory();
      } else {
        console.error('Apply recommendation error:', data.message);
      }
    } catch (e) {
      console.error('Error applying recommendation:', e);
    }
    setLoading(false);
  };

  const manualAssign = async (competitor, bracketId) => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/manual_assign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          competidor: competitor,
          bracket_id: bracketId,
          brackets,
          unpaired,
          usuario: 'colaborador'
        })
      });

      const data = await response.json();
      if (data.success) {
        setBrackets(data.brackets || []);
        setUnpaired(data.unpaired || []);
        setSelectedCompetitor(null);
        fetchHistory();
      } else {
        console.error('Manual assign error:', data.message);
      }
    } catch (e) {
      console.error('Error in manual assign:', e);
    }
    setLoading(false);
  };

  const fetchHistory = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/history');
      const data = await response.json();
      if (data.success) {
        setHistory(data.history || []);
      }
    } catch (e) {
      console.error('Error fetching history:', e);
    }
  };

  const undoLast = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/undo', { method: 'POST' });
      const data = await response.json();
      if (data.success) {
        fetchHistory();
      } else {
        console.error('Undo error:', data.message);
      }
    } catch (e) {
      console.error('Error undoing:', e);
    }
  };

  const finalize = async () => {
    setLoading(true);
    try {
      const allCompetitors = [
        ...brackets.flatMap(b => b.competidores),
        ...unpaired.map(u => u.competidor)
      ];

      const response = await fetch('http://localhost:8000/api/finalize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          brackets,
          unpaired,
          competidores: allCompetitors
        })
      });

      const data = await response.json();
      if (data.success) {
        setBrackets(data.brackets || []);
        alert('Emparejamiento finalizado y exportado');
      } else {
        console.error('Finalize error:', data.message);
      }
    } catch (e) {
      console.error('Error finalizing:', e);
    }
    setLoading(false);
  };

  const exportPDF = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/export/pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          brackets,
          unpaired
        })
      });

      const data = await response.json();
      if (data.success) {
        alert(`PDF exportado: ${data.pdf_file}`);
      } else {
        console.error('PDF export error:', data.message);
      }
    } catch (e) {
      console.error('Error exporting PDF:', e);
    }
  };

  const handleDragStart = (e, competitor) => {
    setDraggedCompetitor(competitor);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e, bracketId) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDropTarget(bracketId);
  };

  const handleDragLeave = () => {
    setDropTarget(null);
  };

  const handleDrop = (e, bracketId) => {
    e.preventDefault();
    if (draggedCompetitor) {
      manualAssign(draggedCompetitor, bracketId);
    }
    setDraggedCompetitor(null);
    setDropTarget(null);
  };

  const getNivelColor = (nivel) => {
    const colors = ['#22c55e', '#84cc16', '#eab308', '#f97316', '#ef4444', '#991b1b'];
    return colors[nivel - 1] || '#22c55e';
  };

  if (!initialData) {
    return (
      <div className="unpaired-manager empty">
        <p>No hay datos disponibles. Sube un archivo Excel primero.</p>
      </div>
    );
  }

  return (
    <div className="unpaired-manager">
      <div className="manager-header">
        <h2>Gestión de Competidores Sin Rival</h2>
        <div className="manager-actions">
          <button onClick={undoLast} disabled={loading || history.filter(h => !h.reversed).length === 0}>
            Deshacer
          </button>
          <button onClick={finalize} disabled={loading}>
            Finalizar
          </button>
          <button onClick={exportPDF} disabled={loading}>
            Exportar PDF
          </button>
        </div>
      </div>

      <div className="manager-panels">
        <div className="unpaired-panel">
          <h3>Competidores Sin Rival ({unpaired.length})</h3>
          <div className="unpaired-list">
            {unpaired.map((item, idx) => (
              <div
                key={idx}
                className={`competitor-card draggable ${selectedCompetitor?.id === item.competidor.id ? 'selected' : ''}`}
                draggable
                onDragStart={(e) => handleDragStart(e, item.competidor)}
                onClick={() => handleCompetitorClick(item.competidor)}
              >
                <div className="comp-name">
                  {item.competidor.nombre} {item.competidor.apellido}
                </div>
                <div className="comp-details">
                  {item.competidor.edad} años • {item.competidor.peso_kg}kg • {item.competidor.cinta_block}
                </div>
                <div className="comp-doyang">{item.competidor.doyang}</div>
              </div>
            ))}
            {unpaired.length === 0 && (
              <p className="no-data">No hay competidores sin rival</p>
            )}
          </div>
        </div>

        <div className="brackets-panel">
          <h3>Brackets Existentes ({brackets.length})</h3>
          <div className="brackets-list">
            {brackets.map((bracket) => (
              <div
                key={bracket.id}
                className={`bracket-card-droppable ${dropTarget === bracket.id ? 'drag-over' : ''}`}
                onDragOver={(e) => handleDragOver(e, bracket.id)}
                onDragLeave={handleDragLeave}
                onDrop={(e) => handleDrop(e, bracket.id)}
              >
                <div className="bracket-header">
                  <span className="bracket-id">#{bracket.numero || bracket.id}</span>
                  <span className="bracket-score">{bracket.score}%</span>
                  <span className="bracket-level">
                    {bracket.nivel_aprobacion || 'auto'}
                  </span>
                </div>
                <div className="bracket-competitors">
                  {bracket.competidores.map((c, i) => (
                    <div key={i} className="bracket-comp">
                      {c.numero_competidor} {c.nombre} {c.apellido}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="recommendations-panel">
          <h3>Recomendaciones</h3>
          {selectedCompetitor ? (
            <div className="recommendations-list">
              {loading ? (
                <p>Cargando...</p>
              ) : recommendations.length > 0 ? (
                recommendations.map((rec, idx) => (
                  <div key={idx} className="recommendation-card">
                    <div className="rec-header">
                      <span className="rec-type">{rec.tipo}</span>
                      <span className="rec-score">{rec.score_esperado}%</span>
                      <span
                        className="rec-nivel"
                        style={{ backgroundColor: getNivelColor(rec.nivel_relajacion) }}
                      >
                        Nivel {rec.nivel_relajacion}
                      </span>
                    </div>
                    <div className="rec-justification">{rec.justificacion}</div>
                    <div className="rec-limits">
                      Peso: {rec.limites_usados.peso}kg |
                      Edad Inf: {rec.limites_usados.edad_inf}a |
                      Edad Adulto: {rec.limites_usados.edad_adulto}a |
                      Est: {rec.limites_usados.estatura}cm
                    </div>
                    <button onClick={() => applyRecommendation(rec)}>
                      Aplicar
                    </button>
                  </div>
                ))
              ) : (
                <p className="no-data">No hay recomendaciones disponibles</p>
              )}
            </div>
          ) : (
            <p className="placeholder">Selecciona un competidor para ver recomendaciones</p>
          )}
        </div>

        <div className="history-panel">
          <h3>Historial ({history.length})</h3>
          <div className="history-list">
            {history.slice().reverse().map((action, idx) => (
              <div key={idx} className={`history-item ${action.reversed ? 'reversed' : ''}`}>
                <span className="history-type">{action.tipo}</span>
                <span className="history-time">
                  {new Date(action.timestamp).toLocaleTimeString()}
                </span>
              </div>
            ))}
            {history.length === 0 && (
              <p className="no-data">Sin acciones registradas</p>
            )}
          </div>
        </div>
      </div>

      <style>{`
        .unpaired-manager {
          margin-top: 24px;
          padding: 20px;
          background: #fff;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .unpaired-manager.empty {
          text-align: center;
          color: #666;
        }
        .manager-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          padding-bottom: 16px;
          border-bottom: 1px solid #e5e5e5;
        }
        .manager-header h2 {
          margin: 0;
          color: #1a1a2e;
        }
        .manager-actions {
          display: flex;
          gap: 8px;
        }
        .manager-actions button {
          padding: 8px 16px;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-weight: 500;
          transition: all 0.2s;
        }
        .manager-actions button:first-child {
          background: #f59e0b;
          color: white;
        }
        .manager-actions button:nth-child(2) {
          background: #22c55e;
          color: white;
        }
        .manager-actions button:nth-child(3) {
          background: #1a1a2e;
          color: white;
        }
        .manager-actions button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .manager-panels {
          display: grid;
          grid-template-columns: 1fr 1fr 1fr 1fr;
          gap: 16px;
        }
        .unpaired-panel, .brackets-panel, .recommendations-panel, .history-panel {
          padding: 16px;
          background: #f9fafb;
          border-radius: 8px;
        }
        .unpaired-panel h3, .brackets-panel h3, .recommendations-panel h3, .history-panel h3 {
          margin: 0 0 12px 0;
          font-size: 14px;
          color: #374151;
        }
        .competitor-card {
          padding: 10px;
          margin-bottom: 8px;
          background: white;
          border-radius: 6px;
          border: 1px solid #e5e5e5;
          cursor: pointer;
          transition: all 0.2s;
        }
        .competitor-card:hover {
          border-color: #3b82f6;
        }
        .competitor-card.selected {
          border-color: #3b82f6;
          background: #eff6ff;
        }
        .competitor-card.draggable {
          cursor: grab;
        }
        .competitor-card.draggable:active {
          cursor: grabbing;
        }
        .comp-name {
          font-weight: 600;
          color: #1a1a2e;
        }
        .comp-details {
          font-size: 12px;
          color: #6b7280;
          margin-top: 4px;
        }
        .comp-doyang {
          font-size: 11px;
          color: #9ca3af;
          margin-top: 2px;
        }
        .bracket-card-droppable {
          padding: 12px;
          margin-bottom: 8px;
          background: white;
          border-radius: 6px;
          border: 2px dashed #d1d5db;
          transition: all 0.2s;
        }
        .bracket-card-droppable.drag-over {
          border-color: #3b82f6;
          background: #eff6ff;
        }
        .bracket-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
        }
        .bracket-id {
          font-weight: 600;
          color: #1a1a2e;
        }
        .bracket-score {
          font-size: 12px;
          color: #22c55e;
        }
        .bracket-level {
          font-size: 10px;
          padding: 2px 6px;
          border-radius: 4px;
          color: white;
          background: #334155;
        }
        .bracket-competitors {
          font-size: 12px;
          color: #6b7280;
        }
        .bracket-comp {
          padding: 4px 0;
        }
        .recommendation-card {
          padding: 12px;
          margin-bottom: 8px;
          background: white;
          border-radius: 6px;
          border: 1px solid #e5e5e5;
        }
        .rec-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
        }
        .rec-type {
          font-weight: 600;
          text-transform: capitalize;
          color: #1a1a2e;
        }
        .rec-score {
          color: #22c55e;
          font-weight: 600;
        }
        .rec-nivel {
          font-size: 10px;
          padding: 2px 6px;
          border-radius: 4px;
          color: white;
        }
        .rec-justification {
          font-size: 12px;
          color: #6b7280;
          margin-bottom: 8px;
        }
        .rec-limits {
          font-size: 10px;
          color: #9ca3af;
          margin-bottom: 8px;
        }
        .recommendation-card button {
          width: 100%;
          padding: 8px;
          background: #3b82f6;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-weight: 500;
        }
        .recommendation-card button:hover {
          background: #2563eb;
        }
        .history-item {
          padding: 8px;
          margin-bottom: 4px;
          background: white;
          border-radius: 4px;
          font-size: 12px;
        }
        .history-item.reversed {
          opacity: 0.5;
          text-decoration: line-through;
        }
        .history-type {
          font-weight: 500;
          color: #1a1a2e;
        }
        .history-time {
          color: #9ca3af;
          margin-left: 8px;
        }
        .placeholder, .no-data {
          text-align: center;
          color: #9ca3af;
          font-size: 12px;
          padding: 20px;
        }
        @media (max-width: 1200px) {
          .manager-panels {
            grid-template-columns: 1fr 1fr;
          }
        }
        @media (max-width: 768px) {
          .manager-panels {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
}
