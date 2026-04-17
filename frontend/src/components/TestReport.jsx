import { useState, useEffect } from 'react';

const BELT_COLORS = {
  "Negra (Dan)": "#1a1a1a",
  "Negra (Poom)": "#1a1a1a",
  "Roja": "#dc3545",
  "Marrón": "#8B4513",
  "Azul": "#007bff",
  "Verde": "#28a745",
  "Amarilla": "#ffc107",
  "Blanca": "#f8f9fa",
  "Pre-Taekwondo": "#6f42c1",
  "Desconocido": "#6c757d"
};

const EDAD_CATEGORY_DISPLAY = {
  "preescolar": "PREESCOLAR",
  "infantil": "INFANTIL",
  "cadete": "CADETE",
  "juvenil": "JUVENIL",
  "adulto": "ADULTO",
  "submaster": "SUBMASTER",
  "master": "MASTER"
};

function getBeltColor(cintaBlock) {
  return BELT_COLORS[cintaBlock] || "#999";
}

function getEdadCategoryDisplay(edad) {
  if (edad <= 5) return "PREESCOLAR";
  if (edad <= 13) return "INFANTIL";
  if (edad <= 15) return "CADETE";
  if (edad <= 17) return "JUVENIL";
  if (edad <= 29) return "ADULTO";
  if (edad <= 45) return "SUBMASTER";
  return "MASTER";
}

export default function TestReport() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [view, setView] = useState('summary');
  const [testType, setTestType] = useState(null);
  const [expandedRow, setExpandedRow] = useState(null);
  const [randomCount, setRandomCount] = useState(25);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [progressCurrent, setProgressCurrent] = useState(0);
  const [progressTotal, setProgressTotal] = useState(0);

  const runStaticTests = async () => {
    setLoading(true);
    setError(null);
    setTestType('static');
    setExpandedRow(null);
    setProgressTotal(0);
    setProgressCurrent(0);
    
    try {
      const res = await fetch('http://localhost:8000/tests');
      const data = await res.json();
      
      if (data.success) {
        const totalFixtures = data.report.fixtures?.length || 0;
        setProgressTotal(totalFixtures);
        
        const reportWithType = {
          ...data.report,
          testType: 'static',
          fixtures: data.report.fixtures.map((f, i) => {
            setProgressCurrent(i + 1);
            return {...f, type: 'Static', index: i};
          })
        };
        setReport(reportWithType);
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError('Error connecting to API');
    } finally {
      setLoading(false);
    }
  };

  const runRandomTests = async (count) => {
    setLoading(true);
    setError(null);
    setTestType('random');
    setExpandedRow(null);
    setProgressTotal(count);
    setProgressCurrent(0);
    
    try {
      const res = await fetch(`http://localhost:8000/tests/random/${count}`);
      const data = await res.json();
      
      if (data.success) {
        const reportWithType = {
          ...data.report,
          testType: 'random',
          tests: data.report.tests.map((t, i) => {
            setProgressCurrent(i + 1);
            return {...t, type: 'Random', index: i};
          })
        };
        setReport(reportWithType);
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError('Error connecting to API');
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = () => {
    if (!report) return;
    
    const reportData = {
      ...report,
      generatedAt: new Date().toISOString(),
      reportType: testType
    };
    
    const blob = new Blob([JSON.stringify(reportData, null, 2)], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `test_report_${testType}_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const runLLMReport = async (count) => {
    setLoading(true);
    setError(null);
    setTestType('llm');
    setExpandedRow(null);
    
    try {
      const res = await fetch(`http://localhost:8000/tests/report/llm/${count}`);
      const data = await res.json();
      
      if (data.success) {
        setReport(data.report);
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError('Error connecting to API');
    } finally {
      setLoading(false);
    }
  };

  const downloadLLMReport = () => {
    if (!report || !report.markdown) return;
    
    const blob = new Blob([report.markdown], {type: 'text/markdown'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `llm_report_${Date.now()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const toggleRow = (index) => {
    setExpandedRow(expandedRow === index ? null : index);
  };

  useEffect(() => {
    let interval;
    if (loading) {
      setElapsedTime(0);
      interval = setInterval(() => {
        setElapsedTime(t => t + 0.1);
      }, 100);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [loading]);

  if (loading) {
    const progress = progressTotal > 0 ? (progressCurrent / progressTotal) * 100 : null;
    return (
      <div className="test-report loading">
        <div className="loading-content">
          <div className="loading-info">
            <p>Running tests...</p>
            {progressTotal > 0 && (
              <p className="progress-text">Test {progressCurrent} of {progressTotal}</p>
            )}
          </div>
          <div className="loading-timer">{elapsedTime.toFixed(1)}s</div>
          {progress !== null && (
            <div className="progress-bar-container">
              <div className="progress-bar" style={{ width: `${progress}%` }}></div>
            </div>
          )}
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="test-report">
        <h3>Test Report</h3>
        <p>Run tests to evaluate the algorithm.</p>

        <details className="scoring-guide">
          <summary>Scoring Breakdown Guide</summary>
          <p>The compatibility score (0–100 pts) is computed as:</p>
          <pre>Total = 100 − (PesoPenalty + EdadPenalty + EstaturaPenalty + DoyangPenalty + CintaPenalty)</pre>
          <p>Penalties are calculated using: <code>penalty = max × (diff / threshold) ^ 1.8</code></p>
          <table className="scoring-table">
            <thead>
              <tr>
                <th>Component</th>
                <th>Max Penalty</th>
                <th>Threshold</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Peso</td>
                <td>40</td>
                <td>5 kg</td>
                <td>diff_peso / 5</td>
              </tr>
              <tr>
                <td>Edad</td>
                <td>30</td>
                <td>1 año</td>
                <td>diff_edad / 1</td>
              </tr>
              <tr>
                <td>Estatura</td>
                <td>20</td>
                <td>10 cm</td>
                <td>diff_estatura / 10</td>
              </tr>
              <tr>
                <td>Doyang</td>
                <td>10</td>
                <td>same doyang</td>
                <td>+10 if same doyang</td>
              </tr>
              <tr>
                <td>Cinta</td>
                <td>flexible</td>
                <td>nivel diff</td>
                <td>5 × |nivel_c1 − nivel_c2|</td>
              </tr>
            </tbody>
          </table>
          <p><strong>MAXIMUM = 100 pts</strong> (identical competitors + different doyang + same cinta level)</p>
          <p>Score thresholds:</p>
          <ul>
            <li>≥ 70 pts → Excelente (no approval needed)</li>
            <li>50–69 pts → Aceptable</li>
            <li>&lt; 50 pts → Bajo (may require approval)</li>
          </ul>
        </details>

        <div className="test-controls">
          <button onClick={runStaticTests} disabled={loading}>
            Run Static Tests
          </button>
          <div className="random-controls">
            <input
              type="number"
              min="1"
              max="100"
              value={randomCount}
              onChange={(e) => setRandomCount(Math.min(100, Math.max(1, parseInt(e.target.value) || 1)))}
              disabled={loading}
            />
            <button onClick={() => runRandomTests(randomCount)} className="random-btn" disabled={loading}>
              Run {randomCount} Random Test{randomCount !== 1 ? 's' : ''}
            </button>
          </div>
          <button onClick={() => runLLMReport(randomCount)} className="llm-btn" disabled={loading}>
            Export for LLM ({randomCount})
          </button>
        </div>
        
        {error && <div className="error">{error}</div>}
      </div>
    );
  }

  const fixtures = report?.tests || report?.fixtures || [];
  const summary = report?.summary || {};

  const isLLMReport = testType === 'llm' && report && report.markdown;

  return (
    <div className="test-report">
      <div className="header">
        <h3>Test Report {testType ? `(${testType === 'random' ? 'Random' : testType === 'llm' ? 'LLM Report' : 'Static'})` : ''}</h3>
        <div className="actions">
          {!isLLMReport && (
            <button onClick={downloadReport} className="export-btn" disabled={!report}>
              Export JSON
            </button>
          )}
          {isLLMReport && (
            <button onClick={downloadLLMReport} className="export-btn llm-export" disabled={!report}>
              Download Markdown
            </button>
          )}
        </div>
      </div>
      
      <div className="test-controls">
        <button onClick={runStaticTests} disabled={loading}>
          Run Static Tests
        </button>
        <div className="random-controls">
          <input
            type="number"
            min="1"
            max="100"
            value={randomCount}
            onChange={(e) => setRandomCount(Math.min(100, Math.max(1, parseInt(e.target.value) || 1)))}
            disabled={loading}
          />
          <button onClick={() => runRandomTests(randomCount)} className="random-btn" disabled={loading}>
            Run {randomCount} Random Test{randomCount !== 1 ? 's' : ''}
          </button>
        </div>
        <button onClick={() => runLLMReport(randomCount)} className="llm-btn" disabled={loading}>
          Export for LLM ({randomCount})
        </button>
      </div>
      
      <div className="timestamp">
        Generated: {report?.timestamp}
      </div>

      <div className="tabs">
        <button className={view === 'summary' ? 'active' : ''} onClick={() => setView('summary')}>
          Summary
        </button>
        <button className={view === 'details' ? 'active' : ''} onClick={() => setView('details')}>
          All Tests ({fixtures.length})
        </button>
        <button className={view === 'issues' ? 'active' : ''} onClick={() => setView('issues')}>
          Issues ({fixtures.filter(f => f.status !== 'success').length})
        </button>
      </div>

      {view === 'summary' && (
        <div className="summary-view">
          <div className="stats-grid">
            <div className="stat-box">
              <span className="stat-value">{summary.total_runs}</span>
              <span className="stat-label">Total Tests</span>
            </div>
            <div className="stat-box success">
              <span className="stat-value">{summary.successful}</span>
              <span className="stat-label">Successful</span>
            </div>
            <div className="stat-box failed">
              <span className="stat-value">{summary.failed}</span>
              <span className="stat-label">Failed</span>
            </div>
            <div className="stat-box">
              <span className="stat-value">{summary.avg_pairing_rate}%</span>
              <span className="stat-label">Avg Pairing</span>
            </div>
            <div className="stat-box">
              <span className="stat-value">{summary.avg_quality_rate}%</span>
              <span className="stat-label">Avg Quality</span>
            </div>
            <div className="stat-box">
              <span className="stat-value">{summary.avg_time}s</span>
              <span className="stat-label">Avg Time</span>
            </div>
          </div>
        </div>
      )}

      {view === 'details' && (
        <div className="details-view">
          <table>
            <thead>
              <tr>
                <th></th>
                <th title="Tipo de prueba: Estática (predefinida) o Aleatoria (generada)">Tipo</th>
                <th title="Nombre del caso de prueba">Prueba</th>
                <th title="Número total de competidores analizados">Comp</th>
                <th title="Número de gráficas generadas">Gráficas</th>
                <th title="Porcentaje de emparejamiento: % de competidores emparejados exitosamente">Emparej%</th>
                <th title="Porcentaje de calidad: % de gráficas con puntuación >= 70%">Calidad%</th>
                <th title="Tiempo de ejecución">Tiempo</th>
                <th title="Competidores sin rival">Sin Rival</th>
                <th title="Estado de la prueba: Aprobado o Fallido">Estado</th>
              </tr>
            </thead>
            <tbody>
              {fixtures.map((f, i) => (
                <>
                  <tr 
                    key={i} 
                    className={`${f.status !== 'success' ? 'error-row' : ''} ${expandedRow === i ? 'expanded' : ''}`}
                    onClick={() => toggleRow(i)}
                  >
                    <td className="expand-icon">{expandedRow === i ? '▼' : '▶'}</td>
                    <td className="type-col">{f.type}</td>
                    <td className="test-name">{f.name}</td>
                    <td>{f.total_competitors || '-'}</td>
                    <td>{f.total_brackets || '-'}</td>
                    <td>{f.pairing_rate || '-'}</td>
                    <td>{f.quality_rate || '-'}</td>
                    <td>{f.elapsed ? `${f.elapsed}s` : '-'}</td>
                    <td>{f.sin_rival || '-'}</td>
                    <td className={f.status === 'success' ? 'status-ok' : 'status-err'}>
                      {f.status}
                    </td>
                  </tr>
                  {expandedRow === i && f.brackets && (
                    <tr className="expanded-content">
                      <td colSpan={9}>
                        <div className="bracket-details">
                          <h4>Brackets ({f.brackets.length})</h4>
                          {f.brackets.map((b, bi) => (
                            <div key={bi} className={`bracket-item type-${b.tipo}`}>
                              <div className="bracket-header-info">
                                <span className="bracket-num">#{b.numero}</span>
                                <span className="bracket-area">Area {b.area}</span>
                                <span className={`bracket-type-badge ${b.tipo}`}>{b.tipo}</span>
                                <span className="bracket-score">Score: {b.score}</span>
                              </div>
<div className="competitor-list">
                                {b.competidores.map((c, ci) => (
                                  <div key={ci} className="competitor-detail">
                                    <span className="comp-num">{c.numero}</span>
                                    <span className="comp-name">{c.nombre} {c.apellido}</span>
                                    <span className="belt-badge" style={{backgroundColor: getBeltColor(c.cinta_block)}} title={c.cinta_block}></span>
                                    <span className="edad-category">{getEdadCategoryDisplay(c.edad)}</span>
                                    <span className="comp-info">{c.edad} años • {c.peso} kg • {c.estatura} cm • {c.modalidad} • {c.doyang}</span>
                                    <span className="comp-bloque">{c.bloque}</span>
                                  </div>
                                ))}
                              </div>
                              {b.score_breakdown && (
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
                                        <td className={b.score_breakdown.modalidad_ok ? 'score-ok' : 'score-bad'}>
                                          {b.score_breakdown.modalidad_ok ? 'Compatible' : 'Incompatible'}
                                        </td>
                                      </tr>
                                      <tr>
                                        <td>Edad</td>
                                        <td className="diff">±{b.score_breakdown.edad_diff} años</td>
                                        <td>{b.score_breakdown.edad_score} pts</td>
                                      </tr>
                                      <tr>
                                        <td>Peso</td>
                                        <td className="diff">±{b.score_breakdown.peso_diff} kg</td>
                                        <td>{b.score_breakdown.peso_score} pts</td>
                                      </tr>
                                      <tr>
                                        <td>Estatura</td>
                                        <td className="diff">±{b.score_breakdown.estatura_diff} cm</td>
                                        <td>{b.score_breakdown.estatura_score} pts</td>
                                      </tr>
                                      <tr>
                                        <td>Doyang</td>
                                        <td className="diff">
                                          {b.competidores.length > 1 && b.competidores[0].doyang !== b.competidores[1].doyang 
                                            ? 'Diferentes → +0.2' 
                                            : 'Mismo → +0'}
                                        </td>
                                        <td>+{b.score_breakdown.doyang_bonus} pts</td>
                                      </tr>
                                      <tr className="total-row">
                                        <td colSpan="2">Puntaje Total</td>
                                        <td className="total">{b.score_breakdown.total}</td>
                                      </tr>
                                    </tbody>
                                  </table>
                                </div>
                              )}
                            </div>
                          ))}
                          {f.unpaired && f.unpaired.length > 0 && (
                            <div className="unpaired-section">
                              <h4>Sin Rival ({f.unpaired.length})</h4>
                              {f.unpaired.map((u, ui) => (
                                <div key={ui} className="unpaired-item">
                                  <span>{u.nombre} {u.apellido}</span>
                                  <span>{u.edad} años • {u.peso} kg</span>
                                  <span>{u.doyang}</span>
                                  <span className="razon">{u.razon}</span>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {view === 'issues' && (
        <div className="issues-view">
          {fixtures.filter(f => f.status !== 'success').length === 0 ? (
            <p className="no-issues">No issues found!</p>
          ) : (
            <ul className="issues-list">
              {fixtures.filter(f => f.status !== 'success').map((f, i) => (
                <li key={i}>
                  <strong>[{f.type}] {f.name}</strong>: {f.error}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {isLLMReport && (
        <div className="llm-report-view">
          <pre className="llm-markdown">{report.markdown}</pre>
        </div>
      )}
    </div>
  );
}