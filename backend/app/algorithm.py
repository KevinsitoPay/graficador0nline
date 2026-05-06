from __future__ import annotations

import logging
from itertools import combinations
from typing import Dict, List, Set, Tuple

from app.models import (
    BlockStats,
    Bracket,
    Competidor,
    GlobalStats,
    Results,
    ScoreBreakdown,
    Unpaired,
)

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTES
# =============================================================================

BLOCK_ORDER = [
    "Adultos Grupo 1",
    "Adultos Grupo 2",
    "Infantil Avanzados",
    "Infantil Azul",
    "Infantil Verde",
    "Infantil Amarilla",
    "Infantil Blanca",
    "Pre-Taekwondo",
]

BLOCK_PREFIXES = {
    "Adultos Grupo 1": "AD1",
    "Adultos Grupo 2": "AD2",
    "Infantil Avanzados": "IAV",
    "Infantil Azul": "AZ",
    "Infantil Verde": "VD",
    "Infantil Amarilla": "AM",
    "Infantil Blanca": "BC",
    "Pre-Taekwondo": "PT",
}

CINTAS_ADULTO_G1 = {"Marrón", "Roja", "Negra (Poom)", "Negra (Dan)"}

EDAD_CATEGORIAS = {
    "Preescolar": (3, 5),
    "Infantil_6_7": (6, 7),
    "Infantil_8_9": (8, 9),
    "Infantil_10_11": (10, 11),
    "Infantil_12_13": (12, 13),
    "Cadete": (14, 15),
    "Juvenil": (16, 17),
    "Adulto": (18, 29),
    "Sub_Master": (30, 45),
    "Master": (46, 200),
}

CINTA_NIVEL = {
    "Pre-Taekwondo": 0,
    "Blanca": 1,
    "Amarilla": 2,
    "Verde": 3,
    "Azul": 4,
    "Marrón": 5,
    "Roja": 6,
    "Negra (Poom)": 7,
    "Negra (Dan)": 8,
    "Desconocido": -1,
}

CINTA_A_BLOQUE_INFANTIL = {
    "Blanca": "Infantil Blanca",
    "Amarilla": "Infantil Amarilla",
    "Verde": "Infantil Verde",
    "Azul": "Infantil Azul",
    "Marrón": "Infantil Avanzados",
    "Roja": "Infantil Avanzados",
    "Negra (Poom)": "Infantil Avanzados",
    "Negra (Dan)": "Infantil Avanzados",
    "Desconocido": None,
}

MAX_PESO_ABS = 7.5
MAX_ESTATURA_ABS = 14.0
MAX_EDAD_INFANTIL_ABS = 2.5
MAX_EDAD_ADULTO_ABS = 6.0

RELAX_LEVELS = [
    {"nivel": 1, "peso": 5.0, "edad_inf": 1.0, "edad_adulto": 1.0, "estatura": 10,
     "score_min_4": 76, "score_min_3": 75, "score_min_2": 74},
    {"nivel": 2, "peso": 5.5, "edad_inf": 1.2, "edad_adulto": 1.2, "estatura": 11,
     "score_min_4": 74, "score_min_3": 73, "score_min_2": 72},
    {"nivel": 3, "peso": 6.0, "edad_inf": 1.5, "edad_adulto": 1.5, "estatura": 12,
     "score_min_4": 72, "score_min_3": 71, "score_min_2": 70},
    {"nivel": 4, "peso": 6.5, "edad_inf": 2.0, "edad_adulto": 2.0, "estatura": 12,
     "score_min_4": 70, "score_min_3": 69, "score_min_2": 68},
    {"nivel": 5, "peso": 7.0, "edad_inf": 2.2, "edad_adulto": 3.0, "estatura": 13,
     "score_min_4": 68, "score_min_3": 67, "score_min_2": 66},
    {"nivel": 6, "peso": 7.3, "edad_inf": 2.5, "edad_adulto": 4.0, "estatura": 14,
     "score_min_4": 66, "score_min_3": 65, "score_min_2": 64},
    {"nivel": 7, "peso": 7.5, "edad_inf": 2.5, "edad_adulto": 6.0, "estatura": 14,
     "score_min_4": 64, "score_min_3": 63, "score_min_2": 62},
]

# =============================================================================
# HELPERS
# =============================================================================

def get_categoria_edad(edad: int) -> str:
    for cat, (lo, hi) in EDAD_CATEGORIAS.items():
        if lo <= edad <= hi:
            return cat
    return "Adulto"

def es_bloque_adulto(bloque: str) -> bool:
    return bloque in ("Adultos Grupo 1", "Adultos Grupo 2")

def asignar_bloque_correcto(c: Competidor) -> None:
    if c.edad <= 5:
        c.bloque = "Pre-Taekwondo"
    elif c.edad >= 14:
        c.bloque = "Adultos Grupo 1" if c.cinta_block in CINTAS_ADULTO_G1 else "Adultos Grupo 2"
    else:
        bloque_correcto = CINTA_A_BLOQUE_INFANTIL.get(c.cinta_block)
        if bloque_correcto:
            c.bloque = bloque_correcto

def mismo_sexo(c1: Competidor, c2: Competidor) -> bool:
    return c1.sexo == c2.sexo

def misma_categoria_edad(c1: Competidor, c2: Competidor) -> bool:
    return c1.categoria_edad == c2.categoria_edad

def modalidad_par_ok(c1: Competidor, c2: Competidor) -> bool:
    return c1.modalidad == c2.modalidad

def modalidad_grupo_ok(competidores: List[Competidor]) -> bool:
    if len(competidores) < 2:
        return True
    return len({c.modalidad for c in competidores}) == 1

def cintas_permitidas(c1: Competidor, c2: Competidor) -> bool:
    if c1.cinta_block == c2.cinta_block:
        return True

    if c1.cinta_block == "Desconocido" or c2.cinta_block == "Desconocido":
        return False

    ambos_adulto_g1 = c1.bloque == "Adultos Grupo 1" and c2.bloque == "Adultos Grupo 1"
    if ambos_adulto_g1:
        n1 = CINTA_NIVEL.get(c1.cinta_block, 0)
        n2 = CINTA_NIVEL.get(c2.cinta_block, 0)
        return abs(n1 - n2) == 1

    return False

def _edad_limite_para(c1: Competidor, c2: Competidor, limits: Dict) -> float:
    return limits["edad_adulto"] if es_bloque_adulto(c1.bloque) and es_bloque_adulto(c2.bloque) else limits["edad_inf"]

def limites_fisicos_ok(c1: Competidor, c2: Competidor, limits: Dict) -> Tuple[bool, str]:
    dp = abs(c1.peso_kg - c2.peso_kg)
    de = abs(c1.edad - c2.edad)
    estatura_valida = c1.estatura_cm > 0 and c2.estatura_cm > 0
    ds = abs(c1.estatura_cm - c2.estatura_cm) if estatura_valida else 0.0

    peso_base = min(c1.peso_kg, c2.peso_kg)
    max_peso_abs_efectivo = max(MAX_PESO_ABS, peso_base * 0.12)

    if dp > max_peso_abs_efectivo:
        return False, "peso_abs"
    if estatura_valida and ds > MAX_ESTATURA_ABS:
        return False, "est_abs"

    max_edad_abs = MAX_EDAD_ADULTO_ABS if es_bloque_adulto(c1.bloque) else MAX_EDAD_INFANTIL_ABS
    if de > max_edad_abs:
        return False, "edad_abs"

    if dp > limits["peso"]:
        return False, "peso_nivel"
    if estatura_valida and ds > limits["estatura"]:
        return False, "est_nivel"
    if de > _edad_limite_para(c1, c2, limits):
        return False, "edad_nivel"

    return True, ""

def puede_emparejarse(c1: Competidor, c2: Competidor, limits: Dict, nivel: int = 1) -> Tuple[bool, str]:
    if not mismo_sexo(c1, c2):
        return False, "sexo"
    if not misma_categoria_edad(c1, c2):
        return False, "categoria"
    if not cintas_permitidas(c1, c2):
        return False, "cinta"
    if not modalidad_par_ok(c1, c2):
        return False, "modalidad"
    return limites_fisicos_ok(c1, c2, limits)

def puede_grupo(competidores: List[Competidor], limits: Dict, nivel: int) -> Tuple[bool, str]:
    if not modalidad_grupo_ok(competidores):
        return False, "modalidad_grupo"
    for i in range(len(competidores)):
        for j in range(i + 1, len(competidores)):
            ok, motivo = puede_emparejarse(competidores[i], competidores[j], limits, nivel)
            if not ok:
                return False, motivo
    return True, ""

# =============================================================================
# SCORE
# =============================================================================

def score(c1: Competidor, c2: Competidor, limits: Dict, nivel: int) -> float:
    ok, _ = puede_emparejarse(c1, c2, limits, nivel)
    if not ok:
        return 0.0

    dp = abs(c1.peso_kg - c2.peso_kg)
    de = abs(c1.edad - c2.edad)
    estatura_valida = c1.estatura_cm > 0 and c2.estatura_cm > 0
    ds = abs(c1.estatura_cm - c2.estatura_cm) if estatura_valida else 0.0

    peso_max = max(limits["peso"], 0.1)
    edad_max = max(_edad_limite_para(c1, c2, limits), 0.1)
    est_max = max(limits["estatura"], 0.1)

    pen_peso = 40 * (dp / peso_max) ** 1.45
    pen_edad = 22 * (de / edad_max) ** 1.35
    pen_est = 10 * (ds / est_max) ** 1.25 if estatura_valida else 0
    pen_doyang = 5 if c1.doyang == c2.doyang else 0
    pen_cinta = 3 * abs(CINTA_NIVEL.get(c1.cinta_block, 0) - CINTA_NIVEL.get(c2.cinta_block, 0))

    total = 100 - (pen_peso + pen_edad + pen_est + pen_doyang + pen_cinta)
    return max(0.0, min(100.0, total))

def _pair_scores_for_group(competidores: List[Competidor], limits: Dict, nivel: int) -> List[float]:
    return [score(competidores[i], competidores[j], limits, nivel)
            for i in range(len(competidores))
            for j in range(i + 1, len(competidores))]

def calcular_bracket_score(competidores: List[Competidor], limits: Dict, nivel: int) -> Tuple[float, Dict, List[str]]:
    if len(competidores) < 2:
        bd = {
            "modalidad_ok": True,
            "edad_diff": 0,
            "edad_score": 0.0,
            "peso_diff": 0.0,
            "peso_score": 0.0,
            "estatura_diff": 0,
            "estatura_score": 0.0,
            "doyang_penalty": 0.0,
            "cinta_penalty": 0.0,
            "total": 0.0,
        }
        return 0.0, bd, []

    ok, motivo = puede_grupo(competidores, limits, nivel)
    if not ok:
        bd = {
            "modalidad_ok": False,
            "edad_diff": 0,
            "edad_score": 0.0,
            "peso_diff": 0.0,
            "peso_score": 0.0,
            "estatura_diff": 0,
            "estatura_score": 0.0,
            "doyang_penalty": 0.0,
            "cinta_penalty": 0.0,
            "total": 0.0,
        }
        return 0.0, bd, [motivo]

    pair_scores = _pair_scores_for_group(competidores, limits, nivel)
    avg_score = sum(pair_scores) / len(pair_scores)
    min_score = min(pair_scores)
    final_score = 0.70 * avg_score + 0.30 * min_score

    edad_diffs, peso_diffs, est_diffs = [], [], []
    for i in range(len(competidores)):
        for j in range(i + 1, len(competidores)):
            edad_diffs.append(abs(competidores[i].edad - competidores[j].edad))
            peso_diffs.append(abs(competidores[i].peso_kg - competidores[j].peso_kg))
            est_diffs.append(abs(competidores[i].estatura_cm - competidores[j].estatura_cm))

    bd = {
        "modalidad_ok": True,
        "edad_diff": int(sum(edad_diffs) / len(edad_diffs)) if edad_diffs else 0,
        "edad_score": round(max(0.0, 100 - (sum(edad_diffs) / max(len(edad_diffs), 1)) * 14), 2),
        "peso_diff": round(sum(peso_diffs) / len(peso_diffs), 2) if peso_diffs else 0.0,
        "peso_score": round(max(0.0, 100 - (sum(peso_diffs) / max(len(peso_diffs), 1)) * 6), 2),
        "estatura_diff": int(sum(est_diffs) / len(est_diffs)) if est_diffs else 0,
        "estatura_score": round(max(0.0, 100 - (sum(est_diffs) / max(len(est_diffs), 1)) * 3.5), 2),
        "doyang_penalty": 0.0,
        "cinta_penalty": 0.0,
        "total": round(final_score, 2),
    }

    return final_score, bd, []

# =============================================================================
# CANDIDATOS Y REACOMODO
# =============================================================================

def _score_min(size: int, config: Dict) -> float:
    return config["score_min_4"] if size == 4 else config["score_min_3"] if size == 3 else config["score_min_2"]

def _min_pair_threshold(size: int, nivel: int) -> float:
    if size == 4:
        return 58 if nivel <= 3 else 54 if nivel <= 5 else 50
    if size == 3:
        return 60 if nivel <= 3 else 56 if nivel <= 5 else 52
    return 68 if nivel <= 5 else 62

def _candidate_color(score_val: float) -> str:
    if score_val >= 85:
        return "verde"
    if score_val >= 75:
        return "amarillo"
    if score_val >= 65:
        return "naranja"
    return "rojo"

def _build_bracket(grupo: List[Competidor], nivel: int, score_val: float, bd: Dict, origen: str) -> Bracket:
    return Bracket(
        id=0,
        numero=0,
        area=0,
        competidores=grupo,
        tipo=f"nivel{nivel}",
        score=round(score_val, 2),
        score_breakdown=ScoreBreakdown(**bd),
        nivel_aprobacion=_candidate_color(score_val),
        requiere_aprobacion=score_val < 85,
        aprobador_requerido="colaborador" if score_val < 85 else None,
        ronda_origen=origen,
        failure_reasons=[],
    )

def _generate_candidates(competitors: List[Competidor], size: int, limits: Dict, nivel: int, config: Dict) -> List[Tuple[float, List[Competidor], Dict]]:
    if len(competitors) < size:
        return []

    comps = sorted(competitors, key=lambda c: (c.peso_kg, c.edad))
    threshold = _score_min(size, config)
    min_pair_req = _min_pair_threshold(size, nivel)
    window = 12 if size == 4 else 10 if size == 3 else 8

    candidates = []
    seen = set()

    for i in range(len(comps)):
        local = comps[i:min(i + window, len(comps))]
        if len(local) < size:
            continue

        for subset in combinations(local, size):
            ids = tuple(sorted(c.id for c in subset))
            if ids in seen:
                continue
            seen.add(ids)

            grupo = list(subset)
            ok, _ = puede_grupo(grupo, limits, nivel)
            if not ok:
                continue

            pair_scores = _pair_scores_for_group(grupo, limits, nivel)
            if min(pair_scores) < min_pair_req:
                continue

            s, bd, _ = calcular_bracket_score(grupo, limits, nivel)
            if s < threshold:
                continue

            bonus = 10 if size == 4 else 5 if size == 3 else -2
            candidates.append((s + bonus, grupo, bd))

    candidates.sort(key=lambda x: (len(x[1]), x[0]), reverse=True)
    return candidates

def _select_disjoint(candidates: List[Tuple[float, List[Competidor], Dict]]) -> Tuple[List[Tuple[float, List[Competidor], Dict]], Set[str]]:
    selected = []
    used = set()

    for priority, grupo, bd in candidates:
        ids = {c.id for c in grupo}
        if ids & used:
            continue
        selected.append((priority, grupo, bd))
        used.update(ids)

    return selected, used

def _reacomodo_estructural(brackets: List[Bracket], restantes: List[Competidor], config: Dict, nivel: int) -> Tuple[List[Bracket], List[Competidor]]:
    if not brackets:
        return brackets, restantes

    limits = {
        "peso": config["peso"],
        "edad_inf": config["edad_inf"],
        "edad_adulto": config["edad_adulto"],
        "estatura": config["estatura"],
    }

    restantes = list(restantes)

    # 3+1 -> 4
    changed = True
    while changed and restantes:
        changed = False
        best = None
        for bi, b in enumerate(brackets):
            if len(b.competidores) != 3:
                continue
            for ri, comp in enumerate(restantes):
                nuevo = b.competidores + [comp]
                ok, _ = puede_grupo(nuevo, limits, nivel)
                if not ok:
                    continue
                s, bd, _ = calcular_bracket_score(nuevo, limits, nivel)
                if s < max(config["score_min_4"] - 4, 60):
                    continue
                if best is None or s > best[0]:
                    best = (s, bi, ri, nuevo, bd)
        if best:
            s, bi, ri, nuevo, bd = best
            old = brackets[bi]
            nb = _build_bracket(nuevo, nivel, s, bd, f"{old.ronda_origen}_3a4")
            nb.id, nb.numero, nb.area = old.id, old.numero, old.area
            brackets[bi] = nb
            restantes.pop(ri)
            changed = True

    # 2+1 -> 3
    changed = True
    while changed and restantes:
        changed = False
        best = None
        for bi, b in enumerate(brackets):
            if len(b.competidores) != 2:
                continue
            for ri, comp in enumerate(restantes):
                nuevo = b.competidores + [comp]
                ok, _ = puede_grupo(nuevo, limits, nivel)
                if not ok:
                    continue
                s, bd, _ = calcular_bracket_score(nuevo, limits, nivel)
                if s < max(config["score_min_3"] - 4, 58):
                    continue
                if best is None or s > best[0]:
                    best = (s, bi, ri, nuevo, bd)
        if best:
            s, bi, ri, nuevo, bd = best
            old = brackets[bi]
            nb = _build_bracket(nuevo, nivel, s, bd, f"{old.ronda_origen}_2a3")
            nb.id, nb.numero, nb.area = old.id, old.numero, old.area
            brackets[bi] = nb
            restantes.pop(ri)
            changed = True

    # 2+2 -> 4
    pair_idx = [i for i, b in enumerate(brackets) if len(b.competidores) == 2]
    used_positions = set()
    eliminar = set()
    nuevos = []

    for i in range(len(pair_idx)):
        if i in used_positions:
            continue
        bi = pair_idx[i]
        b1 = brackets[bi]

        best = None
        best_j = None
        for j in range(i + 1, len(pair_idx)):
            if j in used_positions:
                continue
            bj = pair_idx[j]
            b2 = brackets[bj]

            nuevo = b1.competidores + b2.competidores
            ok, _ = puede_grupo(nuevo, limits, nivel)
            if not ok:
                continue
            s, bd, _ = calcular_bracket_score(nuevo, limits, nivel)
            if s < max(config["score_min_4"] - 5, 58):
                continue
            if best is None or s > best[0]:
                best = (s, bd, nuevo)
                best_j = j

        if best:
            s, bd, nuevo = best
            used_positions.add(i)
            used_positions.add(best_j)
            eliminar.add(bi)
            eliminar.add(pair_idx[best_j])
            nuevos.append(_build_bracket(nuevo, nivel, s, bd, f"fusion_2_2_{nivel}"))

    if eliminar:
        brackets = [b for idx, b in enumerate(brackets) if idx not in eliminar]
        brackets.extend(nuevos)

    return brackets, restantes

# =============================================================================
# RESOLUCIÓN POR POOL
# =============================================================================

def _resolver_pool(grupo: List[Competidor]) -> Tuple[List[Bracket], List[Competidor]]:
    restantes = list(grupo)
    brackets: List[Bracket] = []

    for nivel in range(1, 8):
        if len(restantes) < 2:
            break

        config = RELAX_LEVELS[nivel - 1]
        limits = {
            "peso": config["peso"],
            "edad_inf": config["edad_inf"],
            "edad_adulto": config["edad_adulto"],
            "estatura": config["estatura"],
        }

        # 1) CUARTETOS
        cand4 = _generate_candidates(restantes, 4, limits, nivel, config)
        sel4, used4 = _select_disjoint(cand4)
        for _, g, bd in sel4:
            brackets.append(_build_bracket(g, nivel, bd["total"], bd, f"cuarteto_{nivel}"))
        restantes = [c for c in restantes if c.id not in used4]

        # 2) TRÍOS
        if len(restantes) >= 3:
            cand3 = _generate_candidates(restantes, 3, limits, nivel, config)
            sel3, used3 = _select_disjoint(cand3)
            for _, g, bd in sel3:
                brackets.append(_build_bracket(g, nivel, bd["total"], bd, f"trio_{nivel}"))
            restantes = [c for c in restantes if c.id not in used3]

        # 3) REACOMODO ANTES DE PARES
        brackets, restantes = _reacomodo_estructural(brackets, restantes, config, nivel)

        # 4) PARES AL FINAL
        if nivel >= 3 and len(restantes) >= 2:
            cand2 = _generate_candidates(restantes, 2, limits, nivel, config)
            sel2, used2 = _select_disjoint(cand2)
            for _, g, bd in sel2:
                brackets.append(_build_bracket(g, nivel, bd["total"], bd, f"par_{nivel}"))
            restantes = [c for c in restantes if c.id not in used2]

        # 5) REACOMODO FINAL DE LA RONDA
        brackets, restantes = _reacomodo_estructural(brackets, restantes, config, nivel)

    return brackets, restantes

# =============================================================================
# MOTOR PRINCIPAL
# =============================================================================

def generar_brackets(competitors: List[Competidor]) -> Results:
    if not competitors:
        return _resultado_vacio()

    for c in competitors:
        c.categoria_edad = get_categoria_edad(c.edad)
        asignar_bloque_correcto(c)

    competitors.sort(key=lambda c: (c.bloque, c.sexo, c.cinta_block, c.categoria_edad, c.edad, c.peso_kg))

    def _clave_grupo(c: Competidor) -> tuple:
        bloque = c.bloque
        cinta = c.cinta_block
        sexo = c.sexo

        if bloque == "Adultos Grupo 1":
            return (bloque, sexo)
        if bloque == "Infantil Avanzados":
            return (bloque, c.categoria_edad, sexo)
        return (bloque, c.categoria_edad, sexo, cinta)

    grupos_iniciales: Dict[tuple, List[Competidor]] = {}
    for c in competitors:
        grupos_iniciales.setdefault(_clave_grupo(c), []).append(c)

    todos_brackets: List[Bracket] = []
    no_emparejados: List[Competidor] = []

    for _, grupo in grupos_iniciales.items():
        b, r = _resolver_pool(grupo)
        todos_brackets.extend(b)
        no_emparejados.extend(r)

    asignar_numeracion(todos_brackets, competitors)

    sin_rival_final = [
        Unpaired(competidor=c, razon="Sin rival compatible dentro de límites justos")
        for c in no_emparejados
    ]

    return _construir_results(competitors, todos_brackets, sin_rival_final)

def asignar_numeracion(brackets: List[Bracket], todos_competidores: List[Competidor]) -> None:
    por_bloque = {}
    for c in todos_competidores:
        por_bloque.setdefault(c.bloque, []).append(c)

    for bloque, comps in por_bloque.items():
        prefijo = BLOCK_PREFIXES.get(bloque, "XX")
        for idx, c in enumerate(sorted(comps, key=lambda x: (x.edad, x.peso_kg)), 1):
            c.numero_competidor = f"{prefijo} {idx}"

    graf_num = 1
    for bloque in BLOCK_ORDER:
        brackets_bloque = [b for b in brackets if b.competidores and b.competidores[0].bloque == bloque]
        for b in brackets_bloque:
            b.numero = graf_num
            b.area = ((graf_num - 1) % 12) + 1
            graf_num += 1

def _construir_results(competitors: List[Competidor], brackets: List[Bracket], unpaired: List[Unpaired]) -> Results:
    total_comp = len(competitors)
    total_brack = len(brackets)
    brackets_2 = sum(1 for b in brackets if len(b.competidores) == 2)
    brackets_3 = sum(1 for b in brackets if len(b.competidores) == 3)
    brackets_4 = sum(1 for b in brackets if len(b.competidores) == 4)

    excellent = sum(1 for b in brackets if b.score >= 80)
    low_quality = sum(1 for b in brackets if b.score < 65)
    all_scores = [b.score for b in brackets]
    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0.0

    emp_count = total_comp - len(unpaired)
    emp_pct = (emp_count / total_comp * 100) if total_comp > 0 else 0.0
    avg_size = sum(len(b.competidores) for b in brackets) / total_brack if total_brack > 0 else 0.0

    global_stats = GlobalStats(
        total_competidores=total_comp,
        total_brackets=total_brack,
        avg_bracket_size=round(avg_size, 2),
        brackets_2=brackets_2,
        brackets_3=brackets_3,
        brackets_4=brackets_4,
        sin_rival_total=len(unpaired),
        excellent_brackets=excellent,
        low_quality_brackets=low_quality,
        brackets_verde=sum(1 for b in brackets if b.nivel_aprobacion == "verde"),
        brackets_amarillo=sum(1 for b in brackets if b.nivel_aprobacion == "amarillo"),
        brackets_naranja=sum(1 for b in brackets if b.nivel_aprobacion == "naranja"),
        brackets_rojo=sum(1 for b in brackets if b.nivel_aprobacion == "rojo"),
        avg_score=round(avg_score, 2),
        emparejamiento_pct=round(emp_pct, 2),
    )

    block_stats = []
    for bloque in BLOCK_ORDER:
        bloque_comps = [c for c in competitors if c.bloque == bloque]
        bloque_brackets = [b for b in brackets if b.competidores and b.competidores[0].bloque == bloque]
        bloque_unpaired = [u for u in unpaired if u.competidor.bloque == bloque]

        if not bloque_comps:
            continue

        block_stats.append(BlockStats(
            bloque=bloque,
            competidores=len(bloque_comps),
            brackets=len(bloque_brackets),
            avg_size=round(sum(len(b.competidores) for b in bloque_brackets) / len(bloque_brackets), 2) if bloque_brackets else 0.0,
            sin_rival=len(bloque_unpaired),
            relaxed_count=sum(1 for b in bloque_brackets if b.ronda_origen and "nivel" in b.ronda_origen and not b.ronda_origen.endswith("_1")),
        ))

    return Results(
        global_stats=global_stats,
        block_stats=block_stats,
        brackets=brackets,
        unpaired=unpaired,
    )

def _resultado_vacio() -> Results:
    return Results(
        global_stats=GlobalStats(
            total_competidores=0,
            total_brackets=0,
            avg_bracket_size=0,
            brackets_2=0,
            brackets_3=0,
            brackets_4=0,
            sin_rival_total=0,
            excellent_brackets=0,
            low_quality_brackets=0,
            avg_score=0.0,
            emparejamiento_pct=0.0,
        ),
        block_stats=[],
        brackets=[],
        unpaired=[],
    )

def generate_results(competitors: List[Competidor]) -> Results:
    return generar_brackets(competitors)


