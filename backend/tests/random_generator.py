# import random
# import xlsxwriter
# import time
# import os
# import sys
# import tempfile
# from pathlib import Path
# from datetime import datetime

# sys.path.insert(0, str(Path(__file__).parent.parent))

# from app.parser import parse_excel
# from app.algorithm import generate_results

# # =============================================================================
# # CONSTANTES REALISTAS
# # =============================================================================
# BLOCKS = [
#     "Adultos Grupo 1",
#     "Adultos Grupo 2",
#     "Infantil Azul",
#     "Infantil Verde",
#     "Infantil Amarilla",
#     "Infantil Blanca",
#     "Infantil Marrón",
#     "Infantil Roja",
#     "Infantil Negra",
#     "Pre-Taekwondo",
# ]



# SCHOOLS = [
#     "MDK FLORIDO", "MDK CASA BLANCA", "MDK EL DORADO", "MDK ALBA ROJA",
#     "MDK AGUAJE DE LA TUNA", "MDK DEL VALLE", "MDK OBRERA", "MDK MURUA",
#     "MDK VILLA DEL SOL", "MDK OTAY",
# ]

# FIRST_NAMES_M = ["JESUS", "DAMIAN", "ALEX", "DIEGO", "MIGUEL", "LUIS", "CARLOS", "JUAN", "PEDRO", "GABRIEL",
#                  "ADRIAN", "BRANDON", "KEVIN", "JOSE", "ANGEL", "DANIEL", "ESTEBAN", "IVAN", "OSCAR", "RAUL"]
# FIRST_NAMES_F = ["SOFIA", "MARIA", "CAMILA", "VALENTINA", "LUCIA", "PAULA", "ANA", "LAURA", "KARLA", "GABRIELA",
#                  "ADRIANA", "MONSERRAT", "DANIELA", "ALEXANDRA", "ELIZABETH", "PATRICIA", "ANGELICA", "VERONICA", "DIANA", "LIZBETH"]
# LAST_NAMES = ["LOPEZ", "GARCIA", "MARTINEZ", "RODRIGUEZ", "HERNANDEZ", "PEREZ", "SANCHEZ", "RAMIREZ", "TORRES", "FLORES",
#               "RIVERA", "GOMEZ", "DIAZ", "REYES", "MORALES", "CRUZ", "ORTIZ", "GUTIERREZ", "CHAVEZ", "RAMOS"]

# # Grados por bloque (coherentes con el algoritmo)
# GRADOS_POR_BLOQUE = {
#     "Adultos Grupo 1": ["1er Dan", "2do Dan", "3er Dan"],
#     "Adultos Grupo 2": ["Blanca", "Amarilla", "Verde", "Azul"],
#     "Infantil Azul": ["7 KUP", "6 KUP", "5 KUP"],
#     "Infantil Verde": ["8 KUP", "7 KUP", "6 KUP"],
#     "Infantil Amarilla": ["9 KUP", "8 KUP", "7 KUP"],
#     "Infantil Blanca": ["10 KUP", "Blanca"],
#     "Infantil Marrón": ["4 KUP", "3 KUP"],
#     "Infantil Roja": ["2 KUP", "1 KUP"],
#     "Infantil Negra": ["1er Poom", "1er Dan"],
#     "Pre-Taekwondo": ["Pre-Taekwondo"],
# }

# # Rangos de edad realistas por categoría (usadas internamente)
# EDAD_POR_CATEGORIA = {
#     "Preescolar": (3, 5),
#     "Infantil_6_7": (6, 7),
#     "Infantil_8_9": (8, 9),
#     "Infantil_10_11": (10, 11),
#     "Infantil_12_13": (12, 13),
#     "Cadete": (14, 15),
#     "Juvenil": (16, 17),
#     "Adulto": (18, 29),
#     "Sub_Master": (30, 45),
#     "Master": (46, 60),
# }

# # Parámetros para distribución normal de peso y estatura por edad (media, desviación)
# # Basado en tablas de crecimiento infantil y adulto promedio
# PESO_POR_EDAD = {
#     "Preescolar": (18, 3),      # media 18 kg, desv 3
#     "Infantil_6_7": (23, 4),
#     "Infantil_8_9": (30, 5),
#     "Infantil_10_11": (38, 6),
#     "Infantil_12_13": (48, 7),
#     "Cadete": (55, 8),
#     "Juvenil": (62, 9),
#     "Adulto": (70, 12),
#     "Sub_Master": (75, 12),
#     "Master": (75, 12),
# }

# ESTATURA_POR_EDAD = {
#     "Preescolar": (105, 8),     # media 105 cm, desv 8
#     "Infantil_6_7": (120, 8),
#     "Infantil_8_9": (135, 9),
#     "Infantil_10_11": (145, 10),
#     "Infantil_12_13": (155, 10),
#     "Cadete": (162, 9),
#     "Juvenil": (168, 9),
#     "Adulto": (170, 10),
#     "Sub_Master": (170, 10),
#     "Master": (168, 10),
# }

# # Probabilidad de generar un edge case (fuera de rango normal)
# EDGE_CASE_PROB = 0.05  # 5% de competidores serán casos límite

# # =============================================================================
# # FUNCIONES AUXILIARES
# # =============================================================================

# def get_categoria_edad(edad: int) -> str:
#     for cat, (min_e, max_e) in EDAD_POR_CATEGORIA.items():
#         if min_e <= edad <= max_e:
#             return cat
#     return "Adulto"

# def get_bloque_por_cinta_edad(cinta: str, edad: int) -> str:
#     """Asigna bloque según reglas del torneo (mismo que en algorithm.py)"""
#     if edad <= 5:
#         return "Pre-Taekwondo"
#     elif edad >= 18:
#         # Adultos: Grupo 1 = marrón, roja, negra Dan
#         if cinta in ["Marrón", "Roja", "1er Dan", "2do Dan", "3er Dan"]:
#             return "Adultos Grupo 1"
#         else:
#             return "Adultos Grupo 2"
#     else:
#         # Infantiles: según cinta (mapeo directo)
#         mapeo = {
#             "Azul": "Infantil Azul",
#             "Verde": "Infantil Verde",
#             "Amarilla": "Infantil Amarilla",
#             "Blanca": "Infantil Blanca",
#             "Marrón": "Infantil Marrón",
#             "Roja": "Infantil Roja",
#             "1er Poom": "Infantil Negra",
#             "1er Dan": "Infantil Negra",  # Dan infantil (raro, pero posible)
#         }
#         return mapeo.get(cinta, "Infantil Blanca")  # fallback

# def generar_edad_y_categoria(bloque: str) -> tuple:
#     """Genera edad coherente con el bloque y devuelve (edad, categoria_edad)"""
#     # Obtener rango de edad según bloque (usando rangos realistas)
#     rangos_bloque = {
#         "Adultos Grupo 1": (18, 35),
#         "Adultos Grupo 2": (18, 40),
#         "Infantil Azul": (6, 13),
#         "Infantil Verde": (6, 13),
#         "Infantil Amarilla": (6, 13),
#         "Infantil Blanca": (6, 13),
#         "Infantil Marrón": (6, 13),
#         "Infantil Roja": (6, 13),
#         "Infantil Negra": (6, 13),
#         "Pre-Taekwondo": (3, 5),
#     }
#     min_e, max_e = rangos_bloque.get(bloque, (18, 40))
#     edad = random.randint(min_e, max_e)
#     categoria = get_categoria_edad(edad)
#     return edad, categoria

# def generar_peso_estatura_realista(edad: int, categoria: str, edge_case: bool = False) -> tuple:
#     """Genera peso (kg) y estatura (cm) con distribución normal, opcionalmente edge case"""
#     # Obtener parámetros para la categoría de edad
#     media_peso, std_peso = PESO_POR_EDAD.get(categoria, (70, 12))
#     media_est, std_est = ESTATURA_POR_EDAD.get(categoria, (170, 10))
    
#     if edge_case:
#         # Caso extremo: peso o estatura muy por encima o debajo (percentil 95 o 5)
#         if random.random() < 0.5:
#             # Peso extremo
#             factor = random.choice([1.5, 0.6])  # +50% o -40%
#             peso = media_peso * factor
#             peso = max(10, min(150, peso))
#         else:
#             peso = max(10, min(150, random.gauss(media_peso, std_peso * 2)))
        
#         if random.random() < 0.5:
#             # Estatura extrema
#             factor = random.choice([1.2, 0.8])
#             est = media_est * factor
#             est = max(80, min(210, est))
#         else:
#             est = max(80, min(210, random.gauss(media_est, std_est * 2)))
#     else:
#         # Caso normal: distribución gaussiana truncada a rangos realistas
#         peso = random.gauss(media_peso, std_peso)
#         peso = max(10, min(150, peso))
#         est = random.gauss(media_est, std_est)
#         est = max(80, min(210, est))
    
#     return round(peso, 2), int(round(est))

# def generate_random_competidor(bloque: str, edge_case_prob: float = EDGE_CASE_PROB) -> dict:
#     """Genera un competidor con datos coherentes con el bloque"""
#     sexo = random.choice(["H", "M"])
#     # Generar edad y categoría coherente con el bloque
#     edad, categoria_edad = generar_edad_y_categoria(bloque)
    
#     # Elegir grado según bloque
#     grado = random.choice(GRADOS_POR_BLOQUE[bloque])
#     # Normalizar nombre de cinta para que coincida con lo que espera el algoritmo
#     if grado in ["1er Dan", "2do Dan", "3er Dan"]:
#         cinta_block = "Negra (Dan)"
#     elif grado == "1er Poom":
#         cinta_block = "Negra (Poom)"
#     elif grado in ["Blanca", "Amarilla", "Verde", "Azul", "Marrón", "Roja"]:
#         cinta_block = grado
#     elif grado in ["10 KUP", "9 KUP", "8 KUP", "7 KUP", "6 KUP", "5 KUP", "4 KUP", "3 KUP", "2 KUP", "1 KUP"]:
#         # Mapear KUP a nombre de cinta (simplificado)
#         if grado in ["10 KUP"]:
#             cinta_block = "Blanca"
#         elif grado in ["9 KUP", "8 KUP"]:
#             cinta_block = "Amarilla"
#         elif grado in ["7 KUP", "6 KUP"]:
#             cinta_block = "Verde"
#         elif grado in ["5 KUP", "4 KUP"]:
#             cinta_block = "Azul"
#         elif grado in ["3 KUP", "2 KUP"]:
#             cinta_block = "Marrón"
#         else:  # 1 KUP
#             cinta_block = "Roja"
#     else:
#         cinta_block = grado  # fallback
    
#     # Decidir si es edge case
#     edge_case = random.random() < edge_case_prob
#     peso, estatura = generar_peso_estatura_realista(edad, categoria_edad, edge_case)
    
#     return {
#         "Nombre": random.choice(FIRST_NAMES_M if sexo == "H" else FIRST_NAMES_F),
#         "Apellido": random.choice(LAST_NAMES),
#         "Edad": edad,
#         "H/M": sexo,
#         "Grado": grado,
#         "Peso": peso,
#         "Estatura": estatura,
#         "Modalidad": random.choice(["Doble", "Sencillo"]),
#         "Doyang": random.choice(SCHOOLS),
#         # Campos internos (no van al Excel pero útiles para debug)
#         "_categoria_edad": categoria_edad,
#         "_cinta_block": cinta_block,
#         "_bloque": bloque,
#     }

# # =============================================================================
# # GENERACIÓN DE ARCHIVO EXCEL
# # =============================================================================

# def create_random_fixture(num_competitors=900, num_blocks=10, edge_case_prob=EDGE_CASE_PROB):
#     """Crea un archivo Excel con datos realistas y opcionalmente edge cases"""
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
#     filename = f"random_{timestamp}.xlsx"
#     filepath = Path(tempfile.gettempdir()) / filename
    
#     # Usar todos los bloques o una selección
#     blocks_to_use = random.sample(BLOCKS, min(num_blocks, len(BLOCKS)))
    
#     # Distribuir competidores equitativamente entre bloques (para tener densidad realista)
#     base_count = num_competitors // len(blocks_to_use)
#     remainder = num_competitors % len(blocks_to_use)
#     competitors_per_block = []
#     for i, block in enumerate(blocks_to_use):
#         count = base_count + (1 if i < remainder else 0)
#         if count < 2:
#             count = 2
#         competitors_per_block.append((block, count))
    
#     # Generar Excel
#     workbook = xlsxwriter.Workbook(str(filepath))
#     headers = ["No", "Nombre", "Apellido", "Edad", "H/M", "Grado", "Peso", "Estatura", "Modalidad", "Doyang"]
    
#     for block, count in competitors_per_block:
#         worksheet = workbook.add_worksheet(block)
#         for col, header in enumerate(headers):
#             worksheet.write(0, col, header)
#         for i in range(count):
#             comp = generate_random_competidor(block, edge_case_prob)
#             comp["No"] = i + 1
#             for col, header in enumerate(headers):
#                 worksheet.write(i + 1, col, comp[header])
    
#     workbook.close()
#     return filepath

# # =============================================================================
# # EJECUCIÓN DE PRUEBAS
# # =============================================================================

# def run_random_test(edge_case_prob=EDGE_CASE_PROB):
#     """Ejecuta una prueba aleatoria con datos realistas"""
#     filepath = None
#     start_time = time.time()
#     try:
#         num_competitors = random.randint(900, 1200)
#         num_blocks = random.randint(8, 10)  # usar casi todos los bloques para densidad
#         filepath = create_random_fixture(num_competitors, num_blocks, edge_case_prob)
#         competitors, errors = parse_excel(str(filepath))
#         if not competitors:
#             return {"status": "error", "error": f"No competitors parsed: {errors}", "type": "random"}
#         results = generate_results(competitors)
#         gs = results.global_stats
#         total = gs.total_competidores
#         paired = total - gs.sin_rival_total
#         pairing_rate = (paired / total * 100) if total > 0 else 0
#         excellent = gs.excellent_brackets
#         quality_rate = (excellent / gs.total_brackets * 100) if gs.total_brackets > 0 else 0
        
#         # Datos detallados (opcional, puedes mantener igual)
#         brackets_data = []
#         for b in results.brackets:
#             brackets_data.append({
#                 "id": b.id,
#                 "numero": b.numero,
#                 "area": b.area,
#                 "tipo": b.tipo,
#                 "score": b.score,
#                 "competidores": [{"id": c.id, "nombre": c.nombre, "apellido": c.apellido, "edad": c.edad,
#                                   "categoria_edad": c.categoria_edad, "sexo": c.sexo, "peso": c.peso_kg,
#                                   "estatura": c.estatura_cm, "modalidad": c.modalidad, "doyang": c.doyang,
#                                   "bloque": c.bloque, "cinta_block": c.cinta_block} for c in b.competidores]
#             })
#             if b.score_breakdown:
#                 brackets_data[-1]["score_breakdown"] = {
#                     "modalidad_ok": b.score_breakdown.modalidad_ok,
#                     "edad_diff": b.score_breakdown.edad_diff,
#                     "edad_score": b.score_breakdown.edad_score,
#                     "peso_diff": b.score_breakdown.peso_diff,
#                     "peso_score": b.score_breakdown.peso_score,
#                     "estatura_diff": b.score_breakdown.estatura_diff,
#                     "estatura_score": b.score_breakdown.estatura_score,
#                     "doyang_penalty": b.score_breakdown.doyang_penalty,
#                     "cinta_penalty": b.score_breakdown.cinta_penalty,
#                     "total": b.score_breakdown.total,
#                 }
#             if b.failure_reasons:
#                 brackets_data[-1]["failure_reasons"] = b.failure_reasons
        
#         unpaired_data = [{"nombre": u.competidor.nombre, "apellido": u.competidor.apellido,
#                           "bloque": u.competidor.bloque, "cinta_block": u.competidor.cinta_block,
#                           "edad": u.competidor.edad, "peso": u.competidor.peso_kg,
#                           "doyang": u.competidor.doyang, "razon": u.razon} for u in results.unpaired]
        
#         return {
#             "name": f"random_{filepath.stem}",
#             "type": "random",
#             "total_competitors": total,
#             "total_brackets": gs.total_brackets,
#             "avg_bracket_size": gs.avg_bracket_size,
#             "pairing_rate": round(pairing_rate, 2),
#             "brackets_2": gs.brackets_2,
#             "brackets_3": gs.brackets_3,
#             "brackets_4": gs.brackets_4,
#             "excellent": excellent,
#             "quality_rate": round(quality_rate, 2),
#             "sin_rival": gs.sin_rival_total,
#             "status": "success",
#             "errors": errors,
#             "elapsed": round(time.time() - start_time, 3),
#             "brackets": brackets_data,
#             "unpaired": unpaired_data,
#         }
#     except Exception as e:
#         return {"status": "error", "error": str(e), "type": "random", "elapsed": round(time.time() - start_time, 3)}
#     finally:
#         if filepath and os.path.exists(filepath):
#             try:
#                 os.unlink(filepath)
#             except:
#                 pass

# def run_random_tests(count=25, edge_case_prob=EDGE_CASE_PROB):
#     results = []
#     for i in range(count):
#         result = run_random_test(edge_case_prob)
#         result["name"] = f"random_{i+1}"
#         results.append(result)
#     successful = [r for r in results if r.get("status") == "success"]
#     failed = [r for r in results if r.get("status") == "error"]
#     avg_pairing = sum(r.get("pairing_rate", 0) for r in successful) / len(successful) if successful else 0
#     avg_quality = sum(r.get("quality_rate", 0) for r in successful) / len(successful) if successful else 0
#     avg_time = sum(r.get("elapsed", 0) for r in successful) / len(successful) if successful else 0
#     avg_brackets_2 = sum(r.get("brackets_2", 0) for r in successful) / len(successful) if successful else 0
#     avg_brackets_3 = sum(r.get("brackets_3", 0) for r in successful) / len(successful) if successful else 0
#     avg_brackets_4 = sum(r.get("brackets_4", 0) for r in successful) / len(successful) if successful else 0
#     summary = {
#         "total_runs": count,
#         "successful": len(successful),
#         "failed": len(failed),
#         "avg_pairing_rate": round(avg_pairing, 2),
#         "avg_quality_rate": round(avg_quality, 2),
#         "avg_time": round(avg_time, 3),
#         "avg_brackets_2": round(avg_brackets_2, 1),
#         "avg_brackets_3": round(avg_brackets_3, 1),
#         "avg_brackets_4": round(avg_brackets_4, 1),
#     }
#     return {
#         "timestamp": datetime.now().isoformat(),
#         "type": "random",
#         "total_tests": count,
#         "tests": results,
#         "summary": summary,
#     }

# if __name__ == "__main__":
#     # Ejecutar 5 pruebas con 5% de edge cases
#     report = run_random_tests(5, edge_case_prob=0.05)
#     print(f"Random tests: {report['summary']}")


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
# CONSTANTES REALISTAS (basadas en el Excel del torneo Primavera 2026)
# =============================================================================

# Bloques en el orden habitual (para crear las hojas)
BLOCKS = [
    "Adultos Grupo 1",
    "Adultos Grupo 2",
    "Infantil Azul",
    "Infantil Verde",
    "Infantil Amarilla",
    "Infantil Blanca",
    "Pre-Taekwondo",
    "Infantil Marrón",
    "Infantil Roja",
    "Infantil Negra",
]

# Escuelas reales (lista ampliada)
SCHOOLS = [
    "MDK FLORIDO", "MDK CASA BLANCA", "MDK EL DORADO", "MDK ALBA ROJA",
    "MDK AGUAJE DE LA TUNA", "MDK DEL VALLE", "MDK OBRERA", "MDK MURUA",
    "MDK VILLA DEL SOL", "MDK OTAY", "MDK LOMAS DEL PORVENIR", "MDK CUCAPAH",
    "MDK ALTABRISA", "MDK SANTA CRUZ", "MDK EJIDO FRANCISCO VILLA", "MDK LA MESA",
    "MDK ROSARITO", "MDK SANCHEZ TABOADA", "MDK EL MIRADOR", "MDK INDEPENDENCIA",
    "MDK BUENOS AIRES", "MDK CENTRO", "MDK VILLA FONTANA", "MDK VILLAS DEL SOL",
    "MDK MISIONES PRESA ENS", "MDK CAPISTRANO", "MDK REAL DE SAN FRANCISCO",
    "MDK SALVATIERRA", "MDK ALTIPLANO", "MDK FRANCISCO VILLA", "MDK CEDROS",
]

FIRST_NAMES_M = [
    "JESUS", "DAMIAN", "ALEX", "DIEGO", "MIGUEL", "LUIS", "CARLOS", "JUAN", "PEDRO", "GABRIEL",
    "ADRIAN", "BRANDON", "KEVIN", "JOSE", "ANGEL", "DANIEL", "ESTEBAN", "IVAN", "OSCAR", "RAUL",
    "MATEO", "SANTIAGO", "SEBASTIAN", "EMILIANO", "LEONARDO"
]
FIRST_NAMES_F = [
    "SOFIA", "MARIA", "CAMILA", "VALENTINA", "LUCIA", "PAULA", "ANA", "LAURA", "KARLA", "GABRIELA",
    "ADRIANA", "MONSERRAT", "DANIELA", "ALEXANDRA", "ELIZABETH", "PATRICIA", "ANGELICA", "VERONICA",
    "DIANA", "LIZBETH", "XIMENA", "REGINA", "VICTORIA", "FERNANDA"
]
LAST_NAMES = [
    "LOPEZ", "GARCIA", "MARTINEZ", "RODRIGUEZ", "HERNANDEZ", "PEREZ", "SANCHEZ", "RAMIREZ", "TORRES", "FLORES",
    "RIVERA", "GOMEZ", "DIAZ", "REYES", "MORALES", "CRUZ", "ORTIZ", "GUTIERREZ", "CHAVEZ", "RAMOS",
    "CASTILLO", "JIMENEZ", "MENDOZA", "VARGAS"
]

# =============================================================================
# DISTRIBUCIÓN DE COMPETIDORES POR BLOQUE (proporciones realistas)
# =============================================================================
BLOQUE_PROBS = {
    "Pre-Taekwondo": 0.05,
    "Infantil Blanca": 0.09,
    "Infantil Amarilla": 0.09,
    "Infantil Verde": 0.10,
    "Infantil Azul": 0.15,
    "Infantil Marrón": 0.10,
    "Infantil Roja": 0.10,
    "Infantil Negra": 0.05,
    "Adultos Grupo 2": 0.15,
    "Adultos Grupo 1": 0.12,
}
# Normalizar (por si no suma 1)
total_prob = sum(BLOQUE_PROBS.values())
for k in BLOQUE_PROBS:
    BLOQUE_PROBS[k] /= total_prob

# =============================================================================
# PARÁMETROS DE GENERACIÓN POR BLOQUE (edad, peso, estatura)
# =============================================================================
# Cada bloque tiene: rango_edad (min, max), media_peso, std_peso, media_est, std_est
BLOQUE_PARAMS = {
    "Pre-Taekwondo": {
        "edad": (3, 5),
        "peso_media": 20, "peso_std": 3,
        "est_media": 110, "est_std": 6,
    },
    "Infantil Blanca": {
        "edad": (6, 13),
        "peso_media": 30, "peso_std": 8,
        "est_media": 130, "est_std": 10,
    },
    "Infantil Amarilla": {
        "edad": (6, 13),
        "peso_media": 32, "peso_std": 8,
        "est_media": 132, "est_std": 10,
    },
    "Infantil Verde": {
        "edad": (6, 13),
        "peso_media": 35, "peso_std": 9,
        "est_media": 135, "est_std": 10,
    },
    "Infantil Azul": {
        "edad": (6, 13),
        "peso_media": 40, "peso_std": 10,
        "est_media": 140, "est_std": 12,
    },
    "Infantil Marrón": {
        "edad": (6, 13),
        "peso_media": 45, "peso_std": 10,
        "est_media": 145, "est_std": 12,
    },
    "Infantil Roja": {
        "edad": (6, 13),
        "peso_media": 50, "peso_std": 12,
        "est_media": 150, "est_std": 12,
    },
    "Infantil Negra": {
        "edad": (6, 13),
        "peso_media": 55, "peso_std": 12,
        "est_media": 155, "est_std": 12,
    },
    "Adultos Grupo 2": {
        "edad": (14, 50),
        "peso_media": 70, "peso_std": 15,
        "est_media": 165, "est_std": 10,
    },
    "Adultos Grupo 1": {
        "edad": (14, 55),
        "peso_media": 75, "peso_std": 15,
        "est_media": 170, "est_std": 10,
    },
}

# =============================================================================
# DISTRIBUCIÓN DE GRADOS (CINTAS) POR BLOQUE
# =============================================================================
GRADOS_POR_BLOQUE = {
    "Pre-Taekwondo": [
        ("PRINCIPIANTE", 0.40),
        ("10 KUP", 0.30),
        ("9 KUP", 0.10),
        ("8 KUP", 0.08),
        ("7 KUP", 0.05),
        ("6 KUP", 0.04),
        ("5 KUP", 0.02),
        ("4 KUP", 0.01),
    ],
    "Infantil Blanca": [
        ("PRINCIPIANTE", 0.50),
        ("10 KUP", 0.50),
    ],
    "Infantil Amarilla": [
        ("9 KUP", 0.34),
        ("8 KUP", 0.33),
        ("7 KUP", 0.33),
    ],
    "Infantil Verde": [
        ("8 KUP", 0.34),
        ("7 KUP", 0.33),
        ("6 KUP", 0.33),
    ],
    "Infantil Azul": [
        ("7 KUP", 0.25),
        ("6 KUP", 0.25),
        ("5 KUP", 0.25),
        ("4 KUP", 0.25),
    ],
    "Infantil Marrón": [
        ("4 KUP", 0.34),
        ("3 KUP", 0.33),
        ("2 KUP", 0.33),
    ],
    "Infantil Roja": [
        ("2 KUP", 0.34),
        ("1 KUP", 0.33),
        ("IEBY POOM", 0.33),
    ],
    "Infantil Negra": [
        ("1er Poom", 0.40),
        ("1er Dan", 0.30),
        ("IEBY POOM", 0.30),
    ],
    "Adultos Grupo 2": [
        ("PRINCIPIANTE", 0.10),
        ("Blanca", 0.25),
        ("Amarilla", 0.25),
        ("Verde", 0.20),
        ("Azul", 0.20),
    ],
    "Adultos Grupo 1": [
        ("Marrón", 0.20),
        ("Roja", 0.20),
        ("Negra (Poom)", 0.30),
        ("Negra (Dan)", 0.30),
    ],
}

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def get_categoria_edad(edad: int) -> str:
    """Clasificación por edad (usada internamente, pero no crítica para generación)"""
    if 3 <= edad <= 5:
        return "Preescolar"
    elif 6 <= edad <= 7:
        return "Infantil_6_7"
    elif 8 <= edad <= 9:
        return "Infantil_8_9"
    elif 10 <= edad <= 11:
        return "Infantil_10_11"
    elif 12 <= edad <= 13:
        return "Infantil_12_13"
    elif 14 <= edad <= 15:
        return "Cadete"
    elif 16 <= edad <= 17:
        return "Juvenil"
    elif 18 <= edad <= 29:
        return "Adulto"
    elif 30 <= edad <= 45:
        return "Sub_Master"
    else:
        return "Master"

def elegir_grado(bloque: str) -> tuple:
    """Devuelve (grado, cinta_normalizada) según distribución del bloque."""
    opciones = GRADOS_POR_BLOQUE[bloque]
    r = random.random()
    acum = 0
    for grado, prob in opciones:
        acum += prob
        if r <= acum:
            # Normalizar cinta a como lo espera el algoritmo
            if grado == "PRINCIPIANTE":
                cinta = "Blanca"
            elif grado in ("10 KUP", "9 KUP", "8 KUP", "7 KUP", "6 KUP", "5 KUP", "4 KUP", "3 KUP", "2 KUP", "1 KUP"):
                # Mapeo de KUP a cinta
                if grado in ("10 KUP", "PRINCIPIANTE"):
                    cinta = "Blanca"
                elif grado in ("9 KUP", "8 KUP"):
                    cinta = "Amarilla"
                elif grado in ("7 KUP", "6 KUP"):
                    cinta = "Verde"
                elif grado in ("5 KUP", "4 KUP"):
                    cinta = "Azul"
                elif grado in ("3 KUP", "2 KUP"):
                    cinta = "Marrón"
                else:  # 1 KUP
                    cinta = "Roja"
            elif grado in ("1er Poom", "IEBY POOM"):
                cinta = "Negra (Poom)"
            elif grado in ("1er Dan", "2do Dan", "3er Dan", "IEBY DAN"):
                cinta = "Negra (Dan)"
            else:
                cinta = grado  # "Blanca", "Amarilla", etc.
            return grado, cinta
    # fallback
    return "Blanca", "Blanca"

def generar_peso_estatura(bloque: str, edge_case: bool = False) -> tuple:
    """Genera peso (kg) y estatura (cm) usando distribución normal por bloque."""
    params = BLOQUE_PARAMS[bloque]
    media_peso = params["peso_media"]
    std_peso = params["peso_std"]
    media_est = params["est_media"]
    std_est = params["est_std"]
    if edge_case:
        # Caso extremo moderado (factor 1.3 o 0.7)
        factor_peso = random.choice([1.3, 0.7])
        peso = media_peso * factor_peso
        peso = max(10, min(150, peso))
        factor_est = random.choice([1.15, 0.85])
        est = media_est * factor_est
        est = max(80, min(210, est))
    else:
        peso = random.gauss(media_peso, std_peso)
        peso = max(10, min(150, peso))
        est = random.gauss(media_est, std_est)
        est = max(80, min(210, est))
    return round(peso, 2), int(round(est))

def generar_edad(bloque: str) -> int:
    """Genera edad dentro del rango del bloque."""
    rango = BLOQUE_PARAMS[bloque]["edad"]
    return random.randint(rango[0], rango[1])

def generar_sexo() -> str:
    """Retorna 'H' o 'M' con igual probabilidad."""
    return random.choice(["H", "M"])

def generar_modalidad() -> str:
    """Distribución realista: 80% Doble, 15% Formas, 5% Combate."""
    r = random.random()
    if r < 0.80:
        return "Doble"
    elif r < 0.95:
        return "Formas"
    else:
        return "Combate"

def generate_random_competidor(bloque: str, edge_case_prob: float = 0.02) -> dict:
    """Genera un competidor coherente con el bloque."""
    sexo = generar_sexo()
    edad = generar_edad(bloque)
    grado, cinta_block = elegir_grado(bloque)
    edge_case = random.random() < edge_case_prob
    peso, estatura = generar_peso_estatura(bloque, edge_case)
    modalidad = generar_modalidad()
    doyang = random.choice(SCHOOLS)
    nombre = random.choice(FIRST_NAMES_M if sexo == "H" else FIRST_NAMES_F)
    apellido = random.choice(LAST_NAMES)
    return {
        "Nombre": nombre,
        "Apellido": apellido,
        "Edad": edad,
        "H/M": sexo,
        "Grado": grado,
        "Peso": peso,
        "Estatura": estatura,
        "Modalidad": modalidad,
        "Doyang": doyang,
        "_cinta_block": cinta_block,   # para debug
        "_bloque": bloque,
    }

# =============================================================================
# GENERACIÓN DE ARCHIVO EXCEL
# =============================================================================

def create_random_fixture(num_competitors=1000, edge_case_prob=0.02):
    """Crea un archivo Excel con distribución realista de competidores."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"random_{timestamp}.xlsx"
    filepath = Path(tempfile.gettempdir()) / filename

    # Decidir cuántos competidores por bloque según las proporciones
    counts = {}
    remaining = num_competitors
    for bloque, prob in sorted(BLOQUE_PROBS.items(), key=lambda x: -x[1]):  # ordenar por prob descendente
        if remaining <= 0:
            counts[bloque] = 0
            continue
        count = int(round(prob * num_competitors))
        # Asegurar al menos 2 por bloque (si hay suficientes)
        if count < 2 and remaining >= 2:
            count = 2
        counts[bloque] = count
        remaining -= count
    # Ajustar por redondeo (asignar los restantes al bloque con más probabilidad)
    if remaining > 0:
        max_block = max(BLOQUE_PROBS.items(), key=lambda x: x[1])[0]
        counts[max_block] += remaining

    # Crear el workbook
    workbook = xlsxwriter.Workbook(str(filepath))
    headers = ["No", "Nombre", "Apellido", "Edad", "H/M", "Grado", "Peso", "Estatura", "Modalidad", "Doyang"]

    for bloque in BLOCKS:
        count = counts.get(bloque, 0)
        if count == 0:
            continue
        worksheet = workbook.add_worksheet(bloque)
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)
        for i in range(count):
            comp = generate_random_competidor(bloque, edge_case_prob)
            # Escribir fila
            worksheet.write(i+1, 0, i+1)  # No
            worksheet.write(i+1, 1, comp["Nombre"])
            worksheet.write(i+1, 2, comp["Apellido"])
            worksheet.write(i+1, 3, comp["Edad"])
            worksheet.write(i+1, 4, comp["H/M"])
            worksheet.write(i+1, 5, comp["Grado"])
            worksheet.write(i+1, 6, comp["Peso"])
            worksheet.write(i+1, 7, comp["Estatura"])
            worksheet.write(i+1, 8, comp["Modalidad"])
            worksheet.write(i+1, 9, comp["Doyang"])

    workbook.close()
    return filepath

# =============================================================================
# EJECUCIÓN DE PRUEBAS
# =============================================================================

def run_random_test(edge_case_prob=0.02):
    """Ejecuta una prueba aleatoria con datos realistas."""
    filepath = None
    start_time = time.time()
    try:
        num_competitors = random.randint(800, 1200)  # torneo típico
        filepath = create_random_fixture(num_competitors, edge_case_prob)
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
                          "bloque": u.competidor.bloque, "cinta_block": u.competidor.cinta_block,
                          "edad": u.competidor.edad, "peso": u.competidor.peso_kg,
                          "doyang": u.competidor.doyang, "razon": u.razon} for u in results.unpaired]

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

def run_random_tests(count=25, edge_case_prob=0.02):
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
    # Ejecutar 5 pruebas con 2% de edge cases
    report = run_random_tests(5, edge_case_prob=0.02)
    print(f"Random tests: {report['summary']}")