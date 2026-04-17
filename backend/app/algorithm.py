from typing import List, Dict, Tuple, Optional, Set
from app.models import Competidor, Bracket, BlockStats, GlobalStats, Unpaired, Results, ScoreBreakdown
import logging
from functools import lru_cache

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BLOCK_ORDER = [
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

BLOCK_PREFIXES = {
    "Adultos Grupo 1": "AD",
    "Adultos Grupo 2": "AD",
    "Infantil Azul": "AZ",
    "Infantil Verde": "VD",
    "Infantil Amarilla": "AM",
    "Infantil Blanca": "BC",
    "Pre-Taekwondo": "PT",
    "Infantil Marrón": "MR",
    "Infantil Roja": "RJ",
    "Infantil Negra": "PM",
}

EDAD_CATEGORIES: Dict[str, Tuple[int, int]] = {
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

CINTA_LEVEL: Dict[str, int] = {
    "Pre-Taekwondo": 0,
    "Blanca": 1,
    "Amarilla": 2,
    "Verde": 3,
    "Azul": 4,
    "Marrón": 5,
    "Roja": 6,
    "Negra (Poom)": 7,
    "Negra (Dan)": 8,
}

CINTA_ADYACENTE: Dict[str, List[str]] = {
    "Pre-Taekwondo": [],
    "Blanca": ["Amarilla"],
    "Amarilla": ["Blanca", "Verde"],
    "Verde": ["Amarilla", "Azul"],
    "Azul": ["Verde", "Marrón"],
    "Marrón": ["Azul", "Roja"],
    "Roja": ["Marrón", "Negra (Poom)", "Negra (Dan)"],
    "Negra (Poom)": ["Roja"],
    "Negra (Dan)": ["Roja"],
}

# Niveles de relajación ajustados a límites máximos: 6.5 kg y 14 cm
RELAXATION_LEVELS: List[Dict] = [
    {"nivel": 1, "peso": 5.0, "edad": 1.0, "estatura": 10, "mezcla_cintas": False, "score_min": 80, "color": "verde"},
    {"nivel": 2, "peso": 5.5, "edad": 1.1, "estatura": 11, "mezcla_cintas": False, "score_min": 75, "color": "verde"},
    {"nivel": 3, "peso": 6.0, "edad": 1.2, "estatura": 12, "mezcla_cintas": False, "score_min": 70, "color": "amarillo"},
    {"nivel": 4, "peso": 6.0, "edad": 2.0, "estatura": 12, "mezcla_cintas": True, "score_min": 70, "color": "naranja"},
    {"nivel": 5, "peso": 6.5, "edad": 2.5, "estatura": 14, "mezcla_cintas": True, "score_min": 60, "color": "rojo"},
]


def get_categoria_edad(edad: int) -> str:
    for categoria, (min_edad, max_edad) in EDAD_CATEGORIES.items():
        if min_edad <= edad <= max_edad:
            return categoria
    return "Adulto"


def get_cinta_normalizada(cinta: str) -> str:
    if cinta in ["Negra (Poom)", "Negra (Dan)"]:
        return cinta
    return cinta


def get_cintas_adyacentes(cinta: str) -> List[str]:
    cinta = get_cinta_normalizada(cinta)
    return CINTA_ADYACENTE.get(cinta, [])


def asignar_bloque_correcto(competidor: Competidor) -> None:
    if competidor.edad >= 18:
        cinta_norm = get_cinta_normalizada(competidor.cinta_block)
        if cinta_norm in ["Marrón", "Roja", "Negra (Dan)"]:
            competidor.bloque = "Adultos Grupo 1"
        else:
            competidor.bloque = "Adultos Grupo 2"
    elif competidor.edad <= 5:
        competidor.bloque = "Pre-Taekwondo"


def bloques_adultos_compatibles(c1: Competidor, c2: Competidor) -> bool:
    bloques_adultos = {"Adultos Grupo 1", "Adultos Grupo 2"}
    if c1.bloque in bloques_adultos and c2.bloque in bloques_adultos:
        return c1.bloque == c2.bloque
    return True


def cintas_permitidas(c1: Competidor, c2: Competidor, nivel: int) -> bool:
    if nivel <= 3:
        return c1.cinta_block == c2.cinta_block
    cinta1 = get_cinta_normalizada(c1.cinta_block)
    cinta2 = get_cinta_normalizada(c2.cinta_block)
    if cinta1 == cinta2:
        return True
    if nivel == 4:
        ady1 = get_cintas_adyacentes(cinta1)
        return cinta2 in ady1
    nivel1 = CINTA_LEVEL.get(cinta1, 0)
    nivel2 = CINTA_LEVEL.get(cinta2, 0)
    return abs(nivel1 - nivel2) <= 2


_score_cache: Dict[Tuple[str, str, float, float, float], float] = {}

def _cached_score(c1: Competidor, c2: Competidor, limits: Dict) -> Tuple[float, List[str]]:
    key = (c1.id, c2.id, limits["peso"], limits["edad"], limits["estatura"])
    if key in _score_cache:
        return _score_cache[key], []
    s, razones = score(c1, c2, limits)
    _score_cache[key] = s
    return s, razones


def score(c1: Competidor, c2: Competidor, limits: Dict) -> Tuple[float, List[str]]:
    razones = []
    
    # Validación estricta de sexo
    if c1.sexo != c2.sexo:
        msg = f"❌ INTENTO DE EMPAREJAR SEXOS DIFERENTES: {c1.nombre} ({c1.sexo}) vs {c2.nombre} ({c2.sexo})"
        logger.error(msg)
        raise ValueError(msg)
    
    if not bloques_adultos_compatibles(c1, c2):
        razones.append("bloques_adultos_incompatibles")
        return 0.0, razones
    
    if c1.categoria_edad != c2.categoria_edad:
        razones.append(f"categoria_edad_diferente: {c1.categoria_edad} vs {c2.categoria_edad}")
        return 0.0, razones
    
    diff_peso = abs(c1.peso_kg - c2.peso_kg)
    diff_edad = abs(c1.edad - c2.edad)
    diff_est = abs(c1.estatura_cm - c2.estatura_cm)
    
    if diff_peso > limits["peso"]:
        razones.append(f"peso_limite_excedido: {diff_peso:.2f}kg > {limits['peso']}kg")
        return 0.0, razones
    if diff_edad > limits["edad"]:
        razones.append(f"edad_limite_excedido: {diff_edad} > {limits['edad']}")
        return 0.0, razones
    if diff_est > limits["estatura"]:
        razones.append(f"estatura_limite_excedido: {diff_est}cm > {limits['estatura']}cm")
        return 0.0, razones
    
    peso_max = limits["peso"]
    edad_max = limits["edad"]
    est_max = limits["estatura"]
    
    penalidad_peso = 40 * (diff_peso / peso_max) ** 1.8 if peso_max > 0 else 0
    penalidad_edad = 30 * (diff_edad / edad_max) ** 1.8 if edad_max > 0 else 0
    penalidad_estatura = 20 * (diff_est / est_max) ** 1.8 if est_max > 0 else 0
    penalidad_doyang = 10 if c1.doyang == c2.doyang else 0
    
    nivel_c1 = CINTA_LEVEL.get(c1.cinta_block, 0)
    nivel_c2 = CINTA_LEVEL.get(c2.cinta_block, 0)
    penalidad_cinta = 5 * abs(nivel_c1 - nivel_c2)
    
    total = 100 - (penalidad_peso + penalidad_edad + penalidad_estatura + penalidad_doyang + penalidad_cinta)
    if total <= 0:
        razones.append("score_negativo_por_penalizaciones")
        return 0.0, razones
    
    return max(0.0, min(100.0, total)), razones


def puede_emparejarse(c1: Competidor, c2: Competidor, limits: Dict) -> Tuple[bool, str]:
    if c1.sexo != c2.sexo:
        return False, "sexo_diferente"
    if not bloques_adultos_compatibles(c1, c2):
        return False, "bloques_adultos_incompatibles"
    if c1.categoria_edad != c2.categoria_edad:
        return False, f"categorias_edad_diferentes: {c1.categoria_edad} != {c2.categoria_edad}"
    diff_peso = abs(c1.peso_kg - c2.peso_kg)
    diff_edad = abs(c1.edad - c2.edad)
    diff_est = abs(c1.estatura_cm - c2.estatura_cm)
    if diff_peso > limits["peso"]:
        return False, f"peso_diff={diff_peso:.2f}kg > {limits['peso']}kg"
    if diff_edad > limits["edad"]:
        return False, f"edad_diff={diff_edad} > {limits['edad']}"
    if diff_est > limits["estatura"]:
        return False, f"est_diff={diff_est}cm > {limits['estatura']}cm"
    return True, ""


def misma_modalidad_valida(modalidades: List[str]) -> bool:
    if len(modalidades) < 2:
        return True
    count_doble = modalidades.count("Doble")
    return count_doble != 1


def bono_modalidad_mixta(competidores: List[Competidor]) -> float:
    if len(competidores) != 4:
        return 0.0
    dobles = sum(1 for c in competidores if c.modalidad == "Doble")
    if dobles == 2:
        return 5.0
    return 0.0


def calcular_score_breakdown(c1: Competidor, c2: Competidor, limits: Dict) -> Dict:
    puede, razon = puede_emparejarse(c1, c2, limits)
    diff_peso = abs(c1.peso_kg - c2.peso_kg)
    diff_est = abs(c1.estatura_cm - c2.estatura_cm)
    diff_edad = abs(c1.edad - c2.edad)
    modalidad_ok = misma_modalidad_valida([c1.modalidad, c2.modalidad])
    
    if not puede:
        return {
            "modalidad_ok": modalidad_ok,
            "edad_diff": int(diff_edad),
            "edad_score": 0,
            "peso_diff": round(diff_peso, 2),
            "peso_score": 0,
            "estatura_diff": int(diff_est),
            "estatura_score": 0,
            "doyang_penalty": 0,
            "cinta_penalty": 0,
            "total": 0,
            "razon": razon
        }
    
    peso_max = limits["peso"]
    edad_max = limits["edad"]
    est_max = limits["estatura"]
    penalidad_peso = 40 * (diff_peso / peso_max) ** 1.8 if peso_max > 0 else 0
    penalidad_edad = 30 * (diff_edad / edad_max) ** 1.8 if edad_max > 0 else 0
    penalidad_estatura = 20 * (diff_est / est_max) ** 1.8 if est_max > 0 else 0
    penalidad_doyang = 10 if c1.doyang == c2.doyang else 0
    nivel_c1 = CINTA_LEVEL.get(c1.cinta_block, 0)
    nivel_c2 = CINTA_LEVEL.get(c2.cinta_block, 0)
    penalidad_cinta = 5 * abs(nivel_c1 - nivel_c2)
    total = 100 - (penalidad_peso + penalidad_edad + penalidad_estatura + penalidad_doyang + penalidad_cinta)
    total = max(0, min(100, total))
    
    return {
        "modalidad_ok": modalidad_ok,
        "edad_diff": int(diff_edad),
        "edad_score": round(100 - penalidad_edad, 2),
        "peso_diff": round(diff_peso, 2),
        "peso_score": round(100 - penalidad_peso, 2),
        "estatura_diff": int(diff_est),
        "estatura_score": round(100 - penalidad_estatura, 2),
        "doyang_penalty": penalidad_doyang,
        "cinta_penalty": penalidad_cinta,
        "total": round(total, 2)
    }


def _validar_sexo_bracket(competidores: List[Competidor]) -> bool:
    if not competidores:
        return True
    sexo = competidores[0].sexo
    return all(c.sexo == sexo for c in competidores)


def _crear_bracket(
    competidores: List[Competidor],
    tipo: str,
    score_val: float,
    breakdown: Dict,
    nivel_aprobacion: str,
    requiere_aprobacion: bool,
    aprobador: Optional[str],
    ronda_origen: str,
    failure_reasons: Optional[List[str]] = None
) -> Bracket:
    if not _validar_sexo_bracket(competidores):
        sexos = set(c.sexo for c in competidores)
        logger.error(f"🚨 BRACKET MIXTO DETECTADO en {ronda_origen}: {sexos}")
        raise ValueError(f"Bracket con sexos mixtos en {ronda_origen}")
    return Bracket(
        id=0,
        numero=0,
        area=0,
        competidores=competidores,
        tipo=tipo,
        score=round(score_val, 2),
        score_breakdown=ScoreBreakdown(**breakdown),
        nivel_aprobacion=nivel_aprobacion,
        requiere_aprobacion=requiere_aprobacion,
        aprobador_requerido=aprobador,
        ronda_origen=ronda_origen,
        failure_reasons=failure_reasons or []
    )


def _calcular_bracket_score(competidores: List[Competidor], limits: Dict) -> Tuple[float, Dict, List[str]]:
    if len(competidores) < 2:
        return 0.0, {"modalidad_ok": True, "edad_diff": 0, "edad_score": 0, "peso_diff": 0, "peso_score": 0, "estatura_diff": 0, "estatura_score": 0, "doyang_penalty": 0, "cinta_penalty": 0, "total": 0}, []
    
    modalidades = [c.modalidad for c in competidores]
    modalidad_ok = misma_modalidad_valida(modalidades)
    all_reasons = []
    
    if len(competidores) == 2:
        s, razones = score(competidores[0], competidores[1], limits)
        bd = calcular_score_breakdown(competidores[0], competidores[1], limits)
        bd["modalidad_ok"] = modalidad_ok
        return s, bd, razones
    
    scores = []
    breakdowns = []
    for i in range(len(competidores)):
        for j in range(i + 1, len(competidores)):
            s, razones = score(competidores[i], competidores[j], limits)
            scores.append(s)
            if razones:
                all_reasons.extend(razones)
            bd = calcular_score_breakdown(competidores[i], competidores[j], limits)
            breakdowns.append(bd)
    
    avg_score = sum(scores) / len(scores) if scores else 0.0
    bono = bono_modalidad_mixta(competidores)
    avg_score = min(100.0, avg_score + bono)
    
    breakdown = {
        "modalidad_ok": modalidad_ok and all(b["modalidad_ok"] for b in breakdowns),
        "edad_diff": int(sum(b["edad_diff"] for b in breakdowns) / len(breakdowns)) if breakdowns else 0,
        "edad_score": round(sum(b["edad_score"] for b in breakdowns) / len(breakdowns), 2) if breakdowns else 0,
        "peso_diff": round(sum(b["peso_diff"] for b in breakdowns) / len(breakdowns), 2) if breakdowns else 0,
        "peso_score": round(sum(b["peso_score"] for b in breakdowns) / len(breakdowns), 2) if breakdowns else 0,
        "estatura_diff": int(sum(b["estatura_diff"] for b in breakdowns) / len(breakdowns)) if breakdowns else 0,
        "estatura_score": round(sum(b["estatura_score"] for b in breakdowns) / len(breakdowns), 2) if breakdowns else 0,
        "doyang_penalty": round(sum(b["doyang_penalty"] for b in breakdowns) / len(breakdowns), 2) if breakdowns else 0,
        "cinta_penalty": round(sum(b["cinta_penalty"] for b in breakdowns) / len(breakdowns), 2) if breakdowns else 0,
        "total": round(avg_score, 2)
    }
    return avg_score, breakdown, all_reasons


def preparar_competidores(competitors: List[Competidor]) -> List[Competidor]:
    for c in competitors:
        c.categoria_edad = get_categoria_edad(c.edad)
        asignar_bloque_correcto(c)
    return sorted(competitors, key=lambda c: (
        c.bloque,
        c.categoria_edad,
        c.sexo,
        c.cinta_block,
        c.edad,
        c.peso_kg,
        c.estatura_cm
    ))


def _maximum_weight_matching(competitors: List[Competidor], limits: Dict, score_min: float, nivel: int) -> List[Tuple[int, int]]:
    n = len(competitors)
    if n < 2:
        return []
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            c1, c2 = competitors[i], competitors[j]
            if c1.categoria_edad != c2.categoria_edad:
                continue
            if c1.sexo != c2.sexo:
                logger.warning(f"Intento de emparejar sexos diferentes: {c1.nombre} ({c1.sexo}) y {c2.nombre} ({c2.sexo})")
                continue
            if not bloques_adultos_compatibles(c1, c2):
                continue
            if not cintas_permitidas(c1, c2, nivel):
                continue
            puede, _ = puede_emparejarse(c1, c2, limits)
            if not puede:
                continue
            if not misma_modalidad_valida([c1.modalidad, c2.modalidad]):
                continue
            s, _ = _cached_score(c1, c2, limits)
            if s >= score_min:
                edges.append((i, j, s))
    if not edges:
        return []
    matched = set()
    edges_sorted = sorted(edges, key=lambda x: x[2], reverse=True)
    result = []
    for i, j, s in edges_sorted:
        if i not in matched and j not in matched:
            result.append((i, j))
            matched.add(i)
            matched.add(j)
    return result


def _formar_brackets_3_4(competitors: List[Competidor], limits: Dict, used_ids: Set[str], score_min: float, nivel: int) -> Tuple[List[Bracket], List[Competidor]]:
    disponibles = [c for c in competitors if c.id not in used_ids]
    if len(disponibles) < 3:
        return [], disponibles
    disponibles_sorted = sorted(disponibles, key=lambda c: c.peso_kg)
    brackets = []
    used_in_this_round = set()
    window = 10
    
    # 1. CUARTETOS
    i = 0
    while i < len(disponibles_sorted) - 3:
        c1 = disponibles_sorted[i]
        mejor_cuarteto = None
        mejor_avg = 0
        for j in range(i+1, min(i+window, len(disponibles_sorted)-2)):
            c2 = disponibles_sorted[j]
            for k in range(j+1, min(j+window, len(disponibles_sorted)-1)):
                c3 = disponibles_sorted[k]
                for l in range(k+1, min(k+window, len(disponibles_sorted))):
                    c4 = disponibles_sorted[l]
                    ids = {c1.id, c2.id, c3.id, c4.id}
                    if ids & used_in_this_round:
                        continue
                    if not (c1.sexo == c2.sexo == c3.sexo == c4.sexo):
                        continue
                    if not all(bloques_adultos_compatibles(a,b) for a,b in [(c1,c2),(c1,c3),(c1,c4),(c2,c3),(c2,c4),(c3,c4)]):
                        continue
                    pares = [(c1,c2),(c1,c3),(c1,c4),(c2,c3),(c2,c4),(c3,c4)]
                    ok_cintas = all(cintas_permitidas(a,b, nivel) for a,b in pares)
                    if not ok_cintas:
                        continue
                    ok_limites = all(puede_emparejarse(a,b, limits)[0] for a,b in pares)
                    if not ok_limites:
                        continue
                    modalidades = [c.modalidad for c in [c1,c2,c3,c4]]
                    if not misma_modalidad_valida(modalidades):
                        continue
                    scores = [_cached_score(a,b, limits)[0] for a,b in pares]
                    avg = sum(scores)/len(scores)
                    if avg >= score_min and avg > mejor_avg:
                        mejor_avg = avg
                        mejor_cuarteto = [c1,c2,c3,c4]
        if mejor_cuarteto:
            s, bd, razones = _calcular_bracket_score(mejor_cuarteto, limits)
            brackets.append(_crear_bracket(mejor_cuarteto, "normal", s, bd, "verde", False, None, "formacion_4", razones))
            used_in_this_round.update(c.id for c in mejor_cuarteto)
            disponibles_sorted = [c for c in disponibles_sorted if c.id not in used_in_this_round]
            i = 0
            continue
        i += 1
    
    # 2. TRÍOS
    i = 0
    while i < len(disponibles_sorted) - 2:
        c1 = disponibles_sorted[i]
        mejor_trio = None
        mejor_avg = 0
        for j in range(i+1, min(i+window, len(disponibles_sorted)-1)):
            c2 = disponibles_sorted[j]
            for k in range(j+1, min(j+window, len(disponibles_sorted))):
                c3 = disponibles_sorted[k]
                ids = {c1.id, c2.id, c3.id}
                if ids & used_in_this_round:
                    continue
                if not (c1.sexo == c2.sexo == c3.sexo):
                    continue
                if not all(bloques_adultos_compatibles(a,b) for a,b in [(c1,c2),(c1,c3),(c2,c3)]):
                    continue
                pares = [(c1,c2),(c1,c3),(c2,c3)]
                ok_cintas = all(cintas_permitidas(a,b, nivel) for a,b in pares)
                if not ok_cintas:
                    continue
                ok_limites = all(puede_emparejarse(a,b, limits)[0] for a,b in pares)
                if not ok_limites:
                    continue
                if not misma_modalidad_valida([c1.modalidad, c2.modalidad, c3.modalidad]):
                    continue
                s12, _ = _cached_score(c1, c2, limits)
                s13, _ = _cached_score(c1, c3, limits)
                s23, _ = _cached_score(c2, c3, limits)
                avg = (s12 + s13 + s23) / 3
                if avg >= score_min and avg > mejor_avg:
                    mejor_avg = avg
                    mejor_trio = (c1, c2, c3, j, k)
        if mejor_trio:
            c1, c2, c3, j, k = mejor_trio
            s, bd, razones = _calcular_bracket_score([c1, c2, c3], limits)
            brackets.append(_crear_bracket([c1, c2, c3], "normal", s, bd, "verde", False, None, "formacion_3", razones))
            used_in_this_round.update([c1.id, c2.id, c3.id])
            disponibles_sorted = [c for c in disponibles_sorted if c.id not in used_in_this_round]
            i = 0
            continue
        i += 1
    
    remaining = [c for c in competitors if c.id not in used_ids and c.id not in used_in_this_round]
    return brackets, remaining


def matching_global_con_relajacion(competitors: List[Competidor], nivel: int, limits: Dict, score_min: float) -> Tuple[List[Bracket], List[Competidor]]:
    if len(competitors) < 2:
        return [], competitors
    used_ids: Set[str] = set()
    brackets: List[Bracket] = []
    remaining = list(competitors)
    
    if nivel <= 3:
        trios_cuartetos, remaining = _formar_brackets_3_4(remaining, limits, used_ids, score_min, nivel)
        brackets.extend(trios_cuartetos)
        used_ids.update(c.id for b in trios_cuartetos for c in b.competidores)
        remaining = [c for c in remaining if c.id not in used_ids]
    
    pairs = _maximum_weight_matching(remaining, limits, score_min, nivel)
    for i, j in pairs:
        c1, c2 = remaining[i], remaining[j]
        s, bd, razones = _calcular_bracket_score([c1, c2], limits)
        color = RELAXATION_LEVELS[nivel-1]["color"] if nivel <= len(RELAXATION_LEVELS) else "rojo"
        requiere_aprob = nivel >= 3
        aprobador = None if not requiere_aprob else ("colaborador" if nivel == 3 else "coordinadora")
        brackets.append(_crear_bracket([c1, c2], f"nivel{nivel}", s, bd, color, requiere_aprob, aprobador, f"fase3_nivel{nivel}", razones))
        used_ids.update([c1.id, c2.id])
    
    remaining = [c for c in remaining if c.id not in used_ids]
    return brackets, remaining


def fase_2_5_reorganizar(brackets: List[Bracket], unpaired: List[Competidor]) -> Tuple[List[Bracket], List[Competidor]]:
    limits = {"peso": 5.0, "edad": 1.0, "estatura": 10.0}
    max_iter = 10
    for _ in range(max_iter):
        if not unpaired:
            break
        improved = False
        brackets_4 = [b for b in brackets if len(b.competidores) == 4 and _es_homogeneo(b.competidores)]
        if not brackets_4:
            break
        for u in unpaired[:]:
            best_option = None
            best_min_score = 0
            for b4 in brackets_4:
                comps = b4.competidores
                for i in range(4):
                    for j in range(i+1, 4):
                        if not (comps[i].sexo == comps[j].sexo == u.sexo):
                            continue
                        trio = [comps[i], comps[j], u]
                        resto = [comps[k] for k in range(4) if k not in (i,j)]
                        if len(resto) != 2:
                            continue
                        if resto[0].sexo != resto[1].sexo:
                            continue
                        if not _cumple_limites(trio, limits) or not _cumple_limites(resto, limits):
                            continue
                        score_trio = _score_promedio_bracket(trio, limits)
                        score_resto = _score_promedio_bracket(resto, limits)
                        if score_trio >= 60 and score_resto >= 60:
                            min_score = min(score_trio, score_resto)
                            if min_score > best_min_score:
                                best_min_score = min_score
                                best_option = (b4, trio, resto, score_trio, score_resto)
            if best_option:
                b4_original, trio, resto, s_trio, s_resto = best_option
                brackets.remove(b4_original)
                s_t, bd_t, rz_t = _calcular_bracket_score(trio, limits)
                s_r, bd_r, rz_r = _calcular_bracket_score(resto, limits)
                brackets.append(_crear_bracket(trio, "normal", s_t, bd_t, "amarillo", True, "coordinadora", "fase2_5", rz_t))
                brackets.append(_crear_bracket(resto, "normal", s_r, bd_r, "amarillo", True, "coordinadora", "fase2_5", rz_r))
                unpaired.remove(u)
                improved = True
                break
        if not improved:
            break
    return brackets, unpaired


def _es_homogeneo(competidores: List[Competidor]) -> bool:
    if len(competidores) < 2:
        return True
    pesos = [c.peso_kg for c in competidores]
    edades = [c.edad for c in competidores]
    estaturas = [c.estatura_cm for c in competidores]
    return (max(pesos)-min(pesos))/2 < 1.5 and max(edades)-min(edades) < 0.5 and (max(estaturas)-min(estaturas))/2 < 3


def _cumple_limites(competidores: List[Competidor], limits: Dict) -> bool:
    if len(competidores) < 2:
        return True
    peso_min = min(c.peso_kg for c in competidores)
    peso_max = max(c.peso_kg for c in competidores)
    if peso_max - peso_min > limits["peso"]:
        return False
    edad_min = min(c.edad for c in competidores)
    edad_max = max(c.edad for c in competidores)
    if edad_max - edad_min > limits["edad"]:
        return False
    est_min = min(c.estatura_cm for c in competidores)
    est_max = max(c.estatura_cm for c in competidores)
    if est_max - est_min > limits["estatura"]:
        return False
    return True


def _score_promedio_bracket(competidores: List[Competidor], limits: Dict) -> float:
    if len(competidores) < 2:
        return 0.0
    scores = []
    for i in range(len(competidores)):
        for j in range(i+1, len(competidores)):
            s, _ = _cached_score(competidores[i], competidores[j], limits)
            scores.append(s)
    return sum(scores)/len(scores) if scores else 0.0


def _limpiar_brackets_mixtos(brackets: List[Bracket], unpaired: List[Competidor]) -> Tuple[List[Bracket], List[Competidor]]:
    nuevos_brackets = []
    nuevos_unpaired = list(unpaired)
    for b in brackets:
        if _validar_sexo_bracket(b.competidores):
            nuevos_brackets.append(b)
        else:
            logger.warning(f"Bracket {b.id} con sexos mixtos, desarmando")
            nuevos_unpaired.extend(b.competidores)
    return nuevos_brackets, nuevos_unpaired


def generar_brackets(competitors: List[Competidor]) -> Results:
    global _score_cache
    _score_cache.clear()
    
    if not competitors:
        return Results(
            global_stats=GlobalStats(
                total_competidores=0, total_brackets=0, avg_bracket_size=0,
                brackets_2=0, brackets_3=0, brackets_4=0, sin_rival_total=0,
                excellent_brackets=0, low_quality_brackets=0, avg_score=0.0, emparejamiento_pct=0.0,
                brackets_verde=0, brackets_amarillo=0, brackets_naranja=0, brackets_rojo=0,
                etapa2_count=0, ronda1_count=0, ronda2_count=0, ronda3_count=0, ronda4_count=0,
                fase2_5_count=0, nivel5_count=0, nivel6_count=0, nivel7_count=0
            ),
            block_stats=[], brackets=[], unpaired=[]
        )
    
    competitors = preparar_competidores(competitors)
    
    grupos_iniciales: Dict[Tuple, List[Competidor]] = {}
    for c in competitors:
        cinta = get_cinta_normalizada(c.cinta_block)
        if cinta in ["Negra (Poom)", "Negra (Dan)"]:
            key = (c.bloque, c.categoria_edad, c.sexo, cinta, c.grado_raw)
        else:
            key = (c.bloque, c.categoria_edad, c.sexo, cinta)
        grupos_iniciales.setdefault(key, []).append(c)
    
    todos_brackets: List[Bracket] = []
    no_emparejados: List[Competidor] = []
    
    # Nivel 1
    for key, grupo in grupos_iniciales.items():
        brackets_n1, rest_n1 = matching_global_con_relajacion(grupo, 1, {"peso":5.0, "edad":1.0, "estatura":10}, 80)
        todos_brackets.extend(brackets_n1)
        no_emparejados.extend(rest_n1)
    
    # Fase 2.5
    todos_brackets, no_emparejados = fase_2_5_reorganizar(todos_brackets, no_emparejados)
    
    # Niveles 2 a 5 (relajación progresiva hasta máximos 6.5kg y 14cm)
    for nivel in range(2, 6):  # solo niveles 2,3,4,5
        if not no_emparejados:
            break
        config = RELAXATION_LEVELS[nivel-1]
        limits = {"peso": config["peso"], "edad": config["edad"], "estatura": config["estatura"]}
        score_min = config["score_min"]
        mezcla_cintas = config["mezcla_cintas"]
        
        grupos_relajados: Dict[Tuple, List[Competidor]] = {}
        for c in no_emparejados:
            key = (c.bloque, c.categoria_edad, c.sexo)
            grupos_relajados.setdefault(key, []).append(c)
        
        nuevos_brackets = []
        nuevos_no_emparejados = []
        for key, grupo in grupos_relajados.items():
            if not mezcla_cintas:
                subgrupos_cinta: Dict[str, List[Competidor]] = {}
                for c in grupo:
                    cinta = get_cinta_normalizada(c.cinta_block)
                    subgrupos_cinta.setdefault(cinta, []).append(c)
                for sub in subgrupos_cinta.values():
                    if len(sub) < 2:
                        nuevos_no_emparejados.extend(sub)
                        continue
                    b, r = matching_global_con_relajacion(sub, nivel, limits, score_min)
                    nuevos_brackets.extend(b)
                    nuevos_no_emparejados.extend(r)
            else:
                b, r = matching_global_con_relajacion(grupo, nivel, limits, score_min)
                nuevos_brackets.extend(b)
                nuevos_no_emparejados.extend(r)
        
        todos_brackets.extend(nuevos_brackets)
        no_emparejados = nuevos_no_emparejados
    
    # No hay último recurso: los que quedan se reportan como sin rival (revisión manual)
    sin_rival_final = [Unpaired(competidor=c, razon="No compatible partner after all relaxation levels") for c in no_emparejados]
    
    # Limpieza final de brackets mixtos (por si acaso)
    todos_brackets, _ = _limpiar_brackets_mixtos(todos_brackets, [])
    
    asignar_numeracion(todos_brackets, competitors)
    
    total_competidores = len(competitors)
    total_brackets = len(todos_brackets)
    brackets_2 = sum(1 for b in todos_brackets if len(b.competidores) == 2)
    brackets_3 = sum(1 for b in todos_brackets if len(b.competidores) == 3)
    brackets_4 = sum(1 for b in todos_brackets if len(b.competidores) == 4)
    excellent = sum(1 for b in todos_brackets if b.score >= 70)
    low_quality = sum(1 for b in todos_brackets if b.score < 30)
    all_scores = [b.score for b in todos_brackets]
    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0.0
    emparejados_count = total_competidores - len(sin_rival_final)
    emparejamiento_pct = (emparejados_count / total_competidores * 100) if total_competidores > 0 else 0.0
    
    brackets_verde = sum(1 for b in todos_brackets if b.nivel_aprobacion == "verde")
    brackets_amarillo = sum(1 for b in todos_brackets if b.nivel_aprobacion == "amarillo")
    brackets_naranja = sum(1 for b in todos_brackets if b.nivel_aprobacion == "naranja")
    brackets_rojo = sum(1 for b in todos_brackets if b.nivel_aprobacion == "rojo")
    
    etapa2_count = sum(1 for b in todos_brackets if b.ronda_origen == "fase3_nivel1")
    nivel2_count = sum(1 for b in todos_brackets if b.ronda_origen == "fase3_nivel2")
    nivel3_count = sum(1 for b in todos_brackets if b.ronda_origen == "fase3_nivel3")
    nivel4_count = sum(1 for b in todos_brackets if b.ronda_origen == "fase3_nivel4")
    nivel5_count = sum(1 for b in todos_brackets if b.ronda_origen == "fase3_nivel5")
    fase2_5_count = sum(1 for b in todos_brackets if b.ronda_origen == "fase2_5")
    
    avg_size = sum(len(b.competidores) for b in todos_brackets) / total_brackets if total_brackets > 0 else 0.0
    
    gs = GlobalStats(
        total_competidores=total_competidores,
        total_brackets=total_brackets,
        avg_bracket_size=round(avg_size, 1),
        brackets_2=brackets_2,
        brackets_3=brackets_3,
        brackets_4=brackets_4,
        sin_rival_total=len(sin_rival_final),
        excellent_brackets=excellent,
        low_quality_brackets=low_quality,
        brackets_verde=brackets_verde,
        brackets_amarillo=brackets_amarillo,
        brackets_naranja=brackets_naranja,
        brackets_rojo=brackets_rojo,
        etapa2_count=etapa2_count,
        ronda1_count=etapa2_count,
        ronda2_count=nivel2_count,
        ronda3_count=nivel3_count,
        ronda4_count=nivel4_count,
        fase2_5_count=fase2_5_count,
        nivel5_count=nivel5_count,
        nivel6_count=0,
        nivel7_count=0,
        avg_score=round(avg_score, 2),
        emparejamiento_pct=round(emparejamiento_pct, 1),
    )
    
    block_stats_dict: Dict[str, Dict] = {}
    for b in todos_brackets:
        bloque = b.competidores[0].bloque
        if bloque not in block_stats_dict:
            block_stats_dict[bloque] = {"competidores": set(), "brackets": 0, "sin_rival": 0}
        block_stats_dict[bloque]["brackets"] += 1
        for c in b.competidores:
            block_stats_dict[bloque]["competidores"].add(c.id)
    for u in sin_rival_final:
        bloque = u.competidor.bloque
        if bloque not in block_stats_dict:
            block_stats_dict[bloque] = {"competidores": set(), "brackets": 0, "sin_rival": 0}
        block_stats_dict[bloque]["sin_rival"] += 1
    
    block_stats = []
    for bloque in BLOCK_ORDER:
        if bloque in block_stats_dict:
            data = block_stats_dict[bloque]
            total_comp_bloque = len(data["competidores"]) + data["sin_rival"]
            bs = BlockStats(
                bloque=bloque,
                competidores=total_comp_bloque,
                brackets=data["brackets"],
                avg_size=round(len(data["competidores"]) / data["brackets"], 1) if data["brackets"] > 0 else 0,
                sin_rival=data["sin_rival"],
                relaxed_count=0
            )
            block_stats.append(bs)
    
    return Results(
        global_stats=gs,
        block_stats=block_stats,
        brackets=todos_brackets,
        unpaired=sin_rival_final
    )


def generate_results(competitors: List[Competidor]) -> Results:
    return generar_brackets(competitors)


def asignar_numeracion(brackets: List[Bracket], todos_competidores: List[Competidor]) -> None:
    por_bloque: Dict[str, List[Competidor]] = {}
    for c in todos_competidores:
        if c.bloque not in por_bloque:
            por_bloque[c.bloque] = []
        por_bloque[c.bloque].append(c)
    for bloque, comps in por_bloque.items():
        prefijo = BLOCK_PREFIXES.get(bloque, "XX")
        for idx, c in enumerate(sorted(comps, key=lambda x: (x.edad, x.peso_kg)), start=1):
            c.numero_competidor = f"{prefijo} {idx}"
    graf_num = 1
    for bloque in BLOCK_ORDER:
        brackets_bloque = [b for b in brackets if b.competidores[0].bloque == bloque]
        for b in sorted(brackets_bloque, key=lambda x: x.id):
            b.numero = graf_num
            b.area = ((graf_num - 1) % 12) + 1
            graf_num += 1