import sys
import json
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.parser import parse_excel
from app.algorithm import generate_results


def compute_metrics(results, competitors):
    """Compute all metrics from results"""
    gs = results.global_stats

    total = gs.total_competidores
    paired = total - gs.sin_rival_total
    pairing_rate = (paired / total * 100) if total > 0 else 0

    excellent = gs.excellent_brackets
    good = gs.total_brackets - excellent - gs.low_quality_brackets
    low = gs.low_quality_brackets

    # Calidad real = promedio de score de los brackets
    scores = [b.score for b in results.brackets]
    avg_score = sum(scores) / len(scores) if scores else 0
    min_score = min(scores) if scores else 0
    max_score = max(scores) if scores else 0

    # Mantener una métrica separada de excelencia
    excellent_rate = (excellent / gs.total_brackets * 100) if gs.total_brackets > 0 else 0

    quality_rate = round(avg_score, 2)

    # Convert brackets to serializable format
    brackets_data = []
    for b in results.brackets:
        bracket_dict = {
            "id": b.id,
            "numero": b.numero,
            "area": b.area,
            "tipo": b.tipo,
            "score": b.score,
            "competidores": [
                {
                    "id": c.id,
                    "numero": c.numero_competidor,
                    "nombre": c.nombre,
                    "apellido": c.apellido,
                    "edad": c.edad,
                    "categoria_edad": c.categoria_edad,
                    "peso": c.peso_kg,
                    "estatura": c.estatura_cm,
                    "modalidad": c.modalidad,
                    "doyang": c.doyang,
                    "bloque": c.bloque,
                    "cinta_block": c.cinta_block,
                }
                for c in b.competidores
            ]
        }

        if b.score_breakdown:
            bracket_dict["score_breakdown"] = {
                "modalidad_ok": b.score_breakdown.modalidad_ok,
                "edad_diff": b.score_breakdown.edad_diff,
                "edad_score": b.score_breakdown.edad_score,
                "peso_diff": b.score_breakdown.peso_diff,
                "peso_score": b.score_breakdown.peso_score,
                "estatura_diff": b.score_breakdown.estatura_diff,
                "estatura_score": b.score_breakdown.estatura_score,
                "doyang_penalty": b.score_breakdown.doyang_penalty,
                "cinta_penalty": b.score_breakdown.cinta_penalty,
                "total": b.score_breakdown.total,
            }

        if b.failure_reasons:
            bracket_dict["failure_reasons"] = b.failure_reasons

        brackets_data.append(bracket_dict)

    # Unpaired competitors
    unpaired_data = []
    for u in results.unpaired:
        unpaired_data.append({
            "nombre": u.competidor.nombre,
            "apellido": u.competidor.apellido,
            "bloque": u.competidor.bloque,
            "cinta_block": u.competidor.cinta_block,
            "edad": u.competidor.edad,
            "peso": u.competidor.peso_kg,
            "doyang": u.competidor.doyang,
            "razon": u.razon,
        })

    return {
        "total_competitors": total,
        "total_brackets": gs.total_brackets,
        "avg_bracket_size": gs.avg_bracket_size,
        "pairing_rate": round(pairing_rate, 2),

        "brackets_2": gs.brackets_2,
        "brackets_3": gs.brackets_3,
        "brackets_4": gs.brackets_4,

        "excellent": excellent,
        "excellent_rate": round(excellent_rate, 2),
        "good": good,
        "low_quality": low,
        "quality_rate": round(quality_rate, 2),

        "sin_rival": gs.sin_rival_total,

        "avg_score": round(avg_score, 3),
        "min_score": round(min_score, 3),
        "max_score": round(max_score, 3),

        # Full data for expanded view
        "brackets": brackets_data,
        "unpaired": unpaired_data,
    }


def run_fixture(fixture_path):
    """Run a single fixture and return metrics"""
    try:
        start = time.time()

        competitors, errors = parse_excel(str(fixture_path))

        if not competitors:
            elapsed = time.time() - start
            return {
                "status": "error",
                "error": f"No competitors: {errors}",
                "elapsed": round(elapsed, 3),
            }

        results = generate_results(competitors)
        elapsed = time.time() - start

        metrics = compute_metrics(results, competitors)
        metrics["status"] = "success"
        metrics["elapsed"] = round(elapsed, 3)
        metrics["errors"] = errors

        return metrics

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "elapsed": 0,
        }


def run_all_fixtures(fixtures_dir):
    """Run all fixtures (alias)"""
    return run_all_fixtures_from_dir(fixtures_dir)


def run_all_fixtures_from_dir(fixtures_dir):
    """Run all fixtures and generate report"""
    fixture_files = sorted(fixtures_dir.glob("*.xlsx"))

    report = {
        "timestamp": datetime.now().isoformat(),
        "total_fixtures": len(fixture_files),
        "fixtures": [],
        "summary": {
            "total_runs": 0,
            "successful": 0,
            "failed": 0,
            "avg_pairing_rate": 0,
            "avg_quality_rate": 0,
            "avg_excellent_rate": 0,
            "avg_time": 0,
        }
    }

    all_pairing = []
    all_quality = []
    all_excellent = []
    all_time = []
    all_brackets_2 = []
    all_brackets_3 = []
    all_brackets_4 = []

    for fixture in fixture_files:
        name = fixture.stem
        print(f"Running {name}...")

        metrics = run_fixture(fixture)

        fixture_result = {
            "name": name,
            "file": fixture.name,
            **metrics
        }

        report["fixtures"].append(fixture_result)

        if metrics.get("status") == "success":
            all_pairing.append(metrics.get("pairing_rate", 0))
            all_quality.append(metrics.get("quality_rate", 0))
            all_excellent.append(metrics.get("excellent_rate", 0))
            all_time.append(metrics.get("elapsed", 0))
            all_brackets_2.append(metrics.get("brackets_2", 0))
            all_brackets_3.append(metrics.get("brackets_3", 0))
            all_brackets_4.append(metrics.get("brackets_4", 0))

    successful = len(all_pairing)

    report["summary"]["total_runs"] = len(fixture_files)
    report["summary"]["successful"] = successful
    report["summary"]["failed"] = len(fixture_files) - successful
    report["summary"]["avg_pairing_rate"] = round(sum(all_pairing) / successful, 2) if successful else 0
    report["summary"]["avg_quality_rate"] = round(sum(all_quality) / successful, 2) if successful else 0
    report["summary"]["avg_excellent_rate"] = round(sum(all_excellent) / successful, 2) if successful else 0
    report["summary"]["avg_time"] = round(sum(all_time) / successful, 3) if successful else 0
    report["summary"]["avg_brackets_2"] = round(sum(all_brackets_2) / successful, 1) if successful else 0
    report["summary"]["avg_brackets_3"] = round(sum(all_brackets_3) / successful, 1) if successful else 0
    report["summary"]["avg_brackets_4"] = round(sum(all_brackets_4) / successful, 1) if successful else 0

    return report


def generate_text_report(report):
    """Generate human-readable text report"""
    lines = []
    lines.append("=" * 60)
    lines.append("TEST REPORT - GRAFICADOR")
    lines.append(f"Generated: {report['timestamp']}")
    lines.append("=" * 60)
    lines.append("")

    lines.append("SUMMARY")
    lines.append("-" * 40)
    s = report["summary"]
    lines.append(f"Total fixtures: {s['total_runs']}")
    lines.append(f"Successful: {s['successful']}")
    lines.append(f"Failed: {s['failed']}")
    lines.append(f"Average pairing rate: {s['avg_pairing_rate']}%")
    lines.append(f"Average quality rate: {s['avg_quality_rate']}%")
    lines.append(f"Average excellent rate: {s['avg_excellent_rate']}%")
    lines.append(f"Average time: {s['avg_time']}s")
    lines.append("")

    lines.append("PER-FIXTURE RESULTS")
    lines.append("-" * 72)
    lines.append(f"{'Fixture':<25} {'Comp':>5} {'Brackets':>8} {'Pair%':>7} {'Qual%':>7} {'Exc%':>7} {'Status':>8}")
    lines.append("-" * 72)

    for f in report["fixtures"]:
        name = f.get("name", "-")[:24]
        comp = f.get("total_competitors", "-")
        brackets = f.get("total_brackets", "-")
        pair = f.get("pairing_rate", "-")
        qual = f.get("quality_rate", "-")
        exc = f.get("excellent_rate", "-")
        status = f.get("status", "-")[:8]
        lines.append(f"{name:<25} {comp:>5} {brackets:>8} {pair:>7} {qual:>7} {exc:>7} {status:>8}")

    lines.append("")

    issues = [f for f in report["fixtures"] if f.get("status") != "success"]
    if issues:
        lines.append("ISSUES FOUND")
        lines.append("-" * 40)
        for f in issues:
            lines.append(f"- {f['name']}: {f.get('error', 'Unknown')}")

    return "\n".join(lines)


def main():
    fixtures_dir = Path(__file__).parent.parent.parent / "template" / "fixtures"
    output_dir = Path(__file__).parent.parent / "reports"
    output_dir.mkdir(exist_ok=True)

    print(f"Running tests from: {fixtures_dir}")
    print()

    report = run_all_fixtures(fixtures_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_path = output_dir / f"test_report_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    text_path = output_dir / f"test_report_{timestamp}.txt"
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(generate_text_report(report))

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    s = report["summary"]
    print(f"Total fixtures: {s['total_runs']}")
    print(f"Successful: {s['successful']}")
    print(f"Failed: {s['failed']}")
    print(f"Average pairing rate: {s['avg_pairing_rate']}%")
    print(f"Average quality rate: {s['avg_quality_rate']}%")
    print(f"Average excellent rate: {s['avg_excellent_rate']}%")
    print(f"Average time: {s['avg_time']}s")
    print()
    print(f"Report saved to: {json_path}")
    print(f"Text report: {text_path}")

    issues = [f for f in report["fixtures"] if f.get("status") != "success"]
    if issues:
        print()
        print("ISSUES:")
        for f in issues:
            print(f"  - {f['name']}: {f.get('error', 'Unknown')[:50]}")

    return report


if __name__ == "__main__":
    main()
