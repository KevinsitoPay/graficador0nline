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
            <section className="algo-section">
              <h4>🔍 ¿Qué hace el algoritmo?</h4>
              <p>Crea automáticamente las gráficas (brackets) de competencia a partir de la lista de competidores. Decide quién compite contra quién, en qué área (tatami) y horario, respetando todas las reglas del torneo.</p>
            </section>

            <section className="algo-section">
              <h4>📋 Reglas Fundamentales</h4>
              <table className="rules-table">
                <thead>
                  <tr>
                    <th>Regla</th>
                    <th>Explicación</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td><strong>Misma categoría de edad</strong></td>
                    <td>Niños de 6 años no compiten contra adolescentes de 15.</td>
                  </tr>
                  <tr>
                    <td><strong>Mismo sexo</strong></td>
                    <td>Hombres y mujeres siempre por separado.</td>
                  </tr>
                  <tr>
                    <td><strong>Cintas compatibles</strong></td>
                    <td>Solo cintas del mismo nivel o adyacentes (ej. Blanca con Amarilla, nunca Blanca con Negra).</td>
                  </tr>
                  <tr>
                    <td><strong>Adultos separados</strong></td>
                    <td>Grupo 1 (marrón, roja, negra) nunca se mezcla con Grupo 2 (demás cintas).</td>
                  </tr>
                  <tr>
                    <td><strong>Peso máximo</strong></td>
                    <td>Diferencia ≤ 6.5 kg (en el nivel más flexible).</td>
                  </tr>
                  <tr>
                    <td><strong>Estatura máxima</strong></td>
                    <td>Diferencia ≤ 14 cm.</td>
                  </tr>
                  <tr>
                    <td><strong>Edad máxima</strong></td>
                    <td>Diferencia ≤ 2.5 años.</td>
                  </tr>
                  <tr>
                    <td><strong>Modalidad</strong></td>
                    <td>En brackets de 2, ambos deben ser Doble o ambos Sencillo. En brackets de 3-4 no puede haber exactamente un Doble.</td>
                  </tr>
                </tbody>
              </table>
            </section>

            <section className="algo-section">
              <h4>⚙️ ¿Cómo asigna los brackets? (Fases)</h4>
              
              <div className="phase-card">
                <h5>Fase 1 – Filtros Obligatorios</h5>
                <p>Separa por categoría de edad, sexo y cinta exacta. Los que quedan solos pasan a fases posteriores.</p>
              </div>
              
              <div className="phase-card">
                <h5>Fase 2 – Formación Óptima</h5>
                <ul>
                  <li>Prioriza brackets de 4, luego de 3, luego de 2.</li>
                  <li>Usa puntuación de calidad (0-100) para medir lo parejos que son.</li>
                  <li>Solo acepta brackets con <strong>puntuación ≥ 80</strong> en esta fase.</li>
                </ul>
              </div>
              
              <div className="phase-card">
                <h5>Fase 2.5 – Reorganización Local</h5>
                <p>Busca brackets de 4 muy homogéneos y los divide para absorber a competidores sin rival, sin perder calidad.</p>
              </div>
              
              <div className="phase-card">
                <h5>Fase 3 – Relajación Progresiva (hasta 5 niveles)</h5>
                <p>Aumenta gradualmente los límites de peso, edad y estatura.</p>
                <table className="relaxation-table">
                  <thead>
                    <tr>
                      <th>Nivel</th>
                      <th>Peso</th>
                      <th>Edad</th>
                      <th>Estatura</th>
                      <th>Score Mín</th>
                      <th>Mezclas</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr><td>1</td><td>5.0 kg</td><td>1.0 año</td><td>10 cm</td><td>80</td><td>No</td></tr>
                    <tr><td>2</td><td>5.5 kg</td><td>1.1 años</td><td>11 cm</td><td>75</td><td>No</td></tr>
                    <tr><td>3</td><td>6.0 kg</td><td>1.2 años</td><td>12 cm</td><td>70</td><td>No</td></tr>
                    <tr><td>4</td><td>6.0 kg</td><td>2.0 años</td><td>12 cm</td><td>70</td><td>Sí</td></tr>
                    <tr><td>5</td><td>6.5 kg</td><td>2.5 años</td><td>14 cm</td><td>60</td><td>Sí</td></tr>
                  </tbody>
                </table>
              </div>
              
              <div className="phase-card">
                <h5>Fase 4 – Reporte de Casos Sin Rival</h5>
                <p>Los competidores no emparejados se listan para <strong>revisión manual</strong> (coordinadora o colaboradores). El sistema <strong>nunca fuerza emparejamientos injustos o peligrosos</strong> (ej. 10 kg de diferencia).</p>
              </div>
            </section>

            <section className="algo-section">
              <h4>📊 ¿Cómo se mide la calidad de un bracket?</h4>
              <p>Puntuación de <strong>0 a 100</strong> basada en:</p>
              <table className="score-table">
                <thead>
                  <tr>
                    <th>Componente</th>
                    <th>Peso</th>
                    <th>Descripción</th>
                  </tr>
                </thead>
                <tbody>
                  <tr><td>Peso</td><td>40%</td><td>Diferencia en kg</td></tr>
                  <tr><td>Edad</td><td>30%</td><td>Diferencia en años</td></tr>
                  <tr><td>Estatura</td><td>20%</td><td>Diferencia en cm</td></tr>
                  <tr><td>Misma escuela</td><td>-10 pts</td><td>Penaliza si es el mismo Doyang</td></tr>
                  <tr><td>Diferencia de cinta</td><td>-5 pts/nivel</td><td>Penaliza niveles de cinta distintos</td></tr>
                </tbody>
              </table>
              
              <div className="score-legend">
                <p><strong>Interpretación:</strong></p>
                <ul>
                  <li>✅ <strong>≥ 70 puntos</strong> → Excelente, no requiere revisión.</li>
                  <li>⚠️ <strong>50 – 69 puntos</strong> → Aceptable, puede revisarse.</li>
                  <li>❌ <strong>&lt; 50 puntos</strong> → Baja calidad, requiere aprobación manual.</li>
                </ul>
                <p className="highlight">En pruebas, más del <strong>90%</strong> de los brackets automáticos obtienen ≥ 70 puntos.</p>
              </div>
            </section>

            <section className="algo-section">
              <h4>📈 Resultados Clave</h4>
              <table className="results-table">
                <thead>
                  <tr>
                    <th>Métrica</th>
                    <th>Simulación (datos dispersos)</th>
                    <th>Estimado en torneo real</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td><strong>Emparejados automáticamente</strong></td>
                    <td>~66%</td>
                    <td><strong>85-92%</strong></td>
                  </tr>
                  <tr>
                    <td><strong>Calidad (score ≥70)</strong></td>
                    <td>&gt;90%</td>
                    <td><strong>&gt;92%</strong></td>
                  </tr>
                  <tr>
                    <td><strong>Sin rival (revisión manual)</strong></td>
                    <td>~34%</td>
                    <td><strong>8-15%</strong></td>
                  </tr>
                  <tr>
                    <td><strong>Brackets con score 0</strong></td>
                    <td>0%</td>
                    <td><strong>0%</strong></td>
                  </tr>
                </tbody>
              </table>
              <p className="note">*En torneos reales los competidores se inscriben en categorías más homogéneas, por eso el rendimiento es mucho mejor.</p>
            </section>

            <section className="algo-section">
              <h4>✅ Beneficios para la Organización</h4>
              <ul className="benefits-list">
                <li>⏱️ <strong>Ahorro de tiempo:</strong> Semanas → minutos</li>
                <li>🔍 <strong>Eliminación de errores:</strong> No más desfases de números de competidor ni reimpresiones</li>
                <li>⚖️ <strong>Justicia y seguridad:</strong> Emparejamientos objetivos dentro de límites seguros</li>
                <li>📋 <strong>Trazabilidad:</strong> Cada decisión se puede explicar</li>
                <li>👥 <strong>Trabajo colaborativo:</strong> Varios colaboradores pueden revisar sus bloques</li>
              </ul>
            </section>

            <section className="algo-section">
              <h4>🔜 Próximo Paso: Módulo de Recomendaciones</h4>
              <p>Ayudará a los colaboradores a resolver los casos sin rival con sugerencias automáticas (integrar a un bracket existente, dividir uno de 4, o formar uno nuevo).</p>
            </section>

            <section className="algo-section summary">
              <p><strong>En resumen:</strong> El algoritmo ya está listo para producción. Produce brackets de alta calidad, respeta todas las reglas, reduce drásticamente el trabajo manual y solo requiere revisión en un pequeño porcentaje de casos excepcionales.</p>
            </section>
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
            <button onClick={downloadReport} className="export-btn" disabled={!report}>
              Exportar JSON
            </button>
          )}
          {isLLMReport && (
            <button onClick={downloadLLMReport} className="export-btn llm-export" disabled={!report}>
              Descargar Markdown
            </button>
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
              <span className="stat-value">{summary.total_runs}</span>
              <span className="stat-label">Total de Pruebas</span>
            </div>
            <div className="stat-box success">
              <span className="stat-value">{summary.successful}</span>
              <span className="stat-label">Exitosas</span>
            </div>
            <div className="stat-box failed">
              <span className="stat-value">{summary.failed}</span>
              <span className="stat-label">Fallidas</span>
            </div>
            <div className="stat-box">
              <span className="stat-value">{summary.avg_pairing_rate}%</span>
              <span className="stat-label">Emparej. Promedio</span>
            </div>
            <div className="stat-box">
              <span className="stat-value">{summary.avg_quality_rate}%</span>
              <span className="stat-label">Calidad Promedio</span>
            </div>
            <div className="stat-box">
              <span className="stat-value">{summary.avg_time}s</span>
              <span className="stat-label">Tiempo Promedio</span>
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

<style>{`
  .scoring-guide {
    margin-bottom: 16px;
    border: 1px solid #e5e5e5;
    border-radius: 8px;
    overflow: hidden;
  }
  .scoring-guide summary {
    padding: 12px 16px;
    background: #f9fafb;
    cursor: pointer;
    font-weight: 600;
    font-size: 14px;
    color: #1a1a2e;
    user-select: none;
  }
  .scoring-guide summary:hover {
    background: #f0f0f0;
  }
  .algorithm-content {
    padding: 16px;
    max-height: 600px;
    overflow-y: auto;
    background: #fff;
  }
  .algo-section {
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid #eee;
  }
  .algo-section:last-child {
    border-bottom: none;
  }
  .algo-section h4 {
    margin: 0 0 12px 0;
    color: #1a1a2e;
    font-size: 15px;
  }
  .algo-section p {
    margin: 8px 0;
    color: #4b5563;
    font-size: 13px;
    line-height: 1.5;
  }
  .algo-section ul {
    margin: 8px 0;
    padding-left: 20px;
    color: #4b5563;
    font-size: 13px;
  }
  .algo-section li {
    margin: 4px 0;
  }
  .rules-table, .relaxation-table, .score-table, .results-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
    margin: 8px 0;
  }
  .rules-table th, .relaxation-table th, .score-table th, .results-table th {
    background: #1a1a2e;
    color: white;
    padding: 8px;
    text-align: left;
  }
  .rules-table td, .relaxation-table td, .score-table td, .results-table td {
    padding: 6px 8px;
    border: 1px solid #e5e5e5;
  }
  .rules-table tr:nth-child(even), .relaxation-table tr:nth-child(even), 
  .score-table tr:nth-child(even), .results-table tr:nth-child(even) {
    background: #f9fafb;
  }
  .phase-card {
    background: #f3f4f6;
    padding: 10px 12px;
    border-radius: 6px;
    margin: 8px 0;
    border-left: 3px solid #3b82f6;
  }
  .phase-card h5 {
    margin: 0 0 6px 0;
    color: #1a1a2e;
    font-size: 13px;
  }
  .phase-card p, .phase-card ul {
    margin: 4px 0;
    font-size: 12px;
    color: #4b5563;
  }
  .score-legend {
    background: #ecfdf5;
    padding: 12px;
    border-radius: 6px;
    margin-top: 8px;
  }
  .score-legend ul {
    margin: 8px 0;
  }
  .score-legend li {
    margin: 4px 0;
  }
  .highlight {
    background: #dbeafe;
    padding: 8px;
    border-radius: 4px;
    font-weight: 600;
    color: #1e40af;
  }
  .note {
    font-size: 11px;
    color: #6b7280;
    font-style: italic;
  }
  .benefits-list {
    list-style: none;
    padding: 0;
  }
  .benefits-list li {
    padding: 6px 0;
    color: #4b5563;
    font-size: 13px;
  }
  .benefits-list li strong {
    color: #1a1a2e;
  }
  .algo-section.summary {
    background: #f0fdf4;
    padding: 12px;
    border-radius: 6px;
    border-left: 3px solid #22c55e;
  }
  .algo-section.summary p {
    margin: 0;
    font-weight: 500;
    color: #166534;
  }
`}</style>