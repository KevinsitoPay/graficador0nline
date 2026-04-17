import{j as e}from"./jsx-runtime.TBa3i5EZ.js";import{r as l}from"./index.CVf8TyFT.js";function F({onResults:x}){const[n,g]=l.useState(null),[t,h]=l.useState(!1),[u,p]=l.useState(null),i=j=>{const d=j.target.files[0];d&&d.name.endsWith(".xlsx")?(g(d),p(null)):p("Por favor selecciona un archivo .xlsx")},f=async j=>{if(j.preventDefault(),!n){p("Selecciona un archivo");return}h(!0),p(null);const d=new FormData;d.append("file",n);try{const a=await(await fetch("http://localhost:8000/upload",{method:"POST",body:d})).json();a.success?x(a.results):p(a.message)}catch{p("Error de conexión. ¿Está ejecutándose el backend?")}finally{h(!1)}};return e.jsxs("div",{className:"upload-form",children:[e.jsxs("form",{onSubmit:f,children:[e.jsxs("div",{className:"file-input",children:[e.jsx("input",{type:"file",accept:".xlsx",onChange:i,id:"file-upload"}),e.jsx("label",{htmlFor:"file-upload",className:"file-label",children:n?n.name:"Seleccionar archivo Excel (.xlsx)"})]}),e.jsx("button",{type:"submit",disabled:t||!n,children:t?"Procesando...":"Procesar"})]}),u&&e.jsx("div",{className:"error",children:u})]})}function B({initialData:x}){const[n,g]=l.useState(x?.brackets||[]),[t,h]=l.useState(x?.unpaired||[]),[u,p]=l.useState([]),[i,f]=l.useState([]),[j,d]=l.useState(null),[o,a]=l.useState(!1),[m,y]=l.useState(null),[w,v]=l.useState(null),_=async s=>{a(!0);try{const c=await(await fetch("http://localhost:8000/api/recommendations/generate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({brackets:n,unpaired:t})})).json();c.success&&p(c.recommendations.filter(b=>b.competidor.id===s))}catch(r){console.error("Error fetching recommendations:",r)}a(!1)},S=s=>{d(s),_(s.id)},C=async s=>{a(!0);try{const c=await(await fetch("http://localhost:8000/api/recommendations/apply",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({recomendacion_id:s.id,brackets:n,unpaired:t,usuario:"colaborador"})})).json();c.success&&(g(c.brackets),h(c.unpaired),d(null),p([]),N())}catch(r){console.error("Error applying recommendation:",r)}a(!1)},E=async(s,r)=>{a(!0);try{const b=await(await fetch("http://localhost:8000/api/manual_assign",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({competidor:s,bracket_id:r,brackets:n,unpaired:t,usuario:"colaborador"})})).json();b.success&&(g(b.brackets),h(b.unpaired),d(null),N())}catch(c){console.error("Error in manual assign:",c)}a(!1)},N=async()=>{try{const r=await(await fetch("http://localhost:8000/api/history")).json();r.success&&f(r.history)}catch(s){console.error("Error fetching history:",s)}},P=async()=>{try{(await(await fetch("http://localhost:8000/api/undo",{method:"POST"})).json()).success&&N()}catch(s){console.error("Error undoing:",s)}},D=async()=>{a(!0);try{const s=[...n.flatMap(b=>b.competidores),...t.map(b=>b.competidor)],c=await(await fetch("http://localhost:8000/api/finalize",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({brackets:n,unpaired:t,competidores:s})})).json();c.success&&(g(c.brackets),alert("Emparejamiento finalizado y exportado"))}catch(s){console.error("Error finalizing:",s)}a(!1)},T=async()=>{try{const r=await(await fetch("http://localhost:8000/api/export/pdf",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({brackets:n,unpaired:t})})).json();r.success&&alert(`PDF exportado: ${r.pdf_file}`)}catch(s){console.error("Error exporting PDF:",s)}},z=(s,r)=>{y(r),s.dataTransfer.effectAllowed="move"},R=(s,r)=>{s.preventDefault(),s.dataTransfer.dropEffect="move",v(r)},q=()=>{v(null)},O=(s,r)=>{s.preventDefault(),m&&E(m,r),y(null),v(null)},k=s=>["#22c55e","#84cc16","#eab308","#f97316","#ef4444","#991b1b"][s-1]||"#22c55e";return x?e.jsxs("div",{className:"unpaired-manager",children:[e.jsxs("div",{className:"manager-header",children:[e.jsx("h2",{children:"Gestión de Competidores Sin Rival"}),e.jsxs("div",{className:"manager-actions",children:[e.jsx("button",{onClick:P,disabled:o||i.filter(s=>!s.reversed).length===0,children:"Deshacer"}),e.jsx("button",{onClick:D,disabled:o,children:"Finalizar"}),e.jsx("button",{onClick:T,disabled:o,children:"Exportar PDF"})]})]}),e.jsxs("div",{className:"manager-panels",children:[e.jsxs("div",{className:"unpaired-panel",children:[e.jsxs("h3",{children:["Competidores Sin Rival (",t.length,")"]}),e.jsxs("div",{className:"unpaired-list",children:[t.map((s,r)=>e.jsxs("div",{className:`competitor-card draggable ${j?.id===s.competidor.id?"selected":""}`,draggable:!0,onDragStart:c=>z(c,s.competidor),onClick:()=>S(s.competidor),children:[e.jsxs("div",{className:"comp-name",children:[s.competidor.nombre," ",s.competidor.apellido]}),e.jsxs("div",{className:"comp-details",children:[s.competidor.edad," años • ",s.competidor.peso_kg,"kg • ",s.competidor.cinta_block]}),e.jsx("div",{className:"comp-doyang",children:s.competidor.doyang})]},r)),t.length===0&&e.jsx("p",{className:"no-data",children:"No hay competidores sin rival"})]})]}),e.jsxs("div",{className:"brackets-panel",children:[e.jsxs("h3",{children:["Brackets Existentes (",n.length,")"]}),e.jsx("div",{className:"brackets-list",children:n.map(s=>e.jsxs("div",{className:`bracket-card-droppable ${w===s.id?"drag-over":""}`,onDragOver:r=>R(r,s.id),onDragLeave:q,onDrop:r=>O(r,s.id),children:[e.jsxs("div",{className:"bracket-header",children:[e.jsxs("span",{className:"bracket-id",children:["#",s.numero||s.id]}),e.jsxs("span",{className:"bracket-score",children:[s.score,"%"]}),e.jsx("span",{className:"bracket-level",style:{backgroundColor:k(s.nivel_aprobacion==="rojo_oscuro"?6:5)},children:s.nivel_aprobacion||"auto"})]}),e.jsx("div",{className:"bracket-competitors",children:s.competidores.map((r,c)=>e.jsxs("div",{className:"bracket-comp",children:[r.numero_competidor," ",r.nombre," ",r.apellido]},c))})]},s.id))})]}),e.jsxs("div",{className:"recommendations-panel",children:[e.jsx("h3",{children:"Recomendaciones"}),j?e.jsx("div",{className:"recommendations-list",children:o?e.jsx("p",{children:"Cargando..."}):u.length>0?u.map((s,r)=>e.jsxs("div",{className:"recommendation-card",children:[e.jsxs("div",{className:"rec-header",children:[e.jsx("span",{className:"rec-type",children:s.tipo}),e.jsxs("span",{className:"rec-score",children:[s.score_esperado,"%"]}),e.jsxs("span",{className:"rec-nivel",style:{backgroundColor:k(s.nivel_relajacion)},children:["Nivel ",s.nivel_relajacion]})]}),e.jsx("div",{className:"rec-justification",children:s.justificacion}),e.jsxs("div",{className:"rec-limits",children:["Peso: ",s.limites_usados.peso,"kg | Edad: ",s.limites_usados.edad,"a | Est: ",s.limites_usados.estatura,"cm"]}),e.jsx("button",{onClick:()=>C(s),children:"Aplicar"})]},r)):e.jsx("p",{className:"no-data",children:"No hay recomendaciones disponibles"})}):e.jsx("p",{className:"placeholder",children:"Selecciona un competidor para ver recomendaciones"})]}),e.jsxs("div",{className:"history-panel",children:[e.jsxs("h3",{children:["Historial (",i.length,")"]}),e.jsxs("div",{className:"history-list",children:[i.slice().reverse().map((s,r)=>e.jsxs("div",{className:`history-item ${s.reversed?"reversed":""}`,children:[e.jsx("span",{className:"history-type",children:s.tipo}),e.jsx("span",{className:"history-time",children:new Date(s.timestamp).toLocaleTimeString()})]},r)),i.length===0&&e.jsx("p",{className:"no-data",children:"Sin acciones registradas"})]})]})]}),e.jsx("style",{children:`
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
      `})]}):e.jsx("div",{className:"unpaired-manager empty",children:e.jsx("p",{children:"No hay datos disponibles. Sube un archivo Excel primero."})})}function G({initialResults:x=null}){const[n,g]=l.useState(x),[t,h]=l.useState("stats"),[u,p]=l.useState(null);if(!n)return e.jsx("div",{className:"placeholder",children:e.jsx("p",{children:"Sube un archivo Excel para ver los resultados"})});const{global_stats:i,block_stats:f,brackets:j,unpaired:d}=n;return e.jsxs("div",{className:"results-panel",children:[e.jsxs("div",{className:"tabs",children:[e.jsx("button",{className:t==="stats"?"active":"",onClick:()=>h("stats"),children:"Estadísticas"}),e.jsxs("button",{className:t==="brackets"?"active":"",onClick:()=>h("brackets"),children:["Gráficas (",i.total_brackets,")"]}),e.jsxs("button",{className:t==="unpaired"?"active":"",onClick:()=>h("unpaired"),children:["Sin Rival (",d.length,")"]}),e.jsx("button",{className:t==="manage"?"active":"",onClick:()=>h("manage"),children:"Gestión"})]}),t==="stats"&&e.jsxs("div",{className:"stats-content",children:[e.jsxs("div",{className:"global-stats",children:[e.jsx("h3",{children:"Estadísticas Globales"}),e.jsxs("div",{className:"stats-grid",children:[e.jsxs("div",{className:"stat-box",children:[e.jsx("span",{className:"stat-value",children:i.total_competidores}),e.jsx("span",{className:"stat-label",children:"Total Competidores"})]}),e.jsxs("div",{className:"stat-box",children:[e.jsx("span",{className:"stat-value",children:i.total_brackets}),e.jsx("span",{className:"stat-label",children:"Total Gráficas"})]}),e.jsxs("div",{className:"stat-box",children:[e.jsx("span",{className:"stat-value",children:i.avg_bracket_size}),e.jsx("span",{className:"stat-label",children:"Tamaño Promedio"})]}),e.jsxs("div",{className:"stat-box",children:[e.jsx("span",{className:"stat-value",children:i.sin_rival_total}),e.jsx("span",{className:"stat-label",children:"Sin Rival"})]})]})]}),e.jsxs("div",{className:"bracket-sizes",children:[e.jsx("h4",{children:"Tamaño de Gráficas"}),e.jsxs("div",{className:"size-bars",children:[e.jsxs("div",{children:["2: ",i.brackets_2]}),e.jsxs("div",{children:["3: ",i.brackets_3]}),e.jsxs("div",{children:["4: ",i.brackets_4]})]})]}),e.jsxs("div",{className:"quality",children:[e.jsx("h4",{children:"Calidad"}),e.jsxs("p",{children:["Excelentes (≥70%): ",i.excellent_brackets]}),e.jsxs("p",{children:["Bajas (<50%): ",i.low_quality_brackets]})]}),e.jsxs("div",{className:"block-table",children:[e.jsx("h3",{children:"Por Bloque"}),e.jsxs("table",{children:[e.jsx("thead",{children:e.jsxs("tr",{children:[e.jsx("th",{children:"Bloque"}),e.jsx("th",{children:"Comp."}),e.jsx("th",{children:"Gráf."}),e.jsx("th",{children:"Prom."}),e.jsx("th",{children:"Sin Rival"}),e.jsx("th",{children:"Relajadas"})]})}),e.jsx("tbody",{children:f.map(o=>e.jsxs("tr",{children:[e.jsx("td",{children:o.bloque}),e.jsx("td",{children:o.competidores}),e.jsx("td",{children:o.brackets}),e.jsx("td",{children:o.avg_size}),e.jsx("td",{children:o.sin_rival}),e.jsx("td",{children:o.relaxed_count})]},o.bloque))})]})]})]}),t==="brackets"&&e.jsx("div",{className:"brackets-content",children:f.map(o=>e.jsxs("div",{className:"block-section",children:[e.jsxs("button",{className:"block-header",onClick:()=>p(u===o.bloque?null:o.bloque),children:[e.jsx("span",{children:o.bloque}),e.jsxs("span",{children:[o.brackets," gráficas"]})]}),u===o.bloque&&e.jsx("div",{className:"bracket-list",children:j.filter(a=>a.competidores[0].bloque===o.bloque).map(a=>e.jsxs("div",{className:`bracket-card ${a.tipo}`,children:[e.jsxs("div",{className:"bracket-header",children:[e.jsxs("span",{className:"bracket-number",children:["#",a.numero]}),e.jsxs("span",{className:"bracket-area",children:["Área ",a.area]}),e.jsx("span",{className:`bracket-type ${a.tipo}`,children:a.tipo}),e.jsxs("span",{className:"bracket-score",children:[a.score,"%"]})]}),e.jsx("div",{className:"competitors",children:a.competidores.map(m=>e.jsxs("div",{className:"competitor-item",children:[e.jsxs("div",{children:[e.jsx("span",{className:"comp-num",children:m.numero_competidor}),e.jsxs("span",{className:"comp-name",children:[m.nombre," ",m.apellido]})]}),e.jsxs("span",{className:"comp-details",children:[m.edad," años • ",m.peso_kg," kg • ",m.modalidad," • ",m.doyang]})]},m.id))}),a.score_breakdown&&e.jsxs("div",{className:"score-breakdown",children:[e.jsx("div",{className:"breakdown-title",children:"Desglose de Puntuación"}),e.jsxs("table",{className:"breakdown-table",children:[e.jsx("thead",{children:e.jsxs("tr",{children:[e.jsx("th",{children:"Criterio"}),e.jsx("th",{children:"Diferencia"}),e.jsx("th",{children:"Puntaje"})]})}),e.jsxs("tbody",{children:[e.jsxs("tr",{children:[e.jsx("td",{children:"Modalidad"}),e.jsx("td",{className:"diff",children:"Misma → ✓"}),e.jsx("td",{className:a.score_breakdown.modalidad_ok?"score-ok":"score-bad",children:a.score_breakdown.modalidad_ok?"Compatible":"Incompatible"})]}),e.jsxs("tr",{children:[e.jsx("td",{children:"Edad"}),e.jsxs("td",{className:"diff",children:["±",a.score_breakdown.edad_diff," años"]}),e.jsxs("td",{children:[a.score_breakdown.edad_score," pts"]})]}),e.jsxs("tr",{children:[e.jsx("td",{children:"Peso"}),e.jsxs("td",{className:"diff",children:["±",a.score_breakdown.peso_diff," kg"]}),e.jsxs("td",{children:[a.score_breakdown.peso_score," pts"]})]}),e.jsxs("tr",{children:[e.jsx("td",{children:"Estatura"}),e.jsxs("td",{className:"diff",children:["±",a.score_breakdown.estatura_diff," cm"]}),e.jsxs("td",{children:[a.score_breakdown.estatura_score," pts"]})]}),e.jsxs("tr",{children:[e.jsx("td",{children:"Doyang"}),e.jsx("td",{className:"diff",children:a.competidores.length>1&&a.competidores[0].doyang!==a.competidores[1].doyang?"Diferentes → +0.2":"Mismo → +0"}),e.jsxs("td",{children:["+",a.score_breakdown.doyang_bonus," pts"]})]}),e.jsxs("tr",{className:"total-row",children:[e.jsx("td",{colSpan:"2",children:"Puntaje Total"}),e.jsx("td",{className:"total",children:a.score_breakdown.total})]})]})]})]})]},a.id))})]},o.bloque))}),t==="unpaired"&&e.jsx("div",{className:"unpaired-content",children:d.length===0?e.jsx("p",{className:"no-unpaired",children:"No hay competidores sin rival"}):e.jsxs("table",{className:"unpaired-table",children:[e.jsx("thead",{children:e.jsxs("tr",{children:[e.jsx("th",{title:"Nombre completo del competidor",children:"Nombre"}),e.jsx("th",{title:"Grupo por sexo y cinta",children:"Bloque"}),e.jsx("th",{title:"Años del competidor",children:"Edad"}),e.jsx("th",{title:"Peso en kilogramos",children:"Peso"}),e.jsx("th",{title:"Escuela o club",children:"Doyang"}),e.jsx("th",{title:"Por qué no se pudo emparejar con nadie",children:"Razón"})]})}),e.jsx("tbody",{children:d.map((o,a)=>e.jsxs("tr",{children:[e.jsxs("td",{children:[o.competidor.nombre," ",o.competidor.apellido]}),e.jsx("td",{children:o.competidor.bloque}),e.jsx("td",{children:o.competidor.edad}),e.jsx("td",{children:o.competidor.peso_kg}),e.jsx("td",{children:o.competidor.doyang}),e.jsx("td",{children:o.razon})]},a))})]})}),t==="manage"&&e.jsx(B,{initialData:{brackets:j,unpaired:d}})]})}function $(){const[x,n]=l.useState(null),[g,t]=l.useState(0),h=u=>{n(u),t(p=>p+1)};return e.jsxs("div",{className:"app-wrapper",children:[e.jsx(F,{onResults:h}),x&&e.jsx(G,{initialResults:x},g),e.jsx("style",{children:`
        .app-wrapper {
          margin-top: 24px;
        }
      `})]})}export{$ as default};
