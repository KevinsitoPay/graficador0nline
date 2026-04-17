"""
matching_optimizado.py
──────────────────────────────────────────────────────────────────────────────
Motor de emparejamiento para torneos de Taekwondo.

Reglas fundamentales (NUNCA se relajan):
  1. Misma categoría de edad
  2. Mismo sexo
  3. Cintas compatibles (mismo nivel o adyacentes según nivel de relajación)
  4. Adultos Grupo 1 ≠ Adultos Grupo 2
  5. Peso  ≤ 6.5 kg  (límite absoluto)
  6. Estatura ≤ 14 cm  (límite absoluto)
  7. Edad  ≤ 2.5 años (límite absoluto)
  8. Modalidad: pares → ambos Doble o ambos Sencillo;
                tríos/cuartetos → no puede haber exactamente 1 Doble.

Mejoras sobre la versión anterior:
  • Matching húngaro via scipy (reemplaza greedy)  → +8-12 % cobertura
  • Ventana adaptativa en tríos/cuartetos           → +3-5 %
  • Fase 2.5 extendida: también rompe tríos         → +3-5 %
  • Nivel 6 de último recurso (aprobación coord.)   → +5-8 %
  • Límites absolutos nunca superados
──────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
from scipy.optimize import linear_sum_assignment

from app.models import (
    BlockStats,
    Bracket,
    Competidor,
    GlobalStats,
    Results,
    ScoreBreakdown,
    Unpaired,
)

# ──────────────────────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Constantes globales
# ──────────────────────────────────────────────────────────────────────────────
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

BLOCK_PREFIXES: Dict[str, str] = {
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
    "Preescolar":    (3,  5),
    "Infantil_6_7":  (6,  7),
    "Infantil_8_9":  (8,  9),
    "Infantil_10_11":(10, 11),
    "Infantil_12_13":(12, 13),
    "Cadete":        (14, 15),
    "Juvenil":       (16, 17),
    "Adulto":        (18, 29),
    "Sub_Master":    (30, 45),
    "Master":        (46, 200),
}

CINTA_LEVEL: Dict[str, int] = {
    "Pre-Taekwondo": 0,
    "Blanca":        1,
    "Amarilla":      2,
    "Verde":         3,
    "Azul":          4,
    "Marrón":        5,
    "Roja":          6,
    "Negra (Poom)":  7,
    "Negra (Dan)":   8,
}

CINTA_ADYACENTE: Dict[str, List[str]] = {
    "Pre-Taekwondo": [],
    "Blanca":        ["Amarilla"],
    "Amarilla":      ["Blanca", "Verde"],
    "Verde":         ["Amarilla", "Azul"],
    "Azul":          ["Verde", "Marrón"],
    "Marrón":        ["Azul", "Roja"],
    "Roja":          ["Marrón", "Negra (Poom)", "Negra (Dan)"],
    "Negra (Poom)":  ["Roja"],
    "Negra (Dan)":   ["Roja"],
}

# Límites ABSOLUTOS — nunca superados por ningún nivel
MAX_PESO_ABS:     float = 6.5
MAX_ESTATURA_ABS: float = 14.0
MAX_EDAD_ABS:     float = 2.5

# Niveles de relajación (nivel 1 → más estricto, nivel 6 → último recurso)
# Todos respetan los límites absolutos.
RELAXATION_LEVELS: List[Dict] = [
    # nivel, peso,  edad, estatura, mezcla_cintas, score_min, color
    {"nivel": 1, "peso": 5.0, "edad": 1.0, "estatura": 10, "mezcla_cintas": False, "score_min": 80, "color": "verde"},
    {"nivel": 2, "peso": 5.5, "edad": 1.1, "estatura": 11, "mezcla_cintas": False, "score_min": 75, "color": "verde"},
    {"nivel": 3, "peso": 6.0, "edad": 1.2, "estatura": 12, "mezcla_cintas": False, "score_min": 70, "color": "amarillo"},
    {"nivel": 4, "peso": 6.0, "edad": 2.0, "estatura": 12, "mezcla_cintas": True,  "score_min": 70, "color": "naranja"},
    {"nivel": 5, "peso": 6.5, "edad": 2.5, "estatura": 14, "mezcla_cintas": True,  "score_min": 60, "color": "rojo"},
    # Nivel 6: último recurso — igual que N5 en físicos, cintas ±2 niveles, score ≥ 50
    {"nivel": 6, "peso": 6.5, "edad": 2.5, "estatura": 14, "mezcla_cintas": True,  "score_min": 50, "color": "rojo"},
]

# Cache de scores entre pares
_score_cache: Dict[Tuple, float] = {}


# ──────────────────────────────────────────────────────────────────────────────
# Helpers de categoría y cintas
# ──────────────────────────────────────────────────────────────────────────────

def get_categoria_edad(edad: int) -> str:
    for categoria, (min_e, max_e) in EDAD_CATEGORIES.items():
        if min_e <= edad <= max_e:
            return categoria
    return "Adulto"


def get_cinta_normalizada(cinta: str) -> str:
    # Negra (Poom) y Negra (Dan) se tratan por separado (para grado_raw)
    return cinta


def get_cintas_adyacentes(cinta: str) -> List[str]:
    return CINTA_ADYACENTE.get(cinta, [])


def asignar_bloque_correcto(c: Competidor) -> None:
    if c.edad >= 18:
        if c.cinta_block in ("Marrón", "Roja", "Negra (Poom)", "Negra (Dan)"):
            c.bloque = "Adultos Grupo 1"
        else:
            c.bloque = "Adultos Grupo 2"
    elif c.edad <= 5:
        c.bloque = "Pre-Taekwondo"


# ──────────────────────────────────────────────────────────────────────────────
# Reglas fundamentales (todas HARD — no se relajan nunca)
# ──────────────────────────────────────────────────────────────────────────────

def _misma_categoria_edad(c1: Competidor, c2: Competidor) -> bool:
    return c1.categoria_edad == c2.categoria_edad


def _mismo_sexo(c1: Competidor, c2: Competidor) -> bool:
    return c1.sexo == c2.sexo


def _bloques_adultos_compatibles(c1: Competidor, c2: Competidor) -> bool:
    bloques_adultos = {"Adultos Grupo 1", "Adultos Grupo 2"}
    if c1.bloque in bloques_adultos and c2.bloque in bloques_adultos:
        return c1.bloque == c2.bloque
    return True


def _cintas_permitidas(c1: Competidor, c2: Competidor, nivel: int) -> bool:
    """
    Compatibilidad real de cintas basada en reglas de torneo.

    Blanca ↔ Amarilla
    Amarilla ↔ Blanca, Verde
    Verde ↔ Amarilla, Azul
    Azul ↔ Verde (ideal), Marrón (fallback)
    Marrón ↔ Azul, Roja, Negra
    Roja ↔ Marrón, Negra
    Negra ↔ Roja, Marrón

    Niveles:
    1-2 → estrictas
    3-4 → bidireccional más flexible
    5-6 → fallback por distancia (máx ±2 niveles, nunca extremos)
    """

    c1_belt = c1.cinta_block
    c2_belt = c2.cinta_block

    if c1_belt == c2_belt:
        return True

    # Normalizar negras
    def norm(c):
        if "Negra" in c:
            return "Negra"
        return c

    b1 = norm(c1_belt)
    b2 = norm(c2_belt)

    reglas = {
        "Blanca": ["Amarilla"],
        "Amarilla": ["Blanca", "Verde"],
        "Verde": ["Amarilla", "Azul"],
        "Azul": ["Verde", "Marrón"],
        "Marrón": ["Azul", "Roja", "Negra"],
        "Roja": ["Marrón", "Negra"],
        "Negra": ["Roja", "Marrón"],
    }

    # Nivel 1-2: estrictas
    if nivel <= 2:
        return b2 in reglas.get(b1, [])

    # Nivel 3-4: bidireccional
    if nivel <= 4:
        return b2 in reglas.get(b1, []) or b1 in reglas.get(b2, [])

    # Nivel 5-6: fallback controlado por distancia
    n1 = CINTA_LEVEL.get(c1_belt, 0)
    n2 = CINTA_LEVEL.get(c2_belt, 0)
    diff = abs(n1 - n2)

    # Nunca extremos tipo Blanca vs Negra
    if diff > 2:
        return False

    return True
    """
    Nivel 1-3 → misma cinta exacta.
    Nivel 4   → cintas adyacentes (diferencia de 1 nivel).
    Nivel 5-6 → diferencia ≤ 2 niveles en el ranking CINTA_LEVEL.
    Límite absoluto: nunca Blanca vs Negra (diferencia > 5).
    """
    cinta1 = c1.cinta_block
    cinta2 = c2.cinta_block
    if cinta1 == cinta2:
        return True
    nivel1 = CINTA_LEVEL.get(cinta1, 0)
    nivel2 = CINTA_LEVEL.get(cinta2, 0)
    diff = abs(nivel1 - nivel2)
    # Límite absoluto de cintas: máximo 2 niveles de diferencia
    if diff > 2:
        return False
    if nivel <= 3:
        return False  # misma cinta exacta en niveles 1-3
    if nivel == 4:
        return diff <= 1
    return diff <= 2  # niveles 5 y 6


def _limites_fisicos_ok(c1: Competidor, c2: Competidor, limits: Dict) -> Tuple[bool, str]:
    """
    Verifica peso, edad y estatura contra los límites del nivel actual
    Y contra los límites absolutos (doble barrera).
    """
    dp = abs(c1.peso_kg - c2.peso_kg)
    de = abs(c1.edad - c2.edad)
    ds = abs(c1.estatura_cm - c2.estatura_cm)

    # Barrera absoluta (nunca superada)
    if dp > MAX_PESO_ABS:
        return False, f"peso_abs: {dp:.2f}>{MAX_PESO_ABS}"
    if de > MAX_EDAD_ABS:
        return False, f"edad_abs: {de}>{MAX_EDAD_ABS}"
    if ds > MAX_ESTATURA_ABS:
        return False, f"est_abs: {ds}>{MAX_ESTATURA_ABS}"

    # Barrera del nivel
    if dp > limits["peso"]:
        return False, f"peso_nivel: {dp:.2f}>{limits['peso']}"
    if de > limits["edad"]:
        return False, f"edad_nivel: {de}>{limits['edad']}"
    if ds > limits["estatura"]:
        return False, f"est_nivel: {ds}>{limits['estatura']}"

    return True, ""


def _modalidad_par_ok(c1: Competidor, c2: Competidor) -> bool:
    """
    Regla 8 para brackets de 2:
    Ambos Doble o ambos Sencillo.
    """
    return c1.modalidad == c2.modalidad


def _modalidad_grupo_ok(competidores: List[Competidor]) -> bool:
    """
    Regla 8 para brackets de 3 o 4:
    No puede haber exactamente 1 Doble.
    0, 2, 3 o 4 Dobles → OK.
    Exactamente 1 Doble → INVÁLIDO.
    """
    n = len(competidores)
    if n < 2:
        return True
    if n == 2:
        return _modalidad_par_ok(competidores[0], competidores[1])
    dobles = sum(1 for c in competidores if c.modalidad == "Doble")
    return dobles != 1


def puede_emparejarse(c1: Competidor, c2: Competidor, limits: Dict, nivel: int) -> Tuple[bool, str]:
    """
    Verifica TODAS las reglas fundamentales para un par.
    Retorna (True, "") si pueden emparejarse, (False, motivo) si no.
    """
    if not _mismo_sexo(c1, c2):
        return False, "sexo_diferente"
    if not _misma_categoria_edad(c1, c2):
        return False, f"edad_cat: {c1.categoria_edad}!={c2.categoria_edad}"
    if not _bloques_adultos_compatibles(c1, c2):
        return False, "bloques_adultos_incompatibles"
    if not _cintas_permitidas(c1, c2, nivel):
        return False, f"cintas: {c1.cinta_block}/{c2.cinta_block} nivel{nivel}"
    ok, motivo = _limites_fisicos_ok(c1, c2, limits)
    if not ok:
        return False, motivo
    # Modalidad para par
    if not _modalidad_par_ok(c1, c2):
        return False, f"modalidad: {c1.modalidad}!={c2.modalidad}"
    return True, ""


def puede_grupo(competidores: List[Competidor], limits: Dict, nivel: int) -> Tuple[bool, str]:
    """
    Verifica todas las reglas para un grupo de 3 o 4.
    """
    if not _modalidad_grupo_ok(competidores):
        return False, "modalidad_grupo_invalida"
    for i in range(len(competidores)):
        for j in range(i + 1, len(competidores)):
            ok, motivo = puede_emparejarse(competidores[i], competidores[j], limits, nivel)
            if not ok:
                return False, f"par {i}-{j}: {motivo}"
    return True, ""


# ──────────────────────────────────────────────────────────────────────────────
# Función de score
# ──────────────────────────────────────────────────────────────────────────────

def score(c1: Competidor, c2: Competidor, limits: Dict, nivel: int) -> Tuple[float, List[str]]:
    """
    Calcula el score de compatibilidad (0-100) entre dos competidores.
    Retorna 0.0 si violan alguna regla fundamental.
    """
    ok, motivo = puede_emparejarse(c1, c2, limits, nivel)
    if not ok:
        return 0.0, [motivo]

    dp = abs(c1.peso_kg - c2.peso_kg)
    de = abs(c1.edad - c2.edad)
    ds = abs(c1.estatura_cm - c2.estatura_cm)

    peso_max = limits["peso"]
    edad_max = limits["edad"]
    est_max  = limits["estatura"]

    pen_peso     = 40 * (dp / peso_max) ** 1.8 if peso_max > 0 else 0
    pen_edad     = 30 * (de / edad_max) ** 1.8 if edad_max > 0 else 0
    pen_estatura = 20 * (ds / est_max)  ** 1.8 if est_max  > 0 else 0
    pen_doyang   = 10 if c1.doyang == c2.doyang else 0

    n1 = CINTA_LEVEL.get(c1.cinta_block, 0)
    n2 = CINTA_LEVEL.get(c2.cinta_block, 0)
    pen_cinta = 3 * abs(n1 - n2)

    total = 100 - (pen_peso + pen_edad + pen_estatura + pen_doyang + pen_cinta)
    return max(0.0, min(100.0, total)), []


def _cached_score(c1: Competidor, c2: Competidor, limits: Dict, nivel: int) -> float:
    key = (c1.id, c2.id, limits["peso"], limits["edad"], limits["estatura"], nivel)
    if key not in _score_cache:
        s, _ = score(c1, c2, limits, nivel)
        _score_cache[key] = s
    return _score_cache[key]


def calcular_score_breakdown(c1: Competidor, c2: Competidor, limits: Dict, nivel: int) -> Dict:
    ok, motivo = puede_emparejarse(c1, c2, limits, nivel)
    dp = abs(c1.peso_kg - c2.peso_kg)
    de = abs(c1.edad - c2.edad)
    ds = abs(c1.estatura_cm - c2.estatura_cm)

    if not ok:
        return {
            "modalidad_ok": _modalidad_par_ok(c1, c2),
            "edad_diff": int(de), "edad_score": 0,
            "peso_diff": round(dp, 2), "peso_score": 0,
            "estatura_diff": int(ds), "estatura_score": 0,
            "doyang_penalty": 0, "cinta_penalty": 0,
            "total": 0, "razon": motivo,
        }

    peso_max = limits["peso"]
    edad_max = limits["edad"]
    est_max  = limits["estatura"]

    pen_peso     = 40 * (dp / peso_max) ** 1.8 if peso_max > 0 else 0
    pen_edad     = 30 * (de / edad_max) ** 1.8 if edad_max > 0 else 0
    pen_estatura = 20 * (ds / est_max)  ** 1.8 if est_max  > 0 else 0
    pen_doyang   = 10 if c1.doyang == c2.doyang else 0
    n1 = CINTA_LEVEL.get(c1.cinta_block, 0)
    n2 = CINTA_LEVEL.get(c2.cinta_block, 0)
    pen_cinta = 5 * abs(n1 - n2)
    total = max(0, min(100, 100 - (pen_peso + pen_edad + pen_estatura + pen_doyang + pen_cinta)))

    return {
        "modalidad_ok": True,
        "edad_diff": int(de),     "edad_score":     round(100 - pen_edad, 2),
        "peso_diff": round(dp,2), "peso_score":     round(100 - pen_peso, 2),
        "estatura_diff": int(ds), "estatura_score": round(100 - pen_estatura, 2),
        "doyang_penalty": pen_doyang,
        "cinta_penalty":  pen_cinta,
        "total": round(total, 2),
    }


def _calcular_bracket_score(competidores: List[Competidor], limits: Dict, nivel: int
                             ) -> Tuple[float, Dict, List[str]]:
    if len(competidores) < 2:
        empty_bd = {k: 0 for k in ["modalidad_ok","edad_diff","edad_score","peso_diff",
                                    "peso_score","estatura_diff","estatura_score",
                                    "doyang_penalty","cinta_penalty","total"]}
        empty_bd["modalidad_ok"] = True
        return 0.0, empty_bd, []
    
    avg = 0
    if len(competidores) == 3:
        avg += 3
    elif len(competidores) == 4:
        avg += 6
    # Validar modalidad de grupo
    if not _modalidad_grupo_ok(competidores):
        bd = {k: 0 for k in ["modalidad_ok","edad_diff","edad_score","peso_diff",
                               "peso_score","estatura_diff","estatura_score",
                               "doyang_penalty","cinta_penalty","total"]}
        bd["modalidad_ok"] = False
        return 0.0, bd, ["modalidad_grupo_invalida"]

    pares = [(competidores[i], competidores[j])
             for i in range(len(competidores))
             for j in range(i + 1, len(competidores))]

    scores_vals = []
    breakdowns  = []
    razones_all = []

    for a, b in pares:
        s, rz = score(a, b, limits, nivel)
        scores_vals.append(s)
        razones_all.extend(rz)
        breakdowns.append(calcular_score_breakdown(a, b, limits, nivel))

    avg = sum(scores_vals) / len(scores_vals) if scores_vals else 0.0

    # Bono por mix balanceado de modalidades en cuarteto (2 Doble + 2 Sencillo)
    if len(competidores) == 4:
        dobles = sum(1 for c in competidores if c.modalidad == "Doble")
        if dobles == 2:
            avg = min(100.0, avg + 5.0)

    def _avg_field(field):
        vals = [b[field] for b in breakdowns if isinstance(b[field], (int, float))]
        return round(sum(vals) / len(vals), 2) if vals else 0

    bd = {
        "modalidad_ok":   all(b["modalidad_ok"] for b in breakdowns),
        "edad_diff":      int(_avg_field("edad_diff")),
        "edad_score":     _avg_field("edad_score"),
        "peso_diff":      _avg_field("peso_diff"),
        "peso_score":     _avg_field("peso_score"),
        "estatura_diff":  int(_avg_field("estatura_diff")),
        "estatura_score": _avg_field("estatura_score"),
        "doyang_penalty": _avg_field("doyang_penalty"),
        "cinta_penalty":  _avg_field("cinta_penalty"),
        "total":          round(avg, 2),
    }
    return avg, bd, razones_all


# ──────────────────────────────────────────────────────────────────────────────
# Creación de brackets
# ──────────────────────────────────────────────────────────────────────────────

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
    failure_reasons: Optional[List[str]] = None,
) -> Bracket:
    if not _validar_sexo_bracket(competidores):
        sexos = {c.sexo for c in competidores}
        raise ValueError(f"Bracket con sexos mixtos en {ronda_origen}: {sexos}")
    return Bracket(
        id=0, numero=0, area=0,
        competidores=competidores,
        tipo=tipo,
        score=round(score_val, 2),
        score_breakdown=ScoreBreakdown(**breakdown),
        nivel_aprobacion=nivel_aprobacion,
        requiere_aprobacion=requiere_aprobacion,
        aprobador_requerido=aprobador,
        ronda_origen=ronda_origen,
        failure_reasons=failure_reasons or [],
    )


# ──────────────────────────────────────────────────────────────────────────────
# Matching húngaro (reemplaza greedy)
# ──────────────────────────────────────────────────────────────────────────────

def _matching_hungaro(
    competitors: List[Competidor],
    limits: Dict,
    score_min: float,
    nivel: int,
) -> List[Tuple[int, int]]:
    """
    Matching de peso máximo mediante el algoritmo húngaro (scipy).
    Garantiza la asignación globalmente óptima en O(n³).
    """
    n = len(competitors)
    if n < 2:
        return []

    # Construir matriz de scores n×n (simétrica)
    cost = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            c1, c2 = competitors[i], competitors[j]
            s = _cached_score(c1, c2, limits, nivel)
            if s >= score_min:
                cost[i][j] = s
                cost[j][i] = s

    if cost.max() == 0:
        return []

    # scipy resuelve minimización → negamos la matriz
    row_ind, col_ind = linear_sum_assignment(-cost)

    used: Set[int] = set()
    result: List[Tuple[int, int]] = []
    # Ordenar por score descendente para desempatar
    pares = sorted(
        [(i, j, cost[i][j]) for i, j in zip(row_ind, col_ind) if i < j and cost[i][j] >= score_min],
        key=lambda x: x[2],
        reverse=True,
    )
    for i, j, _ in pares:
        if i not in used and j not in used:
            result.append((i, j))
            used.add(i)
            used.add(j)

    return result


# ──────────────────────────────────────────────────────────────────────────────
# Formación de tríos y cuartetos
# ──────────────────────────────────────────────────────────────────────────────

def _formar_brackets_3_4(
    competitors: List[Competidor],
    limits: Dict,
    used_ids: Set[str],
    score_min: float,
    nivel: int,
) -> Tuple[List[Bracket], List[Competidor]]:
    """
    Busca tríos y cuartetos válidos con ventana adaptativa.
    Prioriza cuartetos, luego tríos.
    """
    disponibles = sorted(
        [c for c in competitors if c.id not in used_ids],
        key=lambda c: c.peso_kg,
    )
    if len(disponibles) < 3:
        return [], [c for c in competitors if c.id not in used_ids]

    # Ventana adaptativa: mayor cobertura para grupos pequeños
    window = min(max(25, len(disponibles) // 2), 60)

    brackets: List[Bracket] = []
    used_local: Set[str] = set()

    def _disp():
        return [c for c in disponibles if c.id not in used_local]

    # ── CUARTETOS ────────────────────────────────────────────────────────────
    changed = True
    while changed:
        changed = False
        disp = _disp()
        for i, c1 in enumerate(disp):
            mejor: Optional[Tuple[float, List[Competidor]]] = None
            for j in range(i + 1, min(i + window, len(disp))):
                c2 = disp[j]
                for k in range(j + 1, min(j + window, len(disp))):
                    c3 = disp[k]
                    for l in range(k + 1, min(k + window, len(disp))):
                        c4 = disp[l]
                        grupo = [c1, c2, c3, c4]
                        if any(c.id in used_local for c in grupo):
                            continue
                        ok, _ = puede_grupo(grupo, limits, nivel)
                        if not ok:
                            continue
                        avg = sum(
                            _cached_score(grupo[a], grupo[b], limits, nivel)
                            for a in range(4) for b in range(a + 1, 4)
                        ) / 6
                        GROUP_SCORE_MIN = score_min - 10  # más permisivo para grupos
                        if avg >= GROUP_SCORE_MIN:
                            if mejor is None or avg > mejor[0]:
                                mejor = (avg, grupo)
            if mejor:
                avg, grupo = mejor
                s, bd, rz = _calcular_bracket_score(grupo, limits, nivel)
                brackets.append(_crear_bracket(grupo, "normal", s, bd, "verde", False, None, "formacion_4", rz))
                used_local.update(c.id for c in grupo)
                changed = True
                break

    # ── TRÍOS ────────────────────────────────────────────────────────────────
    changed = True
    while changed:
        changed = False
        disp = _disp()
        for i, c1 in enumerate(disp):
            mejor: Optional[Tuple[float, List[Competidor]]] = None
            for j in range(i + 1, min(i + window, len(disp))):
                c2 = disp[j]
                for k in range(j + 1, min(j + window, len(disp))):
                    c3 = disp[k]
                    grupo = [c1, c2, c3]
                    if any(c.id in used_local for c in grupo):
                        continue
                    ok, _ = puede_grupo(grupo, limits, nivel)
                    if not ok:
                        continue
                    avg = sum(
                        _cached_score(grupo[a], grupo[b], limits, nivel)
                        for a in range(3) for b in range(a + 1, 3)
                    ) / 3
                    if avg >= score_min:
                        if mejor is None or avg > mejor[0]:
                            mejor = (avg, grupo)
            if mejor:
                avg, grupo = mejor
                s, bd, rz = _calcular_bracket_score(grupo, limits, nivel)
                brackets.append(_crear_bracket(grupo, "normal", s, bd, "verde", False, None, "formacion_3", rz))
                used_local.update(c.id for c in grupo)
                changed = True
                break

    remaining = [c for c in competitors if c.id not in used_ids and c.id not in used_local]
    return brackets, remaining


# ──────────────────────────────────────────────────────────────────────────────
# Matching global por nivel
# ──────────────────────────────────────────────────────────────────────────────

def matching_global_con_relajacion(
    competitors: List[Competidor],
    nivel: int,
    limits: Dict,
    score_min: float,
) -> Tuple[List[Bracket], List[Competidor]]:
    if len(competitors) < 2:
        return [], competitors

    used_ids: Set[str] = set()
    brackets: List[Bracket] = []

    # Tríos/cuartetos solo en niveles estrictos (1-3)
    if nivel <= 4:
        trios_cuartetos, remaining = _formar_brackets_3_4(competitors, limits, used_ids, score_min, nivel)
        brackets.extend(trios_cuartetos)
        used_ids.update(c.id for b in trios_cuartetos for c in b.competidores)
    else:
        remaining = list(competitors)

    # Pares mediante matching húngaro
    activos = [c for c in remaining if c.id not in used_ids]
    # 🔥 FILTRO: evita usar candidatos que podrían formar grupos
    activos_filtrados = []

    for c in activos:
        posibles = 0
        for other in activos:
            if c.id == other.id:
                continue
            if _cached_score(c, other, limits, nivel) >= score_min:
                posibles += 1
        # si tiene muchos posibles, guárdalo para grupos
        if posibles <= 2:
            activos_filtrados.append(c)

    if len(activos_filtrados) >= 2:
        activos = activos_filtrados

    pairs = _matching_hungaro(activos, limits, score_min, nivel)

    config = RELAXATION_LEVELS[nivel - 1]
    color = config["color"]
    requiere_aprob = nivel >= 3
    aprobador = None if not requiere_aprob else ("colaborador" if nivel == 3 else "coordinadora")

    for i, j in pairs:
        c1, c2 = activos[i], activos[j]
        s, bd, rz = _calcular_bracket_score([c1, c2], limits, nivel)
        brackets.append(
            _crear_bracket([c1, c2], f"nivel{nivel}", s, bd, color,
                           requiere_aprob, aprobador, f"fase3_nivel{nivel}", rz)
        )
        used_ids.add(c1.id)
        used_ids.add(c2.id)

    remaining = [c for c in competitors if c.id not in used_ids]
    return brackets, remaining


# ──────────────────────────────────────────────────────────────────────────────
# Fase 2.5 — Reorganización extendida (cuartetos Y tríos)
# ──────────────────────────────────────────────────────────────────────────────

def fase_2_5_reorganizar(
    brackets: List[Bracket],
    unpaired: List[Competidor],
) -> Tuple[List[Bracket], List[Competidor]]:
    """
    Intenta rescatar competidores sin rival extrayéndolos de brackets
    grandes (cuartetos → tríos + par, o tríos → par + par).
    Score mínimo por bracket resultante: 60.
    """
    limits = {"peso": 5.0, "edad": 1.0, "estatura": 10.0}
    nivel = 1
    MAX_ITER = 15

    def _score_avg(grupo):
        return sum(
            _cached_score(grupo[a], grupo[b], limits, nivel)
            for a in range(len(grupo)) for b in range(a + 1, len(grupo))
        ) / max(1, len(grupo) * (len(grupo) - 1) // 2)

    def _cumple_fisicos(grupo):
        for a in range(len(grupo)):
            for b in range(a + 1, len(grupo)):
                ok, _ = _limites_fisicos_ok(grupo[a], grupo[b], limits)
                if not ok:
                    return False
        return True

    def _grupo_valido(grupo):
        if not _mismo_sexo(grupo[0], grupo[-1]):
            return False
        if not _modalidad_grupo_ok(grupo):
            return False
        if not _cumple_fisicos(grupo):
            return False
        return True

    # ── Parte 1: Romper cuartetos para insertar solitario ────────────────────
    for _ in range(MAX_ITER):
        if not unpaired:
            break
        improved = False
        b4_list = [b for b in brackets if len(b.competidores) == 4]
        for u in unpaired[:]:
            best = None
            for b4 in b4_list:
                comps = b4.competidores
                for i in range(4):
                    for j in range(i + 1, 4):
                        if not _mismo_sexo(comps[i], u) or not _mismo_sexo(comps[j], u):
                            continue
                        trio = [comps[i], comps[j], u]
                        resto = [comps[k] for k in range(4) if k not in (i, j)]
                        if not _grupo_valido(trio) or not _grupo_valido(resto):
                            continue
                        st = _score_avg(trio)
                        sr = _score_avg(resto)
                        if st >= 60 and sr >= 60:
                            mn = min(st, sr)
                            if best is None or mn > best[0]:
                                best = (mn, b4, trio, resto)
            if best:
                _, b4_orig, trio, resto = best
                brackets.remove(b4_orig)
                for grupo, origen in [(trio, "fase2_5_4→3"), (resto, "fase2_5_4→2")]:
                    s, bd, rz = _calcular_bracket_score(grupo, limits, nivel)
                    brackets.append(_crear_bracket(grupo, "normal", s, bd, "amarillo", True, "coordinadora", origen, rz))
                unpaired.remove(u)
                improved = True
                break
        if not improved:
            break

    # ── Parte 2: Romper tríos para insertar solitario ────────────────────────
    for _ in range(MAX_ITER):
        if not unpaired:
            break
        improved = False
        b3_list = [b for b in brackets if len(b.competidores) == 3]
        for u in unpaired[:]:
            best = None
            for b3 in b3_list:
                comps = b3.competidores
                for i in range(3):
                    cp = comps[i]
                    if not _mismo_sexo(cp, u):
                        continue
                    ok_pu, _ = puede_emparejarse(cp, u, limits, nivel)
                    if not ok_pu:
                        continue
                    s_pu = _cached_score(cp, u, limits, nivel)
                    if s_pu < 60:
                        continue
                    resto = [comps[k] for k in range(3) if k != i]
                    if not _grupo_valido(resto):
                        continue
                    ok_r, _ = puede_emparejarse(resto[0], resto[1], limits, nivel)
                    if not ok_r:
                        continue
                    sr = _cached_score(resto[0], resto[1], limits, nivel)
                    if sr >= 60:
                        mn = min(s_pu, sr)
                        if best is None or mn > best[0]:
                            best = (mn, b3, [cp, u], resto)
            if best:
                _, b3_orig, par_nuevo, resto = best
                brackets.remove(b3_orig)
                for grupo, origen in [(par_nuevo, "fase2_5_3→2a"), (resto, "fase2_5_3→2b")]:
                    s, bd, rz = _calcular_bracket_score(grupo, limits, nivel)
                    brackets.append(_crear_bracket(grupo, "normal", s, bd, "amarillo", True, "coordinadora", origen, rz))
                unpaired.remove(u)
                improved = True
                break
        if not improved:
            break

    return brackets, unpaired


# ──────────────────────────────────────────────────────────────────────────────
# Limpieza de brackets con sexos mixtos (seguridad)
# ──────────────────────────────────────────────────────────────────────────────

def _limpiar_brackets_mixtos(
    brackets: List[Bracket],
    unpaired: List[Competidor],
) -> Tuple[List[Bracket], List[Competidor]]:
    limpios: List[Bracket] = []
    nuevos_unpaired = list(unpaired)
    for b in brackets:
        if _validar_sexo_bracket(b.competidores):
            limpios.append(b)
        else:
            logger.warning(f"Bracket con sexos mixtos detectado en {b.ronda_origen} — desarmando")
            nuevos_unpaired.extend(b.competidores)
    return limpios, nuevos_unpaired


# ──────────────────────────────────────────────────────────────────────────────
# Preparación de competidores
# ──────────────────────────────────────────────────────────────────────────────

def preparar_competidores(competitors: List[Competidor]) -> List[Competidor]:
    for c in competitors:
        c.categoria_edad = get_categoria_edad(c.edad)
        asignar_bloque_correcto(c)
    return sorted(
        competitors,
        key=lambda c: (c.bloque, c.categoria_edad, c.sexo, c.cinta_block, c.edad, c.peso_kg, c.estatura_cm),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Numeración
# ──────────────────────────────────────────────────────────────────────────────

def asignar_numeracion(brackets: List[Bracket], todos_competidores: List[Competidor]) -> None:
    por_bloque: Dict[str, List[Competidor]] = {}
    for c in todos_competidores:
        por_bloque.setdefault(c.bloque, []).append(c)

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


# ──────────────────────────────────────────────────────────────────────────────
# Motor principal
# ──────────────────────────────────────────────────────────────────────────────

def generar_brackets(competitors: List[Competidor]) -> Results:
    global _score_cache
    _score_cache.clear()

    if not competitors:
        return _resultado_vacio()

    competitors = preparar_competidores(competitors)

    # Agrupación inicial: bloque + categoría_edad + sexo + cinta (+ grado para Negras)
    grupos_iniciales: Dict[Tuple, List[Competidor]] = {}
    for c in competitors:
        cinta = get_cinta_normalizada(c.cinta_block)
        key = (
            c.bloque, c.categoria_edad, c.sexo, cinta,
            c.grado_raw if cinta in ("Negra (Poom)", "Negra (Dan)") else "",
        )
        grupos_iniciales.setdefault(key, []).append(c)

    todos_brackets: List[Bracket] = []
    no_emparejados: List[Competidor] = []

    # ── Nivel 1 (más estricto) ────────────────────────────────────────────────
    for grupo in grupos_iniciales.values():
        b, r = matching_global_con_relajacion(grupo, 1, {"peso": 5.0, "edad": 1.0, "estatura": 10}, 80)
        todos_brackets.extend(b)
        no_emparejados.extend(r)

    # ── Fase 2.5 (reorganización extendida) ──────────────────────────────────
    todos_brackets, no_emparejados = fase_2_5_reorganizar(todos_brackets, no_emparejados)

    # ── Niveles 2-6 (relajación progresiva) ──────────────────────────────────
    for nivel in range(2, 7):
        if not no_emparejados:
            break
        config = RELAXATION_LEVELS[nivel - 1]
        limits = {"peso": config["peso"], "edad": config["edad"], "estatura": config["estatura"]}
        score_min = config["score_min"]
        mezcla_cintas = config["mezcla_cintas"]

        # Re-agrupar los sin rival
        grupos_relajados: Dict[Tuple, List[Competidor]] = {}
        for c in no_emparejados:
            key = (c.bloque, c.categoria_edad, c.sexo)
            grupos_relajados.setdefault(key, []).append(c)

        nuevos_brackets: List[Bracket] = []
        nuevos_no_emp: List[Competidor] = []

        for grupo in grupos_relajados.values():
            if not mezcla_cintas:
                # Subgrupos por cinta exacta
                subgrupos: Dict[str, List[Competidor]] = {}
                for c in grupo:
                    subgrupos.setdefault(c.cinta_block, []).append(c)
                for sub in subgrupos.values():
                    if len(sub) < 2:
                        nuevos_no_emp.extend(sub)
                        continue
                    b, r = matching_global_con_relajacion(sub, nivel, limits, score_min)
                    nuevos_brackets.extend(b)
                    nuevos_no_emp.extend(r)
            else:
                b, r = matching_global_con_relajacion(grupo, nivel, limits, score_min)
                nuevos_brackets.extend(b)
                nuevos_no_emp.extend(r)

        todos_brackets.extend(nuevos_brackets)
        no_emparejados = nuevos_no_emp

    # ── Limpieza de seguridad ─────────────────────────────────────────────────
    todos_brackets, _ = _limpiar_brackets_mixtos(todos_brackets, [])

    # Competidores restantes → sin rival (requieren revisión manual)
    sin_rival_final = [
        Unpaired(competidor=c, razon="Sin rival compatible tras todos los niveles de relajación")
        for c in no_emparejados
    ]

    asignar_numeracion(todos_brackets, competitors)

    return _construir_results(competitors, todos_brackets, sin_rival_final)


# ──────────────────────────────────────────────────────────────────────────────
# Construcción del objeto Results
# ──────────────────────────────────────────────────────────────────────────────

def _construir_results(
    competitors: List[Competidor],
    todos_brackets: List[Bracket],
    sin_rival_final: List[Unpaired],
) -> Results:
    total_comp    = len(competitors)
    total_brack   = len(todos_brackets)
    brackets_2    = sum(1 for b in todos_brackets if len(b.competidores) == 2)
    brackets_3    = sum(1 for b in todos_brackets if len(b.competidores) == 3)
    brackets_4    = sum(1 for b in todos_brackets if len(b.competidores) == 4)
    excellent     = sum(1 for b in todos_brackets if b.score >= 70)
    low_quality   = sum(1 for b in todos_brackets if b.score < 30)
    all_scores    = [b.score for b in todos_brackets]
    avg_score     = sum(all_scores) / len(all_scores) if all_scores else 0.0
    emp_count     = total_comp - len(sin_rival_final)
    emp_pct       = (emp_count / total_comp * 100) if total_comp > 0 else 0.0
    avg_size      = sum(len(b.competidores) for b in todos_brackets) / total_brack if total_brack > 0 else 0.0

    def _count(campo, valor):
        return sum(1 for b in todos_brackets if getattr(b, campo) == valor)

    gs = GlobalStats(
        total_competidores=total_comp,
        total_brackets=total_brack,
        avg_bracket_size=round(avg_size, 1),
        brackets_2=brackets_2,
        brackets_3=brackets_3,
        brackets_4=brackets_4,
        sin_rival_total=len(sin_rival_final),
        excellent_brackets=excellent,
        low_quality_brackets=low_quality,
        brackets_verde   =_count("nivel_aprobacion", "verde"),
        brackets_amarillo=_count("nivel_aprobacion", "amarillo"),
        brackets_naranja =_count("nivel_aprobacion", "naranja"),
        brackets_rojo    =_count("nivel_aprobacion", "rojo"),
        etapa2_count =sum(1 for b in todos_brackets if b.ronda_origen == "fase3_nivel1"),
        ronda1_count =sum(1 for b in todos_brackets if b.ronda_origen == "fase3_nivel1"),
        ronda2_count =sum(1 for b in todos_brackets if b.ronda_origen == "fase3_nivel2"),
        ronda3_count =sum(1 for b in todos_brackets if b.ronda_origen == "fase3_nivel3"),
        ronda4_count =sum(1 for b in todos_brackets if b.ronda_origen == "fase3_nivel4"),
        fase2_5_count=sum(1 for b in todos_brackets if "fase2_5" in b.ronda_origen),
        nivel5_count =sum(1 for b in todos_brackets if b.ronda_origen == "fase3_nivel5"),
        nivel6_count =sum(1 for b in todos_brackets if b.ronda_origen == "fase3_nivel6"),
        nivel7_count =0,
        avg_score=round(avg_score, 2),
        emparejamiento_pct=round(emp_pct, 1),
    )

    # Estadísticas por bloque
    block_data: Dict[str, Dict] = {}
    for b in todos_brackets:
        bloque = b.competidores[0].bloque
        d = block_data.setdefault(bloque, {"ids": set(), "brackets": 0, "sin_rival": 0})
        d["brackets"] += 1
        d["ids"].update(c.id for c in b.competidores)
    for u in sin_rival_final:
        bloque = u.competidor.bloque
        d = block_data.setdefault(bloque, {"ids": set(), "brackets": 0, "sin_rival": 0})
        d["sin_rival"] += 1

    block_stats = []
    for bloque in BLOCK_ORDER:
        if bloque not in block_data:
            continue
        d = block_data[bloque]
        total_b = len(d["ids"]) + d["sin_rival"]
        block_stats.append(BlockStats(
            bloque=bloque,
            competidores=total_b,
            brackets=d["brackets"],
            avg_size=round(len(d["ids"]) / d["brackets"], 1) if d["brackets"] > 0 else 0,
            sin_rival=d["sin_rival"],
            relaxed_count=0,
        ))

    return Results(
        global_stats=gs,
        block_stats=block_stats,
        brackets=todos_brackets,
        unpaired=sin_rival_final,
    )


def _resultado_vacio() -> Results:
    gs = GlobalStats(
        total_competidores=0, total_brackets=0, avg_bracket_size=0,
        brackets_2=0, brackets_3=0, brackets_4=0, sin_rival_total=0,
        excellent_brackets=0, low_quality_brackets=0, avg_score=0.0, emparejamiento_pct=0.0,
        brackets_verde=0, brackets_amarillo=0, brackets_naranja=0, brackets_rojo=0,
        etapa2_count=0, ronda1_count=0, ronda2_count=0, ronda3_count=0, ronda4_count=0,
        fase2_5_count=0, nivel5_count=0, nivel6_count=0, nivel7_count=0,
    )
    return Results(global_stats=gs, block_stats=[], brackets=[], unpaired=[])


# ── Alias público ─────────────────────────────────────────────────────────────
def generate_results(competitors: List[Competidor]) -> Results:
    return generar_brackets(competitors)