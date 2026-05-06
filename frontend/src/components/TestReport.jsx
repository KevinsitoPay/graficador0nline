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
        const fixtures = Array.isArray(data.report?.fixtures) ? data.report.fixtures : [];
        setProgressTotal(fixtures.length);
        setProgressCurrent(fixtures.length);

        const reportWithType = {
          ...data.report,
          testType: 'static',
          fixtures: fixtures.map((f, i) => ({
            ...f,
            type: 'Static',
            index: i
          }))
        };

        setReport(reportWithType);
      } else {
        setError(data.message || 'La API respondió con error.');
      }
    } catch (err) {
      console.error(err);
      setError(err?.message || 'Error procesando la respuesta de la API');
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
        const tests = Array.isArray(data.report?.tests) ? data.report.tests : [];
        setProgressCurrent(tests.length || count);

        const reportWithType = {
          ...data.report,
          testType: 'random',
          tests: tests.map((t, i) => ({
            ...t,
            type: 'Random',
            index: i
          }))
        };

        setReport(reportWithType);
      } else {
        setError(data.message || 'La API respondió con error.');
      }
    } catch (err) {
      console.error(err);
      setError(err?.message || 'Error procesando la respuesta de la API');
    } finally {
      setLoading(false);
    }
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
        setError(data.message || 'La API respondió con error.');
      }
    } catch (err) {
      console.error(err);
      setError(err?.message || 'Error procesando la respuesta de la API');
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

    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `test_report_${testType}_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const downloadUnpaired = () => {
    if (!report) return;

    const unpairedData = [];

    if (report.tests) {
      report.tests.forEach((test) => {
        if (test.unpaired && test.unpaired.length > 0) {
          test.unpaired.forEach((comp) => {
            unpairedData.push({
              test_name: test.name,
              ...comp
            });
          });
        }
      });
    } else if (report.fixtures) {
      report.fixtures.forEach((fixture) => {
        if (fixture.unpaired && fixture.unpaired.length > 0) {
          fixture.unpaired.forEach((comp) => {
            unpairedData.push({
              fixture_name: fixture.name,
              ...comp
            });
          });
        }
      });
    }

    if (unpairedData.length === 0) {
      alert('No hay competidores sin rival para exportar');
      return;
    }

    const blob = new Blob([JSON.stringify(unpairedData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `sin_rival_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const downloadLLMReport = () => {
    if (!report || !report.markdown) return;

    const blob = new Blob([report.markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `llm_report_${Date.now()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const copyLLMReport = async () => {
    if (!report || !report.markdown) return;

    try {
      await navigator.clipboard.writeText(report.markdown);
      alert('Reporte copiado al portapapeles');
    } catch (err) {
      console.error('Error al copiar:', err);
      alert('Error al copiar el reporte');
    }
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
            <p>Ejecutando pruebas...</p>
            {progressTotal > 0 && (
              <p className="progress-text">Prueba {progressCurrent} de {progressTotal}</p>
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
        <h3>Reporte de Pruebas</h3>
        <p>Ejecuta pruebas para evaluar el algoritmo.</p>

        <details className="scoring-guide">
          <summary>📖 Explicación del Algoritmo (Cómo Funciona)</summary>
          <div className="algorithm-content">
            <p>Este panel ejecuta pruebas contra el backend para medir emparejamiento, calidad y tiempos.</p>
          </div>
        </details>

        <div className="test-controls">
          <button onClick={runStaticTests} disabled={loading}>
            Ejecutar Pruebas Estáticas
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
              Ejecutar {randomCount} Pruebas Aleatorias{randomCount !== 1 ? 's' : ''}
            </button>
          </div>
          <button onClick={() => runLLMReport(randomCount)} className="llm-btn" disabled={loading}>
            Exportar para LLM ({randomCount})
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
            <>
              <button onClick={downloadReport} className="export-btn" disabled={!report}>
                Exportar JSON
              </button>
              <button onClick={downloadUnpaired} className="export-btn" disabled={!report}>
                Exportar Sin Rival
              </button>
            </>
          )}
          {isLLMReport && (
            <>
              <button onClick={copyLLMReport} className="export-btn copy-btn" disabled={!report}>
                Copiar Reporte
              </button>
              <button onClick={downloadLLMReport} className="export-btn llm-export" disabled={!report}>
                Descargar Markdown
              </button>
            </>
          )}
        </div>
      </div>

      <div className="test-controls">
        <button onClick={runStaticTests} disabled={loading}>
          Ejecutar Pruebas Estáticas
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
            Ejecutar {randomCount} Pruebas Aleatorias{randomCount !== 1 ? 's' : ''}
          </button>
        </div>
        <button onClick={() => runLLMReport(randomCount)} className="llm-btn" disabled={loading}>
          Export for LLM ({randomCount})
        </button>
      </div>

      <div className="timestamp">
        Generado: {report?.timestamp}
      </div>

      {error && <div className="error">{error}</div>}

      <div className="tabs">
        <button className={view === 'summary' ? 'active' : ''} onClick={() => setView('summary')}>
          Resumen
        </button>
        <button className={view === 'details' ? 'active' : ''} onClick={() => setView('details')}>
          Todas las Pruebas ({fixtures.length})
        </button>
        <button className={view === 'issues' ? 'active' : ''} onClick={() => setView('issues')}>
          Problemas ({fixtures.filter(f => f.status !== 'success').length})
        </button>
      </div>

      {view === 'summary' && (
        <div className="summary-view">
          <div className="stats-grid">
            <div className="stat-box">
              <span className="stat-value">{summary.total_runs ?? 0}</span>
              <span className="stat-label">Total de Pruebas</span>
            </div>
            <div className="stat-box success">
              <span className="stat-value">{summary.successful ?? 0}</span>
              <span className="stat-label">Exitosas</span>
            </div>
            <div className="stat-box failed">
              <span className="stat-value">{summary.failed ?? 0}</span>
              <span className="stat-label">Fallidas</span>
            </div>
            <div className="stat-box">
              <span className="stat-value">{summary.avg_pairing_rate ?? 0}%</span>
              <span className="stat-label">Emparej. Promedio</span>
            </div>
            <div className="stat-box">
              <span className="stat-value">{summary.avg_quality_rate ?? 0}%</span>
              <span className="stat-label">Calidad Promedio</span>
            </div>
            <div className="stat-box">
              <span className="stat-value">{summary.avg_time ?? 0}s</span>
              <span className="stat-label">Tiempo Promedio</span>
            </div>
            <div className="stat-box">
              <span className="stat-value">{summary.avg_brackets_2 ?? summary.brackets_2 ?? 0}</span>
              <span className="stat-label">Gráf. 2 Prom.</span>
            </div>
            <div className="stat-box">
              <span className="stat-value">{summary.avg_brackets_3 ?? summary.brackets_3 ?? 0}</span>
              <span className="stat-label">Gráf. 3 Prom.</span>
            </div>
            <div className="stat-box">
              <span className="stat-value">{summary.avg_brackets_4 ?? summary.brackets_4 ?? 0}</span>
              <span className="stat-label">Gráf. 4 Prom.</span>
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
                <th>Tipo</th>
                <th>Prueba</th>
                <th>Comp</th>
                <th>Gráficas</th>
                <th>Emparej%</th>
                <th>Calidad%</th>
                <th>Tiempo</th>
                <th>Sin Rival</th>
                <th>×2</th>
                <th>×3</th>
                <th>×4</th>
                <th>Estado</th>
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
                    <td>{f.total_competitors ?? '-'}</td>
                    <td>{f.total_brackets ?? '-'}</td>
                    <td>{f.pairing_rate ?? '-'}</td>
                    <td>{f.quality_rate ?? '-'}</td>
                    <td>{f.elapsed ? `${f.elapsed}s` : '-'}</td>
                    <td>{f.sin_rival ?? '-'}</td>
                    <td>{f.brackets_2 ?? '-'}</td>
                    <td>{f.brackets_3 ?? '-'}</td>
                    <td>{f.brackets_4 ?? '-'}</td>
                    <td className={f.status === 'success' ? 'status-ok' : 'status-err'}>
                      {f.status}
                    </td>
                  </tr>

                  {expandedRow === i && Array.isArray(f.brackets) && (
                    <tr className="expanded-content">
                      <td colSpan={13}>
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
                                    <span className="comp-num">{c.numero_competidor}</span>
                                    <span className="comp-name">{c.nombre} {c.apellido}</span>
                                    <span className="belt-badge" style={{ backgroundColor: getBeltColor(c.cinta_block) }} title={c.cinta_block}></span>
                                    <span className="edad-category">{getEdadCategoryDisplay(c.edad)}</span>
                                    <span className="comp-info">
                                      {c.edad} años • {c.peso_kg} kg • {c.estatura_cm} cm • {c.modalidad} • {c.doyang}
                                    </span>
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
                                        <td className="diff">Penalización</td>
                                        <td>-{b.score_breakdown.doyang_penalty || 0} pts</td>
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

                          {Array.isArray(f.unpaired) && f.unpaired.length > 0 && (
                            <div className="unpaired-section">
                              <h4>Sin Rival ({f.unpaired.length})</h4>
                              {f.unpaired.map((u, ui) => (
                                <div key={ui} className="unpaired-item">
                                  <span className="belt-badge" style={{ backgroundColor: getBeltColor(u.cinta_block) }} title={u.cinta_block}></span>
                                  <span>{u.nombre} {u.apellido}</span>
                                  <span>{u.edad} años • {u.peso_kg ?? u.peso} kg</span>
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
            <p className="no-issues">¡No se encontraron problemas!</p>
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
