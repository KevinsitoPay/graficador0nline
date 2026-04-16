from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import tempfile
import os
import json
from pathlib import Path
from datetime import datetime

from app.parser import parse_excel
from app.algorithm import generate_results
from app.models import UploadResponse, Results

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