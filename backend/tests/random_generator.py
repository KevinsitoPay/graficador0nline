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
# BLOQUES
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

# Más infantiles, como en tus históricos
BLOQUE_PROBS = {
    "Pre-Taekwondo": 0.05,
    "Infantil Blanca": 0.11,
    "Infantil Amarilla": 0.13,
    "Infantil Verde": 0.14,
    "Infantil Azul": 0.16,
    "Infantil Marrón": 0.11,
    "Infantil Roja": 0.10,
    "Infantil Negra": 0.05,
    "Adultos Grupo 2": 0.08,
    "Adultos Grupo 1": 0.07,
}
_total_prob = sum(BLOQUE_PROBS.values())
for k in BLOQUE_PROBS:
    BLOQUE_PROBS[k] /= _total_prob

# =============================================================================
# CATÁLOGOS
# =============================================================================

SCHOOLS = [
    "MDK FLORIDO", "MDK CASA BLANCA", "MDK EL DORADO", "MDK ALBA ROJA",
    "MDK AGUAJE DE LA TUNA", "MDK DEL VALLE", "MDK OBRERA", "MDK MURUA",
    "MDK VILLA DEL SOL", "MDK OTAY", "MDK LOMAS DEL PORVENIR", "MDK CUCAPAH",
    "MDK ALTABRISA", "MDK SANTA CRUZ", "MDK EJIDO FRANCISCO VILLA", "MDK LA MESA",
    "MDK ROSARITO", "MDK SANCHEZ TABOADA", "MDK EL MIRADOR", "MDK INDEPENDENCIA",
    "MDK BUENOS AIRES", "MDK CENTRO", "MDK VILLA FONTANA", "MDK VILLAS DEL SOL",
    "MDK MISIONES PRESA ENS", "MDK CAPISTRANO", "MDK REAL DE SAN FRANCISCO",
    "MDK SALVATIERRA", "MDK ALTIPLANO", "MDK FRANCISCO VILLA", "MDK CEDROS",
    "MDK LOMA BONITA", "MDK LOMA DORADA", "MDK EL LAGO", "MDK SANTA FE",
]

FIRST_NAMES_M = [
    "JESUS", "DAMIAN", "ALEX", "DIEGO", "MIGUEL", "LUIS", "CARLOS", "JUAN", "PEDRO", "GABRIEL",
    "ADRIAN", "BRANDON", "KEVIN", "JOSE", "ANGEL", "DANIEL", "ESTEBAN", "IVAN", "OSCAR", "RAUL",
    "MATEO", "SANTIAGO", "SEBASTIAN", "EMILIANO", "LEONARDO", "AXEL", "NOAH", "LIAM", "IAN"
]
FIRST_NAMES_F = [
    "SOFIA", "MARIA", "CAMILA", "VALENTINA", "LUCIA", "PAULA", "ANA", "LAURA", "KARLA", "GABRIELA",
    "ADRIANA", "MONSERRAT", "DANIELA", "ALEXANDRA", "ELIZABETH", "PATRICIA", "ANGELICA", "VERONICA",
    "DIANA", "LIZBETH", "XIMENA", "REGINA", "VICTORIA", "FERNANDA", "MELISSA", "EMILY", "REBECA"
]
LAST_NAMES = [
    "LOPEZ", "GARCIA", "MARTINEZ", "RODRIGUEZ", "HERNANDEZ", "PEREZ", "SANCHEZ", "RAMIREZ", "TORRES", "FLORES",
    "RIVERA", "GOMEZ", "DIAZ", "REYES", "MORALES", "CRUZ", "ORTIZ", "GUTIERREZ", "CHAVEZ", "RAMOS",
    "CASTILLO", "JIMENEZ", "MENDOZA", "VARGAS", "NAVARRO", "AGUILAR", "VELAZQUEZ"
]

# =============================================================================
# GRADOS POR BLOQUE
# =============================================================================

GRADOS_POR_BLOQUE = {
    "Pre-Taekwondo": [
        ("PRINCIPIANTE", 0.30),
        ("10 KUP", 0.35),
        ("9 KUP", 0.20),
        ("8 KUP", 0.10),
        ("7 KUP", 0.05),
    ],
    "Infantil Blanca": [
        ("PRINCIPIANTE", 0.45),
        ("10 KUP", 0.55),
    ],
    "Infantil Amarilla": [
        ("9 KUP", 0.60),
        ("8 KUP", 0.40),
    ],
    "Infantil Verde": [
        ("7 KUP", 0.55),
        ("6 KUP", 0.45),
    ],
    "Infantil Azul": [
        ("5 KUP", 0.50),
        ("4 KUP", 0.50),
    ],
    "Infantil Marrón": [
        ("3 KUP", 0.55),
        ("2 KUP", 0.45),
    ],
    "Infantil Roja": [
        ("1 KUP", 0.35),
        ("IEBY POOM", 0.65),
    ],
    "Infantil Negra": [
        ("1 POOM", 0.70),
        ("2 POOM", 0.20),
        ("3 POOM", 0.10),
    ],
    "Adultos Grupo 2": [
        ("PRINCIPIANTE", 0.10),
        ("10 KUP", 0.18),
        ("9 KUP", 0.18),
        ("8 KUP", 0.18),
        ("7 KUP", 0.14),
        ("6 KUP", 0.10),
        ("5 KUP", 0.07),
        ("4 KUP", 0.05),
    ],
    "Adultos Grupo 1": [
        ("3 KUP", 0.15),
        ("2 KUP", 0.15),
        ("1 KUP", 0.15),
        ("IEBY POOM", 0.20),
        ("IEBY DAN", 0.15),
        ("1 DAN", 0.10),
        ("2 DAN", 0.06),
        ("3 DAN", 0.03),
        ("4 DAN", 0.01),
    ],
}

# =============================================================================
# PARÁMETROS FÍSICOS
# =============================================================================

BLOQUE_PARAMS = {
    "Pre-Taekwondo": {"edad": (3, 5), "peso_media": 19, "peso_std": 3, "est_media": 109, "est_std": 7},
    "Infantil Blanca": {"edad": (6, 13), "peso_media": 33, "peso_std": 10, "est_media": 134, "est_std": 12},
    "Infantil Amarilla": {"edad": (6, 13), "peso_media": 35, "peso_std": 10, "est_media": 136, "est_std": 12},
    "Infantil Verde": {"edad": (6, 13), "peso_media": 37, "peso_std": 11, "est_media": 140, "est_std": 13},
    "Infantil Azul": {"edad": (6, 13), "peso_media": 40, "peso_std": 12, "est_media": 144, "est_std": 13},
    "Infantil Marrón": {"edad": (6, 13), "peso_media": 45, "peso_std": 12, "est_media": 149, "est_std": 13},
    "Infantil Roja": {"edad": (6, 13), "peso_media": 48, "peso_std": 13, "est_media": 152, "est_std": 13},
    "Infantil Negra": {"edad": (9, 13), "peso_media": 52, "peso_std": 14, "est_media": 156, "est_std": 12},
    "Adultos Grupo 2": {"edad": (14, 55), "peso_media": 64, "peso_std": 14, "est_media": 162, "est_std": 10},
    "Adultos Grupo 1": {"edad": (14, 60), "peso_media": 68, "peso_std": 16, "est_media": 167, "est_std": 10},
}

# =============================================================================
# MODALIDAD
# =============================================================================

def generar_modalidad_cluster() -> str:
    # Cluster homogéneo: mayoría de competidores de un cluster comparten modalidad
    r = random.random()
    if r < 0.88:
        return "Doble"
    elif r < 0.97:
        return "Formas"
    return "Combate"

def generar_modalidad_desde_cluster(modalidad_base: str) -> str:
    # Mantener coherencia de cluster
    if random.random() < 0.93:
        return modalidad_base
    return modalidad_base

# =============================================================================
# AUXILIARES
# =============================================================================

def get_categoria_edad(edad: int) -> str:
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
    opciones = GRADOS_POR_BLOQUE[bloque]
    r = random.random()
    acum = 0.0
    for grado, prob in opciones:
        acum += prob
        if r <= acum:
            if grado == "PRINCIPIANTE":
                cinta = "Blanca"
            elif grado in ("10 KUP", "9 KUP", "8 KUP", "7 KUP", "6 KUP", "5 KUP", "4 KUP", "3 KUP", "2 KUP", "1 KUP"):
                if grado == "10 KUP":
                    cinta = "Blanca"
                elif grado in ("8 KUP", "9 KUP"):
                    cinta = "Amarilla"
                elif grado in ("6 KUP", "7 KUP"):
                    cinta = "Verde"
                elif grado in ("4 KUP", "5 KUP"):
                    cinta = "Azul"
                elif grado in ("2 KUP", "3 KUP"):
                    cinta = "Marrón"
                else:
                    cinta = "Roja"
            elif grado in ("1 POOM", "2 POOM", "3 POOM", "IEBY POOM"):
                cinta = "Negra (Poom)"
            elif grado in ("1 DAN", "2 DAN", "3 DAN", "4 DAN", "5 DAN", "IEBY DAN"):
                cinta = "Negra (Dan)"
            else:
                cinta = grado
            return grado, cinta
    return "Blanca", "Blanca"

def generar_edad(bloque: str) -> int:
    lo, hi = BLOQUE_PARAMS[bloque]["edad"]
    return random.randint(lo, hi)

def generar_sexo() -> str:
    return "H" if random.random() < 0.52 else "M"

# =============================================================================
# GENERACIÓN POR CLUSTER
# =============================================================================

def _sample_truncated_gauss(mean, std, lo, hi):
    for _ in range(20):
        val = random.gauss(mean, std)
        if lo <= val <= hi:
            return val
    return max(lo, min(hi, mean))

def generar_cluster_base(bloque: str):
    params = BLOQUE_PARAMS[bloque]

    sexo = generar_sexo()
    edad_base = generar_edad(bloque)
    grado_base, cinta_base = elegir_grado(bloque)
    modalidad_base = generar_modalidad_cluster()
    doyang_base = random.choice(SCHOOLS)

    media_peso = params["peso_media"]
    media_est = params["est_media"]

    edad_min, edad_max = params["edad"]
    if edad_max > edad_min:
        ratio = (edad_base - edad_min) / (edad_max - edad_min)
        media_peso += ratio * 8
        media_est += ratio * 12

    peso_base = _sample_truncated_gauss(media_peso, params["peso_std"], 10, 150)
    est_base = _sample_truncated_gauss(media_est, params["est_std"], 80, 210)

    return {
        "sexo": sexo,
        "edad_base": int(round(edad_base)),
        "grado_base": grado_base,
        "cinta_base": cinta_base,
        "modalidad_base": modalidad_base,
        "doyang_base": doyang_base,
        "peso_base": round(peso_base, 2),
        "est_base": int(round(est_base)),
    }

def generate_random_competidor_from_cluster(bloque: str, cluster: dict, edge_case_prob: float = 0.01) -> dict:
    sexo = cluster["sexo"]
    edad_base = cluster["edad_base"]
    modalidad = generar_modalidad_desde_cluster(cluster["modalidad_base"])
    doyang = cluster["doyang_base"]

    # en general, misma cinta en cluster; a veces una vecina si no rompe bloque
    grado = cluster["grado_base"]
    cinta_block = cluster["cinta_base"]

    edad = edad_base + random.choice([-1, 0, 0, 0, 1])
    lo, hi = BLOQUE_PARAMS[bloque]["edad"]
    edad = max(lo, min(hi, edad))

    edge_case = random.random() < edge_case_prob

    if edge_case:
        peso = cluster["peso_base"] * random.choice([0.85, 1.18])
        est = cluster["est_base"] * random.choice([0.92, 1.08])
    else:
        # compactar alrededor del centro del cluster
        peso = random.gauss(cluster["peso_base"], 2.5 if "Infantil" in bloque or bloque == "Pre-Taekwondo" else 4.5)
        est = random.gauss(cluster["est_base"], 3.5 if "Infantil" in bloque or bloque == "Pre-Taekwondo" else 5.0)

    peso = round(max(10, min(150, peso)), 2)
    estatura = int(round(max(80, min(210, est))))

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
        "_cinta_block": cinta_block,
        "_bloque": bloque,
    }

# =============================================================================
# CREACIÓN DEL EXCEL
# =============================================================================

def create_random_fixture(num_competitors=1000, edge_case_prob=0.01):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"random_{timestamp}.xlsx"
    filepath = Path(tempfile.gettempdir()) / filename

    counts = {}
    remaining = num_competitors

    for bloque, prob in sorted(BLOQUE_PROBS.items(), key=lambda x: -x[1]):
        if remaining <= 0:
            counts[bloque] = 0
            continue
        count = int(round(prob * num_competitors))
        if count < 2 and remaining >= 2:
            count = 2
        counts[bloque] = count
        remaining -= count

    if remaining > 0:
        max_block = max(BLOQUE_PROBS.items(), key=lambda x: x[1])[0]
        counts[max_block] += remaining

    workbook = xlsxwriter.Workbook(str(filepath))
    headers = ["No", "Nombre", "Apellido", "Edad", "H/M", "Grado", "Peso", "Estatura", "Modalidad", "Doyang"]

    for bloque in BLOCKS:
        count = counts.get(bloque, 0)
        if count <= 0:
            continue

        worksheet = workbook.add_worksheet(bloque)

        for col, header in enumerate(headers):
            worksheet.write(0, col, header)

        # Generar varios clusters por bloque
        # más competidores => más clusters, pero no demasiados
        if count <= 12:
            num_clusters = max(1, count // 4)
        elif count <= 40:
            num_clusters = max(2, count // 6)
        else:
            num_clusters = max(4, count // 10)

        clusters = [generar_cluster_base(bloque) for _ in range(num_clusters)]

        # repartir competidores entre clusters
        rows = []
        for i in range(count):
            cluster = random.choice(clusters)
            comp = generate_random_competidor_from_cluster(bloque, cluster, edge_case_prob=edge_case_prob)
            rows.append(comp)

        for i, comp in enumerate(rows, start=1):
            worksheet.write(i, 0, i)
            worksheet.write(i, 1, comp["Nombre"])
            worksheet.write(i, 2, comp["Apellido"])
            worksheet.write(i, 3, comp["Edad"])
            worksheet.write(i, 4, comp["H/M"])
            worksheet.write(i, 5, comp["Grado"])
            worksheet.write(i, 6, comp["Peso"])
            worksheet.write(i, 7, comp["Estatura"])
            worksheet.write(i, 8, comp["Modalidad"])
            worksheet.write(i, 9, comp["Doyang"])

    workbook.close()
    return filepath

# =============================================================================
# EJECUCIÓN DE PRUEBAS
# =============================================================================

def run_random_test(edge_case_prob=0.01):
    filepath = None
    start_time = time.time()

    try:
        num_competitors = random.randint(850, 1200)
        filepath = create_random_fixture(num_competitors, edge_case_prob)

        competitors, errors = parse_excel(str(filepath))
        if not competitors:
            return {
                "status": "error",
                "error": f"No competitors parsed: {errors}",
                "type": "random"
            }

        results = generate_results(competitors)
        gs = results.global_stats

        total = gs.total_competidores
        paired = total - gs.sin_rival_total
        pairing_rate = (paired / total * 100) if total > 0 else 0

        scores = [b.score for b in results.brackets]
        avg_score = sum(scores) / len(scores) if scores else 0

        excellent = gs.excellent_brackets
        excellent_rate = (excellent / gs.total_brackets * 100) if gs.total_brackets > 0 else 0
        quality_rate = round(avg_score, 2)

        brackets_data = []
        for b in results.brackets:
            bracket_info = {
                "id": b.id,
                "numero": b.numero,
                "area": b.area,
                "tipo": b.tipo,
                "score": b.score,
                    "competidores": [
                        {
                            "id": c.id,
                            "nombre": c.nombre,
                            "apellido": c.apellido,
                            "edad": c.edad,
                            "categoria_edad": c.categoria_edad,
                            "sexo": c.sexo,
                            "peso_kg": c.peso_kg,
                            "estatura_cm": c.estatura_cm,
                            "modalidad": c.modalidad,
                            "doyang": c.doyang,
                            "bloque": c.bloque,
                            "cinta_block": c.cinta_block,
                        }
                        for c in b.competidores
                    ]
            }

            if b.score_breakdown:
                bracket_info["score_breakdown"] = {
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
                bracket_info["failure_reasons"] = b.failure_reasons

            brackets_data.append(bracket_info)

        unpaired_data = [
            {
                "nombre": u.competidor.nombre,
                "apellido": u.competidor.apellido,
                "bloque": u.competidor.bloque,
                "cinta_block": u.competidor.cinta_block,
                "edad": u.competidor.edad,
                "peso_kg": u.competidor.peso_kg,
                "estatura_cm": u.competidor.estatura_cm,
                "doyang": u.competidor.doyang,
                "razon": u.razon,
            }
            for u in results.unpaired
        ]

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
            "excellent_rate": round(excellent_rate, 2),
            "quality_rate": round(quality_rate, 2),
            "avg_score": round(avg_score, 2),
            "sin_rival": gs.sin_rival_total,
            "status": "success",
            "errors": errors,
            "elapsed": round(time.time() - start_time, 3),
            "brackets": brackets_data,
            "unpaired": unpaired_data,
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "type": "random",
            "elapsed": round(time.time() - start_time, 3),
        }

    finally:
        if filepath and os.path.exists(filepath):
            try:
                os.unlink(filepath)
            except:
                pass

def run_random_tests(count=25, edge_case_prob=0.01):
    results = []
    for i in range(count):
        result = run_random_test(edge_case_prob)
        result["name"] = f"random_{i + 1}"
        results.append(result)

    successful = [r for r in results if r.get("status") == "success"]
    failed = [r for r in results if r.get("status") == "error"]

    avg_pairing = sum(r.get("pairing_rate", 0) for r in successful) / len(successful) if successful else 0
    avg_quality = sum(r.get("quality_rate", 0) for r in successful) / len(successful) if successful else 0
    avg_excellent = sum(r.get("excellent_rate", 0) for r in successful) / len(successful) if successful else 0
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
        "avg_excellent_rate": round(avg_excellent, 2),
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
    report = run_random_tests(5, edge_case_prob=0.01)
    print(f"Random tests: {report['summary']}")
