from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import tempfile
import os
import json
from pathlib import Path
from datetime import datetime

from app.parser import parse_excel
from app.algorithm import generate_results, asignar_numeracion
from app.models import UploadResponse, Results
from app.recommendations import recommendation_manager

app = FastAPI(title="Graficador - Taekwondo Bracket System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Graficador API", "version": "1.0.0"}


@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="File must be .xlsx")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        competitors, errors = parse_excel(tmp_path)
        
        if not competitors:
            return UploadResponse(
                success=False,
                message=f"No valid competitors found. Errors: {'; '.join(errors) if errors else 'Unknown error'}",
                results=None
            )
        
        results = generate_results(competitors)
        
        return UploadResponse(
            success=True,
            message=f"Processed {len(competitors)} competitors, generated {results.global_stats.total_brackets} brackets",
            results=results
        )
    
    except Exception as e:
        return UploadResponse(
            success=False,
            message=f"Error processing file: {str(e)}",
            results=None
        )
    
    finally:
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except PermissionError:
            pass  # Windows file lock - will be cleaned up eventually


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/tests")
def run_tests():
    """Run all test fixtures and return metrics report"""
    from tests.test_runner import run_all_fixtures
    
    # Absolute path to fixtures
    fixtures_dir = Path("C:/Users/USUARIO/Desktop/sitiosLocales/Graficador/template/fixtures")
    
    if not fixtures_dir.exists():
        return {"success": False, "message": "Fixtures directory not found"}
    
    try:
        report = run_all_fixtures(fixtures_dir)
        
        # Save latest report
        report_dir = Path("C:/Users/USUARIO/Desktop/sitiosLocales/Graficador/reports")
        report_dir.mkdir(exist_ok=True)
        latest_path = report_dir / "latest_report.json"
        
        with open(latest_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "report": report
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


@app.get("/tests/random")
@app.get("/tests/random/{count}")
def run_random_tests(count: int = 25):
    """Run random test cases. Count: 1-100"""
    from tests.random_generator import run_random_tests as run_random
    
    # Validate count
    if count < 1:
        count = 1
    elif count > 100:
        count = 100
    
    try:
        report = run_random(count)
        
        # Save random test report
        report_dir = Path("C:/Users/USUARIO/Desktop/sitiosLocales/Graficador/backend/reports")
        report_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = report_dir / f"random_report_{timestamp}.json"
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Also save as latest
        latest_path = report_dir / "latest_random_report.json"
        with open(latest_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "report": report,
            "report_file": str(report_path)
        }
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.get("/tests/latest")
def get_latest_report():
    """Get the latest test report"""
    report_dir = Path("C:/Users/USUARIO/Desktop/sitiosLocales/Graficador/reports")
    latest_path = report_dir / "latest_report.json"
    
    if not latest_path.exists():
        return {"success": False, "message": "No test report found"}
    
    with open(latest_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    
    return {"success": True, "report": report}


@app.get("/tests/report/llm")
@app.get("/tests/report/llm/{count}")
def generate_llm_report(count: int = 25):
    """Generate LLM-friendly detailed Markdown report"""
    from tests.random_generator import run_random_tests
    from tests.llm_report import generate_llm_report, generate_llm_markdown
    
    if count < 1:
        count = 1
    elif count > 100:
        count = 100
    
    try:
        raw_report = run_random_tests(count)
        llm_report = generate_llm_report(raw_report, count)
        
        report_dir = Path("C:/Users/USUARIO/Desktop/sitiosLocales/Graficador/backend/reports")
        report_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        md_path = report_dir / f"llm_report_{timestamp}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(llm_report["markdown"])
        
        return {
            "success": True,
            "report": llm_report,
            "report_file": str(md_path)
        }
    except Exception as e:
        return {"success": False, "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


@app.post("/api/recommendations/generate")
def generate_recommendations(request: dict):
    """Generate recommendations for unpaired competitors"""
    from app.models import Competidor, Bracket, Unpaired
    
    try:
        brackets_data = request.get("brackets", [])
        unpaired_data = request.get("unpaired", [])
        
        brackets = [Bracket(**b) for b in brackets_data]
        unpaired = [Unpaired(**u) for u in unpaired_data]
        unpaired_comps = [u.competidor for u in unpaired]
        
        recomendaciones = recommendation_manager.generar_recomendaciones(unpaired_comps, brackets)
        
        return {
            "success": True,
            "recommendations": [r.dict() for r in recomendaciones]
        }
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.post("/api/recommendations/apply")
def apply_recommendation(request: dict):
    """Apply a recommendation"""
    try:
        recomendacion_id = request.get("recomendacion_id")
        brackets_data = request.get("brackets", [])
        unpaired_data = request.get("unpaired", [])
        usuario = request.get("usuario", "colaborador")
        
        brackets = [Bracket(**b) for b in brackets_data]
        unpaired = [Unpaired(**u) for u in unpaired_data]
        unpaired_comps = [u.competidor for u in unpaired]
        
        recomendaciones = recommendation_manager.generar_recomendaciones(unpaired_comps, brackets)
        
        rec = next((r for r in recomendaciones if r.id == recomendacion_id), None)
        if not rec:
            return {"success": False, "message": "Recomendación no encontrada"}
        
        brackets, unpaired = recommendation_manager.aplicar_recomendacion(
            rec, brackets, unpaired, usuario
        )
        
        return {
            "success": True,
            "brackets": [b.dict() for b in brackets],
            "unpaired": [{"competidor": u.dict(), "razon": "Manual"} for u in unpaired]
        }
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.post("/api/manual_assign")
def manual_assign(request: dict):
    """Manual assignment of competitor to bracket"""
    try:
        competidor_data = request.get("competidor")
        bracket_id = request.get("bracket_id")
        brackets_data = request.get("brackets", [])
        unpaired_data = request.get("unpaired", [])
        usuario = request.get("usuario", "colaborador")
        
        competidor = Competidor(**competidor_data)
        brackets = [Bracket(**b) for b in brackets_data]
        unpaired = [Unpaired(**u) for u in unpaired_data]
        unpaired_comps = [u.competidor for u in unpaired]
        
        bracket = next((b for b in brackets if b.id == bracket_id), None)
        if not bracket:
            return {"success": False, "message": "Bracket no encontrado"}
        
        brackets, unpaired = recommendation_manager.asignacion_manual(
            competidor, bracket, brackets, unpaired_comps, usuario
        )
        
        return {
            "success": True,
            "brackets": [b.dict() for b in brackets],
            "unpaired": [{"competidor": u.dict(), "razon": "Manual"} for u in unpaired]
        }
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.post("/api/undo")
def undo_last_action():
    """Undo last action"""
    action = recommendation_manager.deshacer_ultima()
    if action:
        return {"success": True, "action": action.dict()}
    return {"success": False, "message": "No hay acciones para deshacer"}


@app.get("/api/history")
def get_history():
    """Get action history"""
    history = recommendation_manager.obtener_historial()
    return {"success": True, "history": [h.dict() for h in history]}


@app.post("/api/finalize")
def finalize_pairing(request: dict):
    """Finalize pairing and export"""
    try:
        brackets_data = request.get("brackets", [])
        unpaired_data = request.get("unpaired", [])
        competidores_data = request.get("competidores", [])
        
        brackets = [Bracket(**b) for b in brackets_data]
        competidores = [Competidor(**c) for c in competidores_data]
        
        asignar_numeracion(brackets, competidores)
        
        report_dir = Path("C:/Users/USUARIO/Desktop/sitiosLocales/Graficador/backend/exports")
        report_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        json_path = report_dir / f"final_results_{timestamp}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "brackets": [b.dict() for b in brackets],
                "unpaired": [u.dict() for u in unpaired_data],
                "timestamp": timestamp
            }, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "brackets": [b.dict() for b in brackets],
            "export_file": str(json_path)
        }
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.get("/api/export/pdf")
def export_pdf(request: dict):
    """Export results to PDF"""
    try:
        brackets_data = request.get("brackets", [])
        unpaired_data = request.get("unpaired", [])
        
        from app.export_pdf import generar_pdf
        
        report_dir = Path("C:/Users/USUARIO/Desktop/sitiosLocales/Graficador/backend/exports")
        report_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_path = report_dir / f"brackets_{timestamp}.pdf"
        
        generar_pdf(brackets_data, unpaired_data, str(pdf_path))
        
        return {"success": True, "pdf_file": str(pdf_path)}
    except Exception as e:
        return {"success": False, "message": str(e)}