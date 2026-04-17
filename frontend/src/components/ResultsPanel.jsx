import { useState } from 'react';
import UnpairedManager from './UnpairedManager';

export default function ResultsPanel({ initialResults = null }) {
  const [results, setResults] = useState(initialResults);
  const [activeTab, setActiveTab] = useState('stats');
  const [expandedBlock, setExpandedBlock] = useState(null);

  const handleResults = (data) => {
    setResults(data);
  };

  if (!results) {
    return (
      <div className="placeholder">
        <p>Sube un archivo Excel para ver los resultados</p>
      </div>
    );
  }

  const { global_stats, block_stats, brackets, unpaired } = results;

  return (
    <div className="results-panel">
      <div className="tabs">
        <button 
          className={activeTab === 'stats' ? 'active' : ''} 
          onClick={() => setActiveTab('stats')}
        >
          Estadísticas
        </button>
        <button 
          className={activeTab === 'brackets' ? 'active' : ''} 
          onClick={() => setActiveTab('brackets')}
        >
          Gráficas ({global_stats.total_brackets})
        </button>
        <button 
          className={activeTab === 'unpaired' ? 'active' : ''} 
          onClick={() => setActiveTab('unpaired')}
        >
          Sin Rival ({unpaired.length})
        </button>
        <button 
          className={activeTab === 'manage' ? 'active' : ''} 
          onClick={() => setActiveTab('manage')}
        >
          Gestión
        </button>
      </div>

      {activeTab === 'stats' && (
        <div className="stats-content">
          <div className="global-stats">
            <h3>Estadísticas Globales</h3>
            <div className="stats-grid">
              <div className="stat-box">
                <span className="stat-value">{global_stats.total_competidores}</span>
                <span className="stat-label">Total Competidores</span>
              </div>
              <div className="stat-box">
                <span className="stat-value">{global_stats.total_brackets}</span>
                <span className="stat-label">Total Gráficas</span>
              </div>
              <div className="stat-box">
                <span className="stat-value">{global_stats.avg_bracket_size}</span>
                <span className="stat-label">Tamaño Promedio</span>
              </div>
              <div className="stat-box">
                <span className="stat-value">{global_stats.sin_rival_total}</span>
                <span className="stat-label">Sin Rival</span>
              </div>
            </div>
          </div>

          <div className="bracket-sizes">
            <h4>Tamaño de Gráficas</h4>
            <div className="size-bars">
              <div>2: {global_stats.brackets_2}</div>
              <div>3: {global_stats.brackets_3}</div>
              <div>4: {global_stats.brackets_4}</div>
            </div>
          </div>

          <div className="quality">
            <h4>Calidad</h4>
            <p>Excelentes (≥70%): {global_stats.excellent_brackets}</p>
            <p>Bajas (&lt;50%): {global_stats.low_quality_brackets}</p>
          </div>

          <div className="block-table">
            <h3>Por Bloque</h3>
            <table>
              <thead>
                <tr>
                  <th>Bloque</th>
                  <th>Comp.</th>
                  <th>Gráf.</th>
                  <th>Prom.</th>
                  <th>Sin Rival</th>
                  <th>Relajadas</th>
                </tr>
              </thead>
              <tbody>
                {block_stats.map(bs => (
                  <tr key={bs.bloque}>
                    <td>{bs.bloque}</td>
                    <td>{bs.competidores}</td>
                    <td>{bs.brackets}</td>
                    <td>{bs.avg_size}</td>
                    <td>{bs.sin_rival}</td>
                    <td>{bs.relaxed_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'brackets' && (
        <div className="brackets-content">
          {block_stats.map(bs => (
            <div key={bs.bloque} className="block-section">
              <button 
                className="block-header"
                onClick={() => setExpandedBlock(expandedBlock === bs.bloque ? null : bs.bloque)}
              >
                <span>{bs.bloque}</span>
                <span>{bs.brackets} gráficas</span>
              </button>
              
              {expandedBlock === bs.bloque && (
                <div className="bracket-list">
                  {brackets.filter(b => b.competidores[0].bloque === bs.bloque).map(bracket => (
                    <div key={bracket.id} className={`bracket-card ${bracket.tipo}`}>
                      <div className="bracket-header">
                        <span className="bracket-number">#{bracket.numero}</span>
                        <span className="bracket-area">Área {bracket.area}</span>
                        <span className={`bracket-type ${bracket.tipo}`}>{bracket.tipo}</span>
                        <span className="bracket-score">{bracket.score}%</span>
                      </div>
                      <div className="competitors">
                        {bracket.competidores.map(comp => (
                          <div key={comp.id} className="competitor-item">
                            <div>
                              <span className="comp-num">{comp.numero_competidor}</span>
                              <span className="comp-name">{comp.nombre} {comp.apellido}</span>
                            </div>
                            <span className="comp-details">{comp.edad} años • {comp.peso_kg} kg • {comp.modalidad} • {comp.doyang}</span>
                          </div>
                        ))}
                      </div>
                      {bracket.score_breakdown && (
                        <div className="score-breakdown">
                          <div className="breakdown-title">Desglose de Puntuación</div>
                          <table className="breakdown-table">
                            <thead>
                              <tr>
                                <th>Criterio</th>
                                <th>Diferencia</th>
                                <th>Puntaje</th>
                              </tr>
                            </thead>
                            <tbody>
                              <tr>
                                <td>Modalidad</td>
                                <td className="diff">Misma → ✓</td>
                                <td className={bracket.score_breakdown.modalidad_ok ? 'score-ok' : 'score-bad'}>
                                  {bracket.score_breakdown.modalidad_ok ? 'Compatible' : 'Incompatible'}
                                </td>
                              </tr>
                              <tr>
                                <td>Edad</td>
                                <td className="diff">±{bracket.score_breakdown.edad_diff} años</td>
                                <td>{bracket.score_breakdown.edad_score} pts</td>
                              </tr>
                              <tr>
                                <td>Peso</td>
                                <td className="diff">±{bracket.score_breakdown.peso_diff} kg</td>
                                <td>{bracket.score_breakdown.peso_score} pts</td>
                              </tr>
                              <tr>
                                <td>Estatura</td>
                                <td className="diff">±{bracket.score_breakdown.estatura_diff} cm</td>
                                <td>{bracket.score_breakdown.estatura_score} pts</td>
                              </tr>
                              <tr>
                                <td>Doyang</td>
                                <td className="diff">
                                  {bracket.competidores.length > 1 && bracket.competidores[0].doyang !== bracket.competidores[1].doyang 
                                    ? 'Diferentes → +0.2' 
                                    : 'Mismo → +0'}
                                </td>
                                <td>+{bracket.score_breakdown.doyang_bonus} pts</td>
                              </tr>
                              <tr className="total-row">
                                <td colSpan="2">Puntaje Total</td>
                                <td className="total">{bracket.score_breakdown.total}</td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {activeTab === 'unpaired' && (
        <div className="unpaired-content">
          {unpaired.length === 0 ? (
            <p className="no-unpaired">No hay competidores sin rival</p>
          ) : (
            <table className="unpaired-table">
              <thead>
                <tr>
                  <th title="Nombre completo del competidor">Nombre</th>
                  <th title="Grupo por sexo y cinta">Bloque</th>
                  <th title="Años del competidor">Edad</th>
                  <th title="Peso en kilogramos">Peso</th>
                  <th title="Escuela o club">Doyang</th>
                  <th title="Por qué no se pudo emparejar con nadie">Razón</th>
                </tr>
              </thead>
              <tbody>
                {unpaired.map((item, idx) => (
                  <tr key={idx}>
                    <td>{item.competidor.nombre} {item.competidor.apellido}</td>
                    <td>{item.competidor.bloque}</td>
                    <td>{item.competidor.edad}</td>
                    <td>{item.competidor.peso_kg}</td>
                    <td>{item.competidor.doyang}</td>
                    <td>{item.razon}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {activeTab === 'manage' && (
        <UnpairedManager initialData={{ brackets, unpaired }} />
      )}
    </div>
  );
}