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

# =============================================================================
# CONSTANTES REALISTAS
# =============================================================================
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
    "MDK FLORIDO", "MDK CASA BLANCA", "MDK EL DORADO", "MDK ALBA ROJA",
    "MDK AGUAJE DE LA TUNA", "MDK DEL VALLE", "MDK OBRERA", "MDK MURUA",
    "MDK VILLA DEL SOL", "MDK OTAY",
]

FIRST_NAMES_M = ["JESUS", "DAMIAN", "ALEX", "DIEGO", "MIGUEL", "LUIS", "CARLOS", "JUAN", "PEDRO", "GABRIEL",
                 "ADRIAN", "BRANDON", "KEVIN", "JOSE", "ANGEL", "DANIEL", "ESTEBAN", "IVAN", "OSCAR", "RAUL"]
FIRST_NAMES_F = ["SOFIA", "MARIA", "CAMILA", "VALENTINA", "LUCIA", "PAULA", "ANA", "LAURA", "KARLA", "GABRIELA",
                 "ADRIANA", "MONSERRAT", "DANIELA", "ALEXANDRA", "ELIZABETH", "PATRICIA", "ANGELICA", "VERONICA", "DIANA", "LIZBETH"]
LAST_NAMES = ["LOPEZ", "GARCIA", "MARTINEZ", "RODRIGUEZ", "HERNANDEZ", "PEREZ", "SANCHEZ", "RAMIREZ", "TORRES", "FLORES",
              "RIVERA", "GOMEZ", "DIAZ", "REYES", "MORALES", "CRUZ", "ORTIZ", "GUTIERREZ", "CHAVEZ", "RAMOS"]

# Grados por bloque (coherentes con el algoritmo)
GRADOS_POR_BLOQUE = {
    "Adultos Grupo 1": ["1er Dan", "2do Dan", "3er Dan"],
    "Adultos Grupo 2": ["Blanca", "Amarilla", "Verde", "Azul"],
    "Infantil Azul": ["7 KUP", "6 KUP", "5 KUP"],
    "Infantil Verde": ["8 KUP", "7 KUP", "6 KUP"],
    "Infantil Amarilla": ["9 KUP", "8 KUP", "7 KUP"],
    "Infantil Blanca": ["10 KUP", "Blanca"],
    "Infantil Marrón": ["4 KUP", "3 KUP"],
    "Infantil Roja": ["2 KUP", "1 KUP"],
    "Infantil Negra": ["1er Poom", "1er Dan"],
    "Pre-Taekwondo": ["Pre-Taekwondo"],
}

# Rangos de edad realistas por categoría (usadas internamente)
EDAD_POR_CATEGORIA = {
    "Preescolar": (3, 5),
    "Infantil_6_7": (6, 7),
    "Infantil_8_9": (8, 9),
    "Infantil_10_11": (10, 11),
    "Infantil_12_13": (12, 13),
    "Cadete": (14, 15),
    "Juvenil": (16, 17),
    "Adulto": (18, 29),
    "Sub_Master": (30, 45),
    "Master": (46, 60),
}

# Parámetros para distribución normal de peso y estatura por edad (media, desviación)
# Basado en tablas de crecimiento infantil y adulto promedio
PESO_POR_EDAD = {
    "Preescolar": (18, 3),      # media 18 kg, desv 3
    "Infantil_6_7": (23, 4),
    "Infantil_8_9": (30, 5),
    "Infantil_10_11": (38, 6),
    "Infantil_12_13": (48, 7),
    "Cadete": (55, 8),
    "Juvenil": (62, 9),
    "Adulto": (70, 12),
    "Sub_Master": (75, 12),
    "Master": (75, 12),
}

ESTATURA_POR_EDAD = {
    "Preescolar": (105, 8),     # media 105 cm, desv 8
    "Infantil_6_7": (120, 8),
    "Infantil_8_9": (135, 9),
    "Infantil_10_11": (145, 10),
    "Infantil_12_13": (155, 10),
    "Cadete": (162, 9),
    "Juvenil": (168, 9),
    "Adulto": (170, 10),
    "Sub_Master": (170, 10),
    "Master": (168, 10),
}

# Probabilidad de generar un edge case (fuera de rango normal)
EDGE_CASE_PROB = 0.05  # 5% de competidores serán casos límite

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def get_categoria_edad(edad: int) -> str:
    for cat, (min_e, max_e) in EDAD_POR_CATEGORIA.items():
        if min_e <= edad <= max_e:
            return cat
    return "Adulto"

def get_bloque_por_cinta_edad(cinta: str, edad: int) -> str:
    """Asigna bloque según reglas del torneo (mismo que en algorithm.py)"""
    if edad <= 5:
        return "Pre-Taekwondo"
    elif edad >= 18:
        # Adultos: Grupo 1 = marrón, roja, negra Dan
        if cinta in ["Marrón", "Roja", "1er Dan", "2do Dan", "3er Dan"]:
            return "Adultos Grupo 1"
        else:
            return "Adultos Grupo 2"
    else:
        # Infantiles: según cinta (mapeo directo)
        mapeo = {
            "Azul": "Infantil Azul",
            "Verde": "Infantil Verde",
            "Amarilla": "Infantil Amarilla",
            "Blanca": "Infantil Blanca",
            "Marrón": "Infantil Marrón",
            "Roja": "Infantil Roja",
            "1er Poom": "Infantil Negra",
            "1er Dan": "Infantil Negra",  # Dan infantil (raro, pero posible)
        }
        return mapeo.get(cinta, "Infantil Blanca")  # fallback

def generar_edad_y_categoria(bloque: str) -> tuple:
    """Genera edad coherente con el bloque y devuelve (edad, categoria_edad)"""
    # Obtener rango de edad según bloque (usando rangos realistas)
    rangos_bloque = {
        "Adultos Grupo 1": (18, 35),
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
    min_e, max_e = rangos_bloque.get(bloque, (18, 40))
    edad = random.randint(min_e, max_e)
    categoria = get_categoria_edad(edad)
    return edad, categoria

def generar_peso_estatura_realista(edad: int, categoria: str, edge_case: bool = False) -> tuple:
    """Genera peso (kg) y estatura (cm) con distribución normal, opcionalmente edge case"""
    # Obtener parámetros para la categoría de edad
    media_peso, std_peso = PESO_POR_EDAD.get(categoria, (70, 12))
    media_est, std_est = ESTATURA_POR_EDAD.get(categoria, (170, 10))
    
    if edge_case:
        # Caso extremo: peso o estatura muy por encima o debajo (percentil 95 o 5)
        if random.random() < 0.5:
            # Peso extremo
            factor = random.choice([1.5, 0.6])  # +50% o -40%
            peso = media_peso * factor
            peso = max(10, min(150, peso))
        else:
            peso = max(10, min(150, random.gauss(media_peso, std_peso * 2)))
        
        if random.random() < 0.5:
            # Estatura extrema
            factor = random.choice([1.2, 0.8])
            est = media_est * factor
            est = max(80, min(210, est))
        else:
            est = max(80, min(210, random.gauss(media_est, std_est * 2)))
    else:
        # Caso normal: distribución gaussiana truncada a rangos realistas
        peso = random.gauss(media_peso, std_peso)
        peso = max(10, min(150, peso))
        est = random.gauss(media_est, std_est)
        est = max(80, min(210, est))
    
    return round(peso, 2), int(round(est))

def generate_random_competidor(bloque: str, edge_case_prob: float = EDGE_CASE_PROB) -> dict:
    """Genera un competidor con datos coherentes con el bloque"""
    sexo = random.choice(["H", "M"])
    # Generar edad y categoría coherente con el bloque
    edad, categoria_edad = generar_edad_y_categoria(bloque)
    
    # Elegir grado según bloque
    grado = random.choice(GRADOS_POR_BLOQUE[bloque])
    # Normalizar nombre de cinta para que coincida con lo que espera el algoritmo
    if grado in ["1er Dan", "2do Dan", "3er Dan"]:
        cinta_block = "Negra (Dan)"
    elif grado == "1er Poom":
        cinta_block = "Negra (Poom)"
    elif grado in ["Blanca", "Amarilla", "Verde", "Azul", "Marrón", "Roja"]:
        cinta_block = grado
    elif grado in ["10 KUP", "9 KUP", "8 KUP", "7 KUP", "6 KUP", "5 KUP", "4 KUP", "3 KUP", "2 KUP", "1 KUP"]:
        # Mapear KUP a nombre de cinta (simplificado)
        if grado in ["10 KUP"]:
            cinta_block = "Blanca"
        elif grado in ["9 KUP", "8 KUP"]:
            cinta_block = "Amarilla"
        elif grado in ["7 KUP", "6 KUP"]:
            cinta_block = "Verde"
        elif grado in ["5 KUP", "4 KUP"]:
            cinta_block = "Azul"
        elif grado in ["3 KUP", "2 KUP"]:
            cinta_block = "Marrón"
        else:  # 1 KUP
            cinta_block = "Roja"
    else:
        cinta_block = grado  # fallback
    
    # Decidir si es edge case
    edge_case = random.random() < edge_case_prob
    peso, estatura = generar_peso_estatura_realista(edad, categoria_edad, edge_case)
    
    return {
        "Nombre": random.choice(FIRST_NAMES_M if sexo == "H" else FIRST_NAMES_F),
        "Apellido": random.choice(LAST_NAMES),
        "Edad": edad,
        "H/M": sexo,
        "Grado": grado,
        "Peso": peso,
        "Estatura": estatura,
        "Modalidad": random.choice(["Doble", "Sencillo"]),
        "Doyang": random.choice(SCHOOLS),
        # Campos internos (no van al Excel pero útiles para debug)
        "_categoria_edad": categoria_edad,
        "_cinta_block": cinta_block,
        "_bloque": bloque,
    }

# =============================================================================
# GENERACIÓN DE ARCHIVO EXCEL
# =============================================================================

def create_random_fixture(num_competitors=900, num_blocks=10, edge_case_prob=EDGE_CASE_PROB):
    """Crea un archivo Excel con datos realistas y opcionalmente edge cases"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"random_{timestamp}.xlsx"
    filepath = Path(tempfile.gettempdir()) / filename
    
    # Usar todos los bloques o una selección
    blocks_to_use = random.sample(BLOCKS, min(num_blocks, len(BLOCKS)))
    
    # Distribuir competidores equitativamente entre bloques (para tener densidad realista)
    base_count = num_competitors // len(blocks_to_use)
    remainder = num_competitors % len(blocks_to_use)
    competitors_per_block = []
    for i, block in enumerate(blocks_to_use):
        count = base_count + (1 if i < remainder else 0)
        if count < 2:
            count = 2
        competitors_per_block.append((block, count))
    
    # Generar Excel
    workbook = xlsxwriter.Workbook(str(filepath))
    headers = ["No", "Nombre", "Apellido", "Edad", "H/M", "Grado", "Peso", "Estatura", "Modalidad", "Doyang"]
    
    for block, count in competitors_per_block:
        worksheet = workbook.add_worksheet(block)
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)
        for i in range(count):
            comp = generate_random_competidor(block, edge_case_prob)
            comp["No"] = i + 1
            for col, header in enumerate(headers):
                worksheet.write(i + 1, col, comp[header])
    
    workbook.close()
    return filepath

# =============================================================================
# EJECUCIÓN DE PRUEBAS
# =============================================================================

def run_random_test(edge_case_prob=EDGE_CASE_PROB):
    """Ejecuta una prueba aleatoria con datos realistas"""
    filepath = None
    start_time = time.time()
    try:
        num_competitors = random.randint(900, 1200)
        num_blocks = random.randint(8, 10)  # usar casi todos los bloques para densidad
        filepath = create_random_fixture(num_competitors, num_blocks, edge_case_prob)
        competitors, errors = parse_excel(str(filepath))
        if not competitors:
            return {"status": "error", "error": f"No competitors parsed: {errors}", "type": "random"}
        results = generate_results(competitors)
        gs = results.global_stats
        total = gs.total_competidores
        paired = total - gs.sin_rival_total
        pairing_rate = (paired / total * 100) if total > 0 else 0
        excellent = gs.excellent_brackets
        quality_rate = (excellent / gs.total_brackets * 100) if gs.total_brackets > 0 else 0
        
        # Datos detallados (opcional, puedes mantener igual)
        brackets_data = []
        for b in results.brackets:
            brackets_data.append({
                "id": b.id,
                "numero": b.numero,
                "area": b.area,
                "tipo": b.tipo,
                "score": b.score,
                "competidores": [{"id": c.id, "nombre": c.nombre, "apellido": c.apellido, "edad": c.edad,
                                  "categoria_edad": c.categoria_edad, "sexo": c.sexo, "peso": c.peso_kg,
                                  "estatura": c.estatura_cm, "modalidad": c.modalidad, "doyang": c.doyang,
                                  "bloque": c.bloque, "cinta_block": c.cinta_block} for c in b.competidores]
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
                    "doyang_penalty": b.score_breakdown.doyang_penalty,
                    "cinta_penalty": b.score_breakdown.cinta_penalty,
                    "total": b.score_breakdown.total,
                }
            if b.failure_reasons:
                brackets_data[-1]["failure_reasons"] = b.failure_reasons
        
        unpaired_data = [{"nombre": u.competidor.nombre, "apellido": u.competidor.apellido,
                          "bloque": u.competidor.bloque, "edad": u.competidor.edad,
                          "peso": u.competidor.peso_kg, "doyang": u.competidor.doyang,
                          "razon": u.razon} for u in results.unpaired]
        
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
            "elapsed": round(time.time() - start_time, 3),
            "brackets": brackets_data,
            "unpaired": unpaired_data,
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "type": "random", "elapsed": round(time.time() - start_time, 3)}
    finally:
        if filepath and os.path.exists(filepath):
            try:
                os.unlink(filepath)
            except:
                pass

def run_random_tests(count=25, edge_case_prob=EDGE_CASE_PROB):
    results = []
    for i in range(count):
        result = run_random_test(edge_case_prob)
        result["name"] = f"random_{i+1}"
        results.append(result)
    successful = [r for r in results if r.get("status") == "success"]
    failed = [r for r in results if r.get("status") == "error"]
    avg_pairing = sum(r.get("pairing_rate", 0) for r in successful) / len(successful) if successful else 0
    avg_quality = sum(r.get("quality_rate", 0) for r in successful) / len(successful) if successful else 0
    avg_time = sum(r.get("elapsed", 0) for r in successful) / len(successful) if successful else 0
    avg_brackets_2 = sum(r.get("brackets_2", 0) for r in successful) / len(successful) if successful else 0
    avg_brackets_3 = sum(r.get("brackets_3", 0) for r in successful) / len(successful) if successful else 0
    avg_brackets_4 = sum(r.get("brackets_4", 0) for r in successful) / len(successful) if successful else 0
    summary = {
        "total_runs": count,
        "successful": len(successful),
        "failed": len(failed),
        "avg_pairing_rate": round(avg_pairing, 2),
        "avg_quality_rate": round(avg_quality, 2),
        "avg_time": round(avg_time, 3),
        "avg_brackets_2": round(avg_brackets_2, 1),
        "avg_brackets_3": round(avg_brackets_3, 1),
        "avg_brackets_4": round(avg_brackets_4, 1),
    }
    return {
        "timestamp": datetime.now().isoformat(),
        "type": "random",
        "total_tests": count,
        "tests": results,
        "summary": summary,
    }

if __name__ == "__main__":
    # Ejecutar 5 pruebas con 5% de edge cases
    report = run_random_tests(5, edge_case_prob=0.05)
    print(f"Random tests: {report['summary']}")