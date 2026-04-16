import random
import xlsxwriter
import time
import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.parser import parse_excel
from app.algorithm import generate_results


BLOCKS = [
    "Adultos Grupo 1",
    "Adultos Grupo 2",
    "Infantil Azul",
    "Infantil Verde",
    "Infantil Amarilla",
    "Infantil Blanca",
    "Infantil Marrón",
    "Infantil Roja",
    "Infantil Negra",
    "Pre-Taekwondo",
]

SCHOOLS = [
    "MDK FLORIDO",
    "MDK CASA BLANCA",
    "MDK EL DORADO",
    "KUK SUL",
    "CHAMPIONS",
    "TAEKWONDO PLUS",
    "OLIMPICO",
    "VICTORY",
    "KORYO",
    "PAQUI",
]

FIRST_NAMES_M = [
    "JESUS", "DAMIAN", "ALEX", "DIEGO", "MIGUEL", "LUIS", "CARLOS", "JUAN", "PEDRO", "GABRIEL",
    "ADRIAN", "BRANDON", "KEVIN", "JOSE", "ANGEL", "DANIEL", "ESTEBAN", "IVAN", "OSCAR", "RAUL",
]

FIRST_NAMES_F = [
    "SOFIA", "MARIA", "CAMILA", "VALENTINA", "LUCIA", "PAULA", "ANA", "LAURA", "KARLA", "GABRIELA",
    "ADRIANA", "MONSERRAT", "DANIELA", "ALEXANDRA", "ELIZABETH", "PATRICIA", "ANGELICA", "VERONICA", "DIANA", "LIZBETH",
]

LAST_NAMES = [
    "LOPEZ", "GARCIA", "MARTINEZ", "RODRIGUEZ", "HERNANDEZ", "PEREZ", "SANCHEZ", "RAMIREZ", "TORRES", "FLORES",
    "RIVERA", "GOMEZ", "DIAZ", "REYES", "MORALES", "CRUZ", "ORTIZ", "GUTIERREZ", "CHAVEZ", "RAMOS",
]

GRADOS = {
    "Adultos Grupo 1": ["1er Dan", "2do Dan", "3er Dan"],
    "Adultos Grupo 2": ["1er Dan", "2do Dan", "3er Dan"],
    "Infantil Azul": ["7 KUP", "6 KUP", "5 KUP"],
    "Infantil Verde": ["8 KUP", "7 KUP", "6 KUP"],
    "Infantil Amarilla": ["9 KUP", "8 KUP", "7 KUP"],
    "Infantil Blanca": ["10 KUP", "Blanca"],
    "Infantil Marrón": ["4 KUP", "3 KUP"],
    "Infantil Roja": ["2 KUP", "1 KUP"],
    "Infantil Negra": ["1er Poom", "1er Dan"],
    "Pre-Taekwondo": ["Pre-Taekwondo"],
}

EDAD_RANGES = {
    "Adultos Grupo 1": (18, 30),
    "Adultos Grupo 2": (18, 40),
    "Infantil Azul": (6, 13),
    "Infantil Verde": (6, 13),
    "Infantil Amarilla": (6, 13),
    "Infantil Blanca": (6, 13),
    "Infantil Marrón": (6, 13),
    "Infantil Roja": (6, 13),
    "Infantil Negra": (6, 13),
    "Pre-Taekwondo": (3, 5),
}

PESO_RANGES = {
    "Adultos Grupo 1": (45, 90),
    "Adultos Grupo 2": (50, 100),
    "Infantil Azul": (30, 60),
    "Infantil Verde": (28, 55),
    "Infantil Amarilla": (25, 50),
    "Infantil Blanca": (20, 40),
    "Infantil Marrón": (28, 55),
    "Infantil Roja": (25, 50),
    "Infantil Negra": (30, 65),
    "Pre-Taekwondo": (15, 30),
}

ESTATURA_RANGES = {
    "Adultos Grupo 1": (150, 195),
    "Adultos Grupo 2": (145, 200),
    "Infantil Azul": (130, 175),
    "Infantil Verde": (125, 165),
    "Infantil Amarilla": (115, 155),
    "Infantil Blanca": (105, 140),
    "Infantil Marrón": (120, 165),
    "Infantil Roja": (115, 160),
    "Infantil Negra": (130, 180),
    "Pre-Taekwondo": (95, 125),
}


def generate_random_competitor(block):
    """Generate a single random competitor"""
    sexo = random.choice(["H", "M"])
    
    edad_min, edad_max = EDAD_RANGES[block]
    peso_min, peso_max = PESO_RANGES[block]
    estatura_min, estatura_max = ESTATURA_RANGES[block]
    
    return {
        "Nombre": random.choice(FIRST_NAMES_M if sexo == "H" else FIRST_NAMES_F),
        "Apellido": random.choice(LAST_NAMES),
        "Edad": random.randint(edad_min, edad_max),
        "H/M": sexo,
        "Grado": random.choice(GRADOS[block]),
        "Peso": round(random.uniform(peso_min, peso_max), 2),
        "Estatura": random.randint(estatura_min, estatura_max),
        "Modalidad": random.choice(["Doble", "Sencillo"]).capitalize(),
        "Doyang": random.choice(SCHOOLS),
    }


def create_random_fixture(num_competitors=20, num_blocks=5):
    """Create a random fixture Excel file and return path"""
    # Use timestamp for unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"random_{timestamp}.xlsx"
    filepath = Path(tempfile.gettempdir()) / filename
    
    # Select random blocks
    blocks_to_use = random.sample(BLOCKS, min(num_blocks, len(BLOCKS)))
    
    # Distribute competitors among blocks
    competitors_per_block = []
    for i, block in enumerate(blocks_to_use):
        count = max(2, num_competitors // num_blocks)
        if i == 0:
            count = num_competitors - (len(blocks_to_use) - 1) * 2
        competitors_per_block.append((block, count))
    
    # Generate Excel
    workbook = xlsxwriter.Workbook(str(filepath))
    
    for block, count in competitors_per_block:
        worksheet = workbook.add_worksheet(block)
        headers = ["No", "Nombre", "Apellido", "Edad", "H/M", "Grado", "Peso", "Estatura", "Modalidad", "Doyang"]
        
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)
        
        for i in range(count):
            comp = generate_random_competitor(block)
            comp["No"] = i + 1  # Add row number
            for col, header in enumerate(headers):
                worksheet.write(i + 1, col, comp[header])
    
    workbook.close()
    return filepath


def run_random_test():
    """Run a single random test case"""
    filepath = None
    try:
        # Generate random fixture
        num_competitors = random.randint(100, 200)
        num_blocks = random.randint(5, 10)
        
        filepath = create_random_fixture(num_competitors, num_blocks)
        
        # Run through parser and algorithm
        competitors, errors = parse_excel(str(filepath))
        
        if not competitors:
            return {
                "status": "error",
                "error": f"No competitors parsed: {errors}",
                "type": "random",
            }
        
        results = generate_results(competitors)
        
        # Compute metrics
        gs = results.global_stats
        total = gs.total_competidores
        paired = total - gs.sin_rival_total
        pairing_rate = (paired / total * 100) if total > 0 else 0
        
        excellent = gs.excellent_brackets
        quality_rate = (excellent / gs.total_brackets * 100) if gs.total_brackets > 0 else 0
        
        # Convert brackets to serializable format
        brackets_data = []
        for b in results.brackets:
            brackets_data.append({
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
                        "peso": c.peso_kg,
                        "estatura": c.estatura_cm,
                        "modalidad": c.modalidad,
                        "doyang": c.doyang,
                        "bloque": c.bloque,
                        "cinta_block": c.cinta_block,
                    }
                    for c in b.competidores
                ]
            })
            
            if b.score_breakdown:
                brackets_data[-1]["score_breakdown"] = {
                    "modalidad_ok": b.score_breakdown.modalidad_ok,
                    "edad_diff": b.score_breakdown.edad_diff,
                    "edad_score": b.score_breakdown.edad_score,
                    "peso_diff": b.score_breakdown.peso_diff,
                    "peso_score": b.score_breakdown.peso_score,
                    "estatura_diff": b.score_breakdown.estatura_diff,
                    "estatura_score": b.score_breakdown.estatura_score,
                    "doyang_bonus": b.score_breakdown.doyang_bonus,
                    "total": b.score_breakdown.total,
                }
        
        # Unpaired competitors
        unpaired_data = []
        for u in results.unpaired:
            unpaired_data.append({
                "nombre": u.competidor.nombre,
                "apellido": u.competidor.apellido,
                "bloque": u.competidor.bloque,
                "edad": u.competidor.edad,
                "peso": u.competidor.peso_kg,
                "doyang": u.competidor.doyang,
                "razon": u.razon,
            })
        
        return {
            "name": f"random_{filepath.stem}",
            "type": "random",
            "total_competitors": total,
            "total_brackets": gs.total_brackets,
            "avg_bracket_size": gs.avg_bracket_size,
            "pairing_rate": round(pairing_rate, 2),
            "brackets_2": gs.brackets_2,
            "brackets_3": gs.brackets_3,
            "brackets_4": gs.brackets_4,
            "excellent": excellent,
            "quality_rate": round(quality_rate, 2),
            "sin_rival": gs.sin_rival_total,
            "status": "success",
            "errors": errors,
            # Full data for expanded view
            "brackets": brackets_data,
            "unpaired": unpaired_data,
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "type": "random",
        }
    
    finally:
        # Clean up temporary file
        if filepath and os.path.exists(filepath):
            try:
                os.unlink(filepath)
            except:
                pass


def run_random_tests(count=25):
    """Run multiple random tests and return report"""
    results = []
    
    for i in range(count):
        result = run_random_test()
        result["name"] = f"random_{i+1}"
        results.append(result)
    
    # Compute summary
    successful = [r for r in results if r.get("status") == "success"]
    failed = [r for r in results if r.get("status") == "error"]
    
    avg_pairing = sum(r.get("pairing_rate", 0) for r in successful) / len(successful) if successful else 0
    avg_quality = sum(r.get("quality_rate", 0) for r in successful) / len(successful) if successful else 0
    
    summary = {
        "total_runs": count,
        "successful": len(successful),
        "failed": len(failed),
        "avg_pairing_rate": round(avg_pairing, 2),
        "avg_quality_rate": round(avg_quality, 2),
        "avg_time": 0,
    }
    
    return {
        "timestamp": datetime.now().isoformat(),
        "type": "random",
        "total_tests": count,
        "tests": results,
        "summary": summary,
    }


if __name__ == "__main__":
    # Test run
    report = run_random_tests(5)
    print(f"Random tests: {report['summary']}")