"""
LLM Report Generator for Algorithm Analysis
Generates detailed Markdown reports for diagnosing pairing algorithm issues
"""

from collections import Counter
from typing import Dict, List, Any
from datetime import datetime


CINTA_ORDER = [
    "Pre-Taekwondo", "Blanca", "Amarilla", "Verde", "Azul",
    "Marrón", "Roja", "Negra (Poom)", "Negra (Dan)"
]


def cinta_diff(c1: str, c2: str) -> int:
    """Calcula la diferencia de cinta (-1, 0, 1, 2, etc.)"""
    try:
        i1 = CINTA_ORDER.index(c1)
        i2 = CINTA_ORDER.index(c2)
        return abs(i1 - i2)
    except (ValueError, IndexError):
        return -1


def analyze_failure_reasons(bracket: dict) -> List[str]:
    """Analizar razones por las cuales un bracket tiene baja calidad"""
    reasons = []
    breakdown = bracket.get("score_breakdown", {})
    
    if not breakdown:
        return reasons
    
    # New scoring: 0-100 scale
    # Low scores: edad < 8, peso < 10, estatura < 6
    if breakdown.get("edad_score", 25) < 8:
        reasons.append(f"edad_diff={breakdown.get('edad_diff', 0)} anos")
    if breakdown.get("peso_score", 40) < 10:
        reasons.append(f"peso_diff={breakdown.get('peso_diff', 0)}kg")
    if breakdown.get("estatura_score", 25) < 6:
        reasons.append(f"estatura_diff={breakdown.get('estatura_diff', 0)}cm")
    
    return reasons


def analyze_unpaired_reasons(unpaired: List[dict]) -> Dict[str, int]:
    """Analizar motivos de no emparejamiento"""
    reasons = Counter()
    
    for u in unpaired:
        reason = u.get("razon", "Unknown")
        if "edad" in reason.lower():
            reasons["diferencia_edad"] += 1
        elif "peso" in reason.lower():
            reasons["diferencia_peso"] += 1
        elif "estatura" in reason.lower():
            reasons["diferencia_estatura"] += 1
        elif "modalidad" in reason.lower():
            reasons["modalidad_incompatible"] += 1
        elif "compatible" in reason.lower():
            reasons["no_hay_rival_compatible"] += 1
        else:
            reasons["sin_rival"] += 1
    
    return dict(reasons)


def analyze_cinta_distribution(tests: List[dict]) -> dict:
    """Analizar distribución de mezcla de cintas en brackets"""
    misma_cinta = 0
    adyacente = 0
    diferencia_2 = 0
    mayor = 0
    total = 0

    for test in tests:
        for bracket in test.get("brackets", []):
            comps = bracket.get("competidores", [])
            if len(comps) < 2:
                continue
            total += 1
            cintas = [c.get("cinta_block", "") for c in comps]
            max_diff = 0
            for i in range(len(cintas)):
                for j in range(i + 1, len(cintas)):
                    d = cinta_diff(cintas[i], cintas[j])
                    if d >= 0:
                        max_diff = max(max_diff, d)
            if max_diff == 0:
                misma_cinta += 1
            elif max_diff == 1:
                adyacente += 1
            elif max_diff == 2:
                diferencia_2 += 1
            else:
                mayor += 1

    return {
        "total": total,
        "misma_cinta": misma_cinta,
        "misma_cinta_pct": round(misma_cinta / total * 100, 1) if total else 0,
        "adyacente": adyacente,
        "adyacente_pct": round(adyacente / total * 100, 1) if total else 0,
        "diferencia_2": diferencia_2,
        "diferencia_2_pct": round(diferencia_2 / total * 100, 1) if total else 0,
        "mayor": mayor,
        "mayor_pct": round(mayor / total * 100, 1) if total else 0,
    }


def analyze_score_by_nivel(tests: List[dict]) -> dict:
    """Score promedio por nivel de relajación"""
    niveles = {
        "etapa2": [], "ronda1": [], "ronda2": [], "ronda3": [],
        "ronda4": [], "nivel5": [], "nivel6": [], "nivel7": [],
        "post_proc": []
    }

    for test in tests:
        for bracket in test.get("brackets", []):
            ronda = bracket.get("ronda_origen", "etapa2")
            if ronda in niveles:
                niveles[ronda].append(bracket.get("score", 0))
            elif "post" in ronda.lower():
                niveles["post_proc"].append(bracket.get("score", 0))
            else:
                niveles["ronda4"].append(bracket.get("score", 0))

    result = {}
    for nivel, scores in niveles.items():
        if scores:
            result[nivel] = {
                "count": len(scores),
                "avg_score": round(sum(scores) / len(scores), 2),
                "min": min(scores),
                "max": max(scores)
            }
        else:
            result[nivel] = {"count": 0, "avg_score": 0, "min": 0, "max": 0}

    return result


def calculate_percentile(data: List[float], p: float) -> float:
    """Calcular percentil p de una lista de numeros"""
    if not data:
        return 0
    s = sorted(data)
    idx = int(len(s) * p / 100)
    idx = min(idx, len(s) - 1)
    return round(s[idx], 2)


def calculate_component_metrics(tests: List[dict]) -> dict:
    """Calcular distribucion de metricas por componente"""
    edad_diffs = []
    peso_diffs = []
    estatura_diffs = []
    edad_scores = []
    peso_scores = []
    estatura_scores = []
    doyang_penalty_count = 0
    total_brackets = 0
    
    for test in tests:
        for bracket in test.get("brackets", []):
            total_brackets += 1
            bd = bracket.get("score_breakdown", {})
            
            if bd:
                edad_diffs.append(bd.get("edad_diff", 0))
                peso_diffs.append(bd.get("peso_diff", 0))
                estatura_diffs.append(bd.get("estatura_diff", 0))
                edad_scores.append(bd.get("edad_score", 0))
                peso_scores.append(bd.get("peso_score", 0))
                estatura_scores.append(bd.get("estatura_score", 0))
                if bd.get("doyang_bonus", 0) > 0:
                    doyang_penalty_count += 1
    
    n = len(edad_diffs) if edad_diffs else 1
    
    return {
        "total_brackets": total_brackets,
        "edad": {
            "avg": round(sum(edad_diffs) / n, 2) if n > 0 else 0,
            "p25": calculate_percentile(edad_diffs, 25),
            "p50": calculate_percentile(edad_diffs, 50),
            "p75": calculate_percentile(edad_diffs, 75),
            "p95": calculate_percentile(edad_diffs, 95),
            "max": max(edad_diffs) if edad_diffs else 0
        },
        "peso": {
            "avg": round(sum(peso_diffs) / n, 2) if n > 0 else 0,
            "p25": calculate_percentile(peso_diffs, 25),
            "p50": calculate_percentile(peso_diffs, 50),
            "p75": calculate_percentile(peso_diffs, 75),
            "p95": calculate_percentile(peso_diffs, 95),
            "max": max(peso_diffs) if peso_diffs else 0
        },
        "estatura": {
            "avg": round(sum(estatura_diffs) / n, 2) if n > 0 else 0,
            "p25": calculate_percentile(estatura_diffs, 25),
            "p50": calculate_percentile(estatura_diffs, 50),
            "p75": calculate_percentile(estatura_diffs, 75),
            "p95": calculate_percentile(estatura_diffs, 95),
            "max": max(estatura_diffs) if estatura_diffs else 0
        },
        "scores": {
            "edad_avg": round(sum(edad_scores) / n, 2) if n > 0 else 0,
            "peso_avg": round(sum(peso_scores) / n, 2) if n > 0 else 0,
            "estatura_avg": round(sum(estatura_scores) / n, 2) if n > 0 else 0,
            "doyang_penalty_count": doyang_penalty_count,
            "doyang_penalty_pct": round(doyang_penalty_count / n * 100, 1) if n > 0 else 0
        }
    }


def extract_low_quality_brackets(tests: List[dict], threshold: float = 30.0) -> List[dict]:
    """Extraer brackets de baja calidad (score < 30 = muy bajo)"""
    low_quality = []
    
    for test in tests:
        test_name = test.get("name", "unknown")
        for bracket in test.get("brackets", []):
            if bracket.get("score", 0) < threshold:
                comps = bracket.get("competidores", [])
                breakdown = bracket.get("score_breakdown", {})
                
                comps_info = []
                for c in comps:
                    comps_info.append({
                        "nombre": c.get("nombre", ""),
                        "apellido": c.get("apellido", ""),
                        "edad": c.get("edad", 0),
                        "peso_kg": c.get("peso_kg", c.get("peso", 0)),
                        "estatura_cm": c.get("estatura_cm", c.get("estatura", 0)),
                        "doyang": c.get("doyang", "")
                    })
                
                failure_reasons = analyze_failure_reasons(bracket)
                
                low_quality.append({
                    "bracket_id": bracket.get("numero", 0),
                    "test": test_name,
                    "bloque": comps[0].get("bloque", "Unknown") if comps else "Unknown",
                    "tipo": bracket.get("tipo", "unknown"),
                    "nivel_aprobacion": bracket.get("nivel_aprobacion", "unknown"),
                    "ronda_origen": bracket.get("ronda_origen", "unknown"),
                    "score": bracket.get("score", 0),
                    "competidores": comps_info,
                    "breakdown": breakdown,
                    "failure_reasons": failure_reasons
                })
    
    return low_quality


def analyze_unpaired(tests: List[dict]) -> dict:
    """Analizar competidores no emparejados con razones detalladas"""
    by_bloque = {}
    by_reason = Counter()
    by_cinta = Counter()
    profiles = []
    total_unpaired = 0
    failure_details = []

    for test in tests:
        for u in test.get("unpaired", []):
            total_unpaired += 1
            bloque = u.get("bloque", "Unknown")
            cinta = u.get("cinta_block", "Unknown")
            reason = u.get("razon", "Unknown")
            nombre = u.get("nombre", "")
            apellido = u.get("apellido", "")

            if bloque not in by_bloque:
                by_bloque[bloque] = {"count": 0, "competitors": []}
            by_bloque[bloque]["count"] += 1
            by_bloque[bloque]["competitors"].append({
                "nombre": nombre,
                "apellido": apellido,
                "edad": u.get("edad", 0),
                "peso_kg": u.get("peso_kg", u.get("peso", 0)),
                "estatura_cm": u.get("estatura_cm", u.get("estatura", 0)),
                "cinta_block": cinta,
                "doyang": u.get("doyang", ""),
                "razon": reason
            })

            by_reason[reason] += 1
            by_cinta[cinta] += 1

            razon_detallada = []
            if "compatible" in reason.lower():
                razon_detallada.append("sin_rival_en_bloque")
            else:
                if bloques_sin_rival_posibles(u, test):
                    razon_detallada.append("competidores_incompatibles_en_peso")
                else:
                    razon_detallada.append("ninguno_cumple_restricciones")

            failure_details.append({
                "nombre": nombre,
                "apellido": apellido,
                "bloque": bloque,
                "cinta_block": cinta,
                "edad": u.get("edad", 0),
                "peso_kg": u.get("peso_kg", u.get("peso", 0)),
                "estatura_cm": u.get("estatura_cm", u.get("estatura", 0)),
                "doyang": u.get("doyang", ""),
                "razon": reason,
                "razones_detalladas": razon_detallada
            })

            profiles.append({
                "bloque": bloque,
                "edad": u.get("edad", 0),
                "peso_kg": u.get("peso_kg", u.get("peso", 0)),
                "razon": reason
            })

    return {
        "total": total_unpaired,
        "by_bloque": by_bloque,
        "by_reason": dict(by_reason.most_common(10)),
        "by_cinta": dict(by_cinta.most_common(10)),
        "profiles": profiles[:20],
        "failure_details": failure_details[:30]
    }


def bloques_sin_rival_posibles(unpaired: dict, test: dict) -> list:
    """Determinar qué bloques podrían tener al competidor sin rival"""
    resultados = []
    for b in test.get("brackets", []):
        comps = b.get("competidores", [])
        if not comps:
            continue
        if comps[0].get("bloque") != unpaired.get("bloque"):
            continue
        diffs = []
        for c in comps:
            peso_u = unpaired.get("peso_kg", unpaired.get("peso", 0))
            peso_c = c.get("peso_kg", c.get("peso", 0))
            peso_diff = abs(peso_c - peso_u)
            if peso_diff > 7.5:
                diffs.append(f"peso: {round(peso_diff, 1)}kg > 7.5kg")
            edad_diff = abs(c.get("edad", 0) - unpaired.get("edad", 0))
            if edad_diff > 3:
                diffs.append(f"edad: {edad_diff} anos > 3")
        if diffs:
            resultados.append({" bracket_id": b.get("numero"), "razones": diffs})
    return resultados


def extract_unpaired_detailed(tests: List[dict]) -> List[dict]:
    """Extraer detalle completo de competidores sin rival"""
    resultados = []

    for test in tests:
        test_name = test.get("name", "unknown")
        for u in test.get("unpaired", []):
            nombre = u.get("nombre", "")
            apellido = u.get("apellido", "")
            bloque = u.get("bloque", "Unknown")
            cinta = u.get("cinta_block", "Unknown")
            edad = u.get("edad", 0)
            peso_kg = u.get("peso_kg", u.get("peso", 0))
            estatura_cm = u.get("estatura_cm", u.get("estatura", 0))
            doyang = u.get("doyang", "")
            reason = u.get("razon", "Unknown")

            intentos = []
            for b in test.get("brackets", []):
                comps = b.get("competidores", [])
                if not comps:
                    continue
                if comps[0].get("bloque") != bloque:
                    continue
                for c in comps:
                    razones = []
                    c_peso = c.get("peso_kg", c.get("peso", 0))
                    if abs(c_peso - peso_kg) > 7.5:
                        razones.append(f"peso_abs: {round(abs(c_peso - peso_kg), 1)}kg > 7.5kg")
                    if cinta != c.get("cinta_block", ""):
                        razones.append(f"cintas: {cinta} vs {c.get('cinta_block', '')}")
                    if abs(c.get("edad", 0) - edad) > 3:
                        razones.append(f"edad_cat: {edad} vs {c.get('edad', 0)}")
                    if razones:
                        intentos.append({
                            "competidor": f"{c.get('nombre', '')} {c.get('apellido', '')}",
                            "razones": razones,
                            "bracket_id": b.get("numero")
                        })

            razones_fallo = []
            if "compatible" in reason.lower():
                razones_fallo.append("no_hay_rival_compatible_en_bloque")
            else:
                if "peso" in reason.lower():
                    razones_fallo.append("restriccion_peso_mayor")
                if "edad" in reason.lower():
                    razones_fallo.append("restriccion_edad_mayor")
                if "cinta" in reason.lower():
                    razones_fallo.append("restriccion_cinta_no_cumple")

            ultimo_intento = intentos[0] if intentos else None

            resultados.append({
                "test": test_name,
                "nombre": nombre,
                "apellido": apellido,
                "bloque": bloque,
                "cinta_block": cinta,
                "edad": edad,
                "peso_kg": peso_kg,
                "estatura_cm": estatura_cm,
                "doyang": doyang,
                "razon": reason,
                "razones_fallo": razones_fallo,
                "ultimo_intento": ultimo_intento,
                "intentos": intentos[:5]
            })

    return resultados


def analyze_by_category(tests: List[dict]) -> dict:
    """Agrupar metricas por bloque y cinta"""
    categories = {}
    
    for test in tests:
        for bracket in test.get("brackets", []):
            for comp in bracket.get("competidores", []):
                bloque = comp.get("bloque", "Unknown")
                cinta = comp.get("cinta_block", "Unknown")
                key = f"{bloque}"
                
                if key not in categories:
                    categories[key] = {
                        "competitors": 0,
                        "brackets": 0,
                        "scores": [],
                        "failure_reasons": []
                    }
                
                categories[key]["competitors"] += 1
                categories[key]["brackets"] += 1
                categories[key]["scores"].append(bracket.get("score", 0))
                categories[key]["failure_reasons"].extend(analyze_failure_reasons(bracket))
    
    for key, data in categories.items():
        n = len(data["scores"]) if data["scores"] else 1
        data["avg_score"] = round(sum(data["scores"]) / n, 2)
        
        reason_counts = Counter(data["failure_reasons"])
        data["top_problems"] = reason_counts.most_common(3)
    
    return categories


def extract_zero_score_brackets(tests: List[dict]) -> List[dict]:
    """Extraer brackets con score == 0 con analisis detallado de fallos"""
    zero_score_brackets = []
    
    for test in tests:
        test_name = test.get("name", "unknown")
        for bracket in test.get("brackets", []):
            if bracket.get("score", -1) == 0:
                comps = bracket.get("competidores", [])
                
                categorias_edad = list(set(c.get("categoria_edad", "Unknown") for c in comps))
                sexos = list(set(c.get("sexo", c.get("sexo", "?")) for c in comps))
                cintas = list(set(c.get("cinta_block", "Unknown") for c in comps))
                
                age_diffs = []
                peso_diffs = []
                est_diffs = []
                
                for i in range(len(comps)):
                    for j in range(i + 1, len(comps)):
                        c1, c2 = comps[i], comps[j]
                        age_diffs.append(abs(c1.get("edad", 0) - c2.get("edad", 0)))
                        p1 = c1.get("peso_kg", c1.get("peso", 0))
                        p2 = c2.get("peso_kg", c2.get("peso", 0))
                        peso_diffs.append(abs(p1 - p2))
                        e1 = c1.get("estatura_cm", c1.get("estatura", 0))
                        e2 = c2.get("estatura_cm", c2.get("estatura", 0))
                        est_diffs.append(abs(e1 - e2))
                
                max_age_diff = max(age_diffs) if age_diffs else 0
                max_peso_diff = max(peso_diffs) if peso_diffs else 0
                max_est_diff = max(est_diffs) if est_diffs else 0
                
                nivel = bracket.get("nivel_aprobacion", "unknown")
                ronda = bracket.get("ronda_origen", "unknown")
                
                failure_reasons = bracket.get("failure_reasons", [])
                
                primera_falla = failure_reasons[0] if failure_reasons else "desconocido"
                
                comps_info = []
                for c in comps:
                    comps_info.append({
                        "nombre": c.get("nombre", ""),
                        "apellido": c.get("apellido", ""),
                        "edad": c.get("edad", 0),
                        "categoria_edad": c.get("categoria_edad", "Unknown"),
                        "sexo": c.get("sexo", "?"),
                        "peso_kg": c.get("peso_kg", c.get("peso", 0)),
                        "estatura_cm": c.get("estatura_cm", c.get("estatura", 0)),
                        "cinta_block": c.get("cinta_block", "Unknown"),
                        "doyang": c.get("doyang", ""),
                    })
                
                zero_score_brackets.append({
                    "test": test_name,
                    "bracket_id": bracket.get("numero", 0),
                    "bloque": comps[0].get("bloque", "Unknown") if comps else "Unknown",
                    "ronda_origen": ronda,
                    "nivel_aprobacion": nivel,
                    "competidores": comps_info,
                    "categorias_edad": categorias_edad,
                    "categorias_diferentes": len(categorias_edad) > 1,
                    "sexos": sexos,
                    "sexos_diferentes": len(sexos) > 1,
                    "cintas": cintas,
                    "diferencias": {
                        "edad": max_age_diff,
                        "peso": round(max_peso_diff, 2),
                        "estatura": max_est_diff,
                    },
                    "failure_reasons": failure_reasons,
                    "primera_falla": primera_falla,
                    "tipo_falla": _clasificar_falla(failure_reasons),
                })
    
    return zero_score_brackets


def _clasificar_falla(reasons: List[str]) -> str:
    """Clasificar el tipo de falla principal"""
    if not reasons:
        return "desconocido"
    
    primera = reasons[0].lower()
    
    if "categoria_edad" in primera:
        return "categoria_edad_diferente"
    elif "sexo" in primera:
        return "sexo_diferente"
    elif "cinta" in primera:
        return "cinta_no_permitida"
    elif "peso" in primera:
        return "peso_limite_excedido"
    elif "edad" in primera and "limite" in primera:
        return "edad_limite_excedido"
    elif "estatura" in primera:
        return "estatura_limite_excedido"
    elif "penalizacion" in primera or "score_negativo" in primera:
        return "penalizaciones_llevaron_a_cero"
    else:
        return "otra"


def generate_llm_markdown(report: dict) -> str:
    """Generar reporte completo en formato Markdown"""
    
    tests = report.get("tests", [])
    summary = report.get("summary", {})
    
    lines = []
    lines.append("# Reporte de Analisis - Algoritmo de Emparejamiento")
    lines.append("")
    lines.append(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Total pruebas ejecutadas:** {summary.get('total_runs', len(tests))}")
    lines.append(f"**Sistema de puntaje:** 0-100 puntos")
    lines.append(f"  - Peso: 40 pts max (prioridad alta)")
    lines.append(f"  - Estatura: 25 pts max")
    lines.append(f"  - Edad: 25 pts max (variable por categoria)")
    lines.append(f"  - Doyang: +10% multiplicativo si diferente escuela")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # 1. RESUMEN EJECUTIVO
    lines.append("## 1. Resumen Ejecutivo")
    lines.append("")
    
    if tests:
        sorted_by_pairing = sorted(tests, key=lambda x: x.get("pairing_rate", 0), reverse=True)
        sorted_by_score = sorted(tests, key=lambda x: x.get("avg_score", 0) or 0, reverse=True)
        
        best_test = sorted_by_pairing[0]
        worst_test = sorted_by_pairing[-1]
        
        all_pairing = [t.get("pairing_rate", 0) for t in tests]
        all_quality = [t.get("quality_rate", 0) for t in tests]
        
        avg_pairing = round(sum(all_pairing) / len(all_pairing), 1) if all_pairing else 0
        avg_quality = round(sum(all_quality) / len(all_quality), 1) if all_quality else 0
    else:
        best_test = worst_test = {"name": "N/A", "pairing_rate": 0}
        avg_pairing = avg_quality = 0
    
    lines.append("| Metrica | Valor |")
    lines.append("|---------|-------|")
    lines.append(f"| Tasa emparejamiento global | {avg_pairing}% |")
    lines.append(f"| Calidad global | {avg_quality}% |")
    lines.append(f"| Mejor prueba | {best_test.get('name', 'N/A')} ({best_test.get('pairing_rate', 0)}%) |")
    lines.append(f"| Peor prueba | {worst_test.get('name', 'N/A')} ({worst_test.get('pairing_rate', 0)}%) |")
    lines.append("")
    
    all_failure_reasons = Counter()
    for test in tests:
        for b in test.get("brackets", []):
            for reason in analyze_failure_reasons(b):
                all_failure_reasons[reason] += 1
        for u in test.get("unpaired", []):
            reason = u.get("razon", "")
            if "compatible" in reason.lower():
                all_failure_reasons["no_hay_rival_compatible"] += 1
    
    lines.append("### Top Razones de Fallo")
    lines.append("")
    for i, (reason, count) in enumerate(all_failure_reasons.most_common(5), 1):
        lines.append(f"{i}. `{reason}` ({count} casos)")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # 2. TABLA COMPARATIVA
    lines.append("## 📊 2. Tabla Comparativa de Pruebas")
    lines.append("")
    lines.append("| Prueba | Comp | Brackets | Emparej% | Calidad% | Score | Excl | Baja | Sin Rival |")
    lines.append("|--------|------|----------|----------|----------|-------|------|------|----------|")
    
    for t in tests:
        name = t.get("name", "N/A")
        comps = t.get("total_competitors", 0)
        brackets = t.get("total_brackets", 0)
        pairing = t.get("pairing_rate", 0)
        quality = t.get("quality_rate", 0)
        score = t.get("avg_score", 0) or 0
        excellent = t.get("excellent", 0)
        low_q = t.get("low_quality", 0)
        unpaired = t.get("sin_rival", 0)
        
        lines.append(f"| {name} | {comps} | {brackets} | {pairing}% | {quality}% | {round(score, 2)} | {excellent} | {low_q} | {unpaired} |")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # 3. DISTRIBUCION POR RONDA Y COLOR
    lines.append("## 3. Distribucion por Ronda y Color")
    lines.append("")
    
    rounds = {"etapa2": 0, "ronda1": 0, "ronda2": 0, "ronda3": 0, "ronda4": 0}
    colors = {"verde_claro": 0, "amarillo": 0, "naranja": 0, "rojo": 0}
    
    for test in tests:
        for b in test.get("brackets", []):
            ronda = b.get("ronda_origen", "etapa2")
            rounds[ronda] = rounds.get(ronda, 0) + 1
            color = b.get("nivel_aprobacion", "verde_claro")
            colors[color] = colors.get(color, 0) + 1
    
    total_brackets = sum(rounds.values()) or 1
    
    lines.append("### Por Ronda")
    lines.append("")
    lines.append("| Ronda | Brackets | Porcentaje | Color |")
    lines.append("|-------|----------|------------|-------|")
    lines.append(f"| Etapa 2 (optimo) | {rounds['etapa2']} | {round(rounds['etapa2']/total_brackets*100,1)}% | Verde claro |")
    lines.append(f"| Ronda 1 (estandar) | {rounds['ronda1']} | {round(rounds['ronda1']/total_brackets*100,1)}% | Verde claro |")
    lines.append(f"| Ronda 2 (relajado) | {rounds['ronda2']} | {round(rounds['ronda2']/total_brackets*100,1)}% | Amarillo |")
    lines.append(f"| Ronda 3 (cintas ady.) | {rounds['ronda3']} | {round(rounds['ronda3']/total_brackets*100,1)}% | Naranja |")
    lines.append(f"| Ronda 4 (forzado) | {rounds['ronda4']} | {round(rounds['ronda4']/total_brackets*100,1)}% | Rojo |")
    lines.append("")
    
    lines.append("### Por Color")
    lines.append("")
    lines.append("| Color | Significado | Brackets |")
    lines.append("|-------|-------------|----------|")
    lines.append(f"| Verde claro | Estandar, aprobado automatico | {colors.get('verde_claro', 0)} |")
    lines.append(f"| Amarillo | Relajado, solo notificacion | {colors.get('amarillo', 0)} |")
    lines.append(f"| Naranja | Cintas adyacentes, requiere colaborador | {colors.get('naranja', 0)} |")
    lines.append(f"| Rojo | Forzado, requiere coordinadora | {colors.get('rojo', 0)} |")
    lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # 4. ANALISIS POR CATEGORIA
    lines.append("## 4. Analisis por Categoria (Bloque)")
    lines.append("")
    
    categories = analyze_by_category(tests)
    for bloque, data in sorted(categories.items()):
        lines.append(f"### {bloque}")
        lines.append("")
        lines.append(f"- **Competidores:** {data['competitors']}")
        lines.append(f"- **Brackets:** {data['brackets']}")
        lines.append(f"- **Score promedio:** {data['avg_score']}")
        if data["top_problems"]:
            lines.append("- **Problemas frecuentes:**")
            for reason, count in data["top_problems"]:
                lines.append(f"  - `{reason}` ({count} veces)")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # 4. BRACKETS DE BAJA CALIDAD
    lines.append("## 4. Brackets de Baja Calidad (< 30 puntos)")
    lines.append("")
    
    low_quality = extract_low_quality_brackets(tests, threshold=30.0)
    lines.append(f"**Total:** {len(low_quality)} brackets de baja calidad (score < 30)")
    lines.append("")
    
    for i, bq in enumerate(low_quality[:10], 1):
        lines.append(f"### {i}. Bracket #{bq['bracket_id']} ({bq['test']}, {bq['bloque']})")
        lines.append("")
        lines.append(f"**Tipo:** {bq['tipo']} | **Ronda:** {bq.get('ronda_origen', 'N/A')} | **Color:** {bq.get('nivel_aprobacion', 'N/A')} | **Score:** {bq['score']}/100")
        lines.append("")
        lines.append("**Competidores:**")
        for c in bq["competidores"]:
            lines.append(f"- {c['nombre']} {c['apellido']}: {c['edad']} anos, {c.get('peso_kg', c.get('peso', 0))}kg, {c.get('estatura_cm', c.get('estatura', 0))}cm, {c['doyang']}")
        lines.append("")
        
        bd = bq.get("breakdown", {})
        if bd:
            lines.append("**Desglose:**")
            lines.append(f"- Edad: diff={bd.get('edad_diff', 0)} anos, score={bd.get('edad_score', 0)}/25 pts")
            lines.append(f"- Peso: diff={bd.get('peso_diff', 0)}kg, score={bd.get('peso_score', 0)}/40 pts")
            lines.append(f"- Estatura: diff={bd.get('estatura_diff', 0)}cm, score={bd.get('estatura_score', 0)}/25 pts")
            lines.append(f"- Doyang penalty: -{bd.get('doyang_penalty', 0)} pts")
            lines.append("")
        
        if bq["failure_reasons"]:
            lines.append("**Razones de fallo:** " + ", ".join(f"`{r}`" for r in bq["failure_reasons"]))
        lines.append("")
    
    if len(low_quality) > 10:
        lines.append(f"_... y {len(low_quality) - 10} mas_")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # 5. ANALISIS DE UNPAIRED
    lines.append("## 5. Analisis de Competidores Sin Rival")
    lines.append("")
    
    unpaired_analysis = analyze_unpaired(tests)
    lines.append(f"**Total no emparejados:** {unpaired_analysis['total']}")
    lines.append("")
    
    lines.append("### Por Bloque")
    lines.append("")
    lines.append("| Bloque | Cantidad | Porcentaje |")
    lines.append("|--------|----------|------------|")
    total_up = unpaired_analysis["total"] or 1
    for bloque, data in sorted(unpaired_analysis["by_bloque"].items(), key=lambda x: x[1]["count"], reverse=True):
        pct = round(data["count"] / total_up * 100, 1)
        lines.append(f"| {bloque} | {data['count']} | {pct}% |")
    lines.append("")
    
    lines.append("### Por Motivo")
    lines.append("")
    lines.append("| Motivo | Casos |")
    lines.append("|--------|-------|")
    for reason, count in sorted(unpaired_analysis["by_reason"].items(), key=lambda x: x[1], reverse=True):
        lines.append(f"| {reason} | {count} |")
    lines.append("")

    cinta_data = unpaired_analysis.get("by_cinta", {})
    if cinta_data:
        lines.append("### Por Cinta (sin rival)")
        lines.append("")
        lines.append("| Cinta | Sin Rival |")
        lines.append("|--------|----------|")
        for cinta, count in cinta_data.items():
            lines.append(f"| {cinta} | {count} |")
        lines.append("")

    unpaired_detailed = extract_unpaired_detailed(tests)
    if unpaired_detailed:
        lines.append("### Competidores Sin Rival - Detalle")
        lines.append("")
        for i, u in enumerate(unpaired_detailed[:15], 1):
            lines.append(f"**{i}. {u['nombre']} {u['apellido']}** ({u['bloque']}, {u['cinta_block']})")
            lines.append(f"- Edad: {u['edad']}, Peso: {u.get('peso_kg', u.get('peso', 0))} kg, Estatura: {u.get('estatura_cm', u.get('estatura', 0))} cm")
            lines.append(f"- **Razón:** {u['razon']}")
            if u["razones_fallo"]:
                lines.append(f"- **Razones de fallo:** {', '.join(u['razones_fallo'])}")
            if u["ultimo_intento"]:
                lines.append(f"- **Último intento con:** {u['ultimo_intento']['competidor']} (razones: {', '.join(u['ultimo_intento']['razones'])})")
            lines.append("")

    lines.append("---")
    lines.append("")

    # 5B. DISTRIBUCION DE MEZCLA DE CINTAS
    lines.append("## 5B. Distribucion de Mezcla de Cintas")
    lines.append("")

    cinta_dist = analyze_cinta_distribution(tests)
    lines.append(f"**Total brackets analizados:** {cinta_dist['total']}")
    lines.append("")
    lines.append("| Tipo de Mezcla | Cantidad | Porcentaje |")
    lines.append("|---------------|----------|------------|")
    lines.append(f"| Misma cinta exacta | {cinta_dist['misma_cinta']} | {cinta_dist['misma_cinta_pct']}% |")
    lines.append(f"| Cintas adyacentes (diff 1) | {cinta_dist['adyacente']} | {cinta_dist['adyacente_pct']}% |")
    lines.append(f"| Diferencia 2 | {cinta_dist['diferencia_2']} | {cinta_dist['diferencia_2_pct']}% |")
    lines.append(f"| Mayor diferencia | {cinta_dist['mayor']} | {cinta_dist['mayor_pct']}% |")
    lines.append("")

    lines.append("---")
    lines.append("")

    # 5C. SCORE PROMEDIO POR NIVEL DE RELAJACION
    lines.append("## 5C. Score Promedio por Nivel de Relajacion")
    lines.append("")

    score_by_nivel = analyze_score_by_nivel(tests)
    lines.append("| Nivel | Brackets | Score Avg | Min | Max |")
    lines.append("|-------|----------|-----------|-----|-----|")
    for nivel in ["etapa2", "ronda1", "ronda2", "ronda3", "ronda4", "nivel5", "nivel6", "nivel7", "post_proc"]:
        data = score_by_nivel.get(nivel, {})
        nombre_nivel = {"etapa2": "Etapa 2", "ronda1": "Ronda 1", "ronda2": "Ronda 2", "ronda3": "Ronda 3", "ronda4": "Ronda 4", "nivel5": "Nivel 5", "nivel6": "Nivel 6", "nivel7": "Nivel 7", "post_proc": "Post-Procesamiento"}.get(nivel, nivel)
        lines.append(f"| {nombre_nivel} | {data.get('count', 0)} | {data.get('avg_score', 0)} | {data.get('min', 0)} | {data.get('max', 0)} |")
    lines.append("")

    lines.append("---")
    lines.append("")

    # 6. METRICAS POR COMPONENTE
    lines.append("## 6. Metricas por Componente (sobre 100 pts)")
    lines.append("")
    
    metrics = calculate_component_metrics(tests)
    
    lines.append("### Distribucion de Diferencias")
    lines.append("")
    lines.append("| Componente | Avg | P50 | P75 | P95 | Max |")
    lines.append("|------------|-----|-----|-----|-----|-----|")
    lines.append(f"| Edad (anos) | {metrics['edad']['avg']} | {metrics['edad']['p50']} | {metrics['edad']['p75']} | {metrics['edad']['p95']} | {metrics['edad']['max']} |")
    lines.append(f"| Peso (kg) | {metrics['peso']['avg']} | {metrics['peso']['p50']} | {metrics['peso']['p75']} | {metrics['peso']['p95']} | {metrics['peso']['max']} |")
    lines.append(f"| Estatura (cm) | {metrics['estatura']['avg']} | {metrics['estatura']['p50']} | {metrics['estatura']['p75']} | {metrics['estatura']['p95']} | {metrics['estatura']['max']} |")
    lines.append("")
    
    lines.append("### Scores Promedio por Componente")
    lines.append("")
    lines.append("| Componente | Score Promedio | Maximo |")
    lines.append("|------------|----------------|--------|")
    lines.append(f"| Edad | {metrics['scores']['edad_avg']} | 25 |")
    lines.append(f"| Peso | {metrics['scores']['peso_avg']} | 40 |")
    lines.append(f"| Estatura | {metrics['scores']['estatura_avg']} | 25 |")
    lines.append(f"| Doyang penalty | -{metrics['scores']['doyang_penalty_pct']}% | -10% |")
    lines.append("")
    lines.append(f"**Total brackets analizados:** {metrics['total_brackets']}")
    lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # 6B. BRACKETS CON SCORE == 0
    lines.append("## 6B. Brackets con Score == 0 (Fallo Total)")
    lines.append("")
    
    zero_score = extract_zero_score_brackets(tests)
    lines.append(f"**Total:** {len(zero_score)} brackets con score 0")
    lines.append("")
    
    if zero_score:
        tipo_fallas = Counter(b["tipo_falla"] for b in zero_score)
        lines.append("### Resumen de Tipos de Falla")
        lines.append("")
        lines.append("| Tipo de Falla | Cantidad |")
        lines.append("|---------------|----------|")
        for tipo, count in tipo_fallas.most_common():
            lines.append(f"| {tipo} | {count} |")
        lines.append("")
        
        lines.append("### Detalle de Cada Bracket con Score 0")
        lines.append("")
        
        for i, z in enumerate(zero_score[:20], 1):
            lines.append(f"#### {i}. Bracket #{z['bracket_id']} ({z['test']})")
            lines.append("")
            lines.append(f"**Bloque:** {z['bloque']} | **Ronda:** {z['ronda_origen']} | **Nivel:** {z['nivel_aprobacion']}")
            lines.append("")
            
            lines.append("**Categorias de edad de competidores:**")
            for cat in z["categorias_edad"]:
                lines.append(f"- `{cat}`")
            if z["categorias_diferentes"]:
                lines.append("⚠️ **PROBLEMA:** Categorias DIFERENTES en mismo bracket!")
            lines.append("")
            
            lines.append(f"**Diferencias reales:**")
            lines.append(f"- Edad: {z['diferencias']['edad']} anos")
            lines.append(f"- Peso: {z['diferencias']['peso']} kg")
            lines.append(f"- Estatura: {z['diferencias']['estatura']} cm")
            lines.append("")
            
            if z["failure_reasons"]:
                lines.append(f"**Primera condicion que fallo:** `{z['primera_falla']}`")
                lines.append(f"**Tipo de falla:** `{z['tipo_falla']}`")
                lines.append("")
            
            lines.append("**Competidores:**")
            for c in z["competidores"]:
                lines.append(f"- {c['nombre']} {c['apellido']}: edad={c['edad']} ({c['categoria_edad']}), sexo={c['sexo']}, cinta={c['cinta_block']}")
            lines.append("")
            
            lines.append("---")
            lines.append("")
        
        if len(zero_score) > 20:
            lines.append(f"_... y {len(zero_score) - 20} mas_")
            lines.append("")
        
        lines.append("### Posibles Causas Identificadas")
        lines.append("")
        lines.append("| Causa | Como detectarla en este reporte |")
        lines.append("|-------|----------------------------------|")
        lines.append("| Categoria de edad no se asigna correctamente | Verificar que todos competidores del mismo bracket tengan la misma categoria_edad. Si no, el filtro fallo. |")
        lines.append("| Filtro de categoria no se aplica en fase de relajacion | Brackets formados en nivel naranja/rojo donde se permitio mezcla de categorias. Revisar la logica de esos niveles. |")
        lines.append("| Limites de edad demasiado estrictos | Si las edades estan dentro de la misma categoria pero la diferencia es >1 ano. Aqui el error es de asignacion de categoria. |")
        lines.append("| Problemas con el matching global (Blossom) | Puede estar emparejando competidores de diferentes categorias porque no se separaron los subgrupos correctamente antes del matching. |")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # 7. RECOMENDACIONES
    lines.append("## 7. Recomendaciones")
    lines.append("")
    
    recommendations = []
    
    if metrics["edad"]["avg"] > 2:
        recommendations.append("- **Edad:** La diferencia promedio de edad es alta. Considera revisar el limite hard para categorias problematicas.")
    
    if metrics["peso"]["avg"] > 4:
        recommendations.append("- **Peso:** La diferencia promedio de peso es significativa. Verificar que el limite de 5kg funcione correctamente.")
    
    if metrics["estatura"]["avg"] > 10:
        recommendations.append("- **Estatura:** La diferencia promedio de estatura es alta. Considerar si el limite de 14cm es apropiado.")
    
    low_q_pct = len(low_quality) / metrics["total_brackets"] * 100 if metrics["total_brackets"] > 0 else 0
    if low_q_pct > 10:
        recommendations.append(f"- **Calidad:** {round(low_q_pct, 1)}% de brackets tienen score < 1.0. Revisar casos problematicos.")
    
    total_competitors = sum(t.get("total_competitors", 0) for t in tests)
    unpaired_pct = unpaired_analysis["total"] / total_competitors * 100 if total_competitors > 0 else 0
    if unpaired_pct > 20:
        recommendations.append(f"- **Emparejamiento:** {round(unpaired_pct, 1)}% de competidores no encuentran rival. Considerar relajamiento controlado.")
    
    if not recommendations:
        recommendations.append("- El algoritmo funciona dentro de parametros esperados.")
        recommendations.append("- No se detectan problemas criticos.")
    
    for rec in recommendations:
        lines.append(rec)
    
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"_Reporte generado automaticamente el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
    
    return "\n".join(lines)


def generate_llm_report(raw_report: dict, count: int = 25) -> dict:
    """Generar reporte LLM completo"""
    return {
        "timestamp": datetime.now().isoformat(),
        "total_tests": count,
        "summary": raw_report.get("summary", {}),
        "markdown": generate_llm_markdown(raw_report)
    }
