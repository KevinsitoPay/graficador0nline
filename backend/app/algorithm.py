"""
pairing_engine.py – Algoritmo de emparejamiento para torneos de Taekwondo
================================================================================
Versión v4 – Cintas estrictas por bloque, mezcla solo por humano.

REGLA CENTRAL (v4):
  Cada competidor compite SOLO con su misma cinta dentro de su bloque.
  El algoritmo NUNCA mezcla cintas distintas, excepto la única excepción
  reglamentaria: en Adultos Grupo 1, Marrón+Roja y Roja+Negra (diff 1 nivel)
  son automáticamente válidas. Cualquier otra mezcla queda como "sin rival"
  y es responsabilidad del humano decidir si arrastrar manualmente.

ESTRUCTURA DE BLOQUES (v4):
  - Adultos Grupo 1:      Marrón, Roja, Negra Dan/Poom  (mezcla diff≤1 OK)
  - Adultos Grupo 2:      Blanca, Amarilla, Verde, Azul  (solo misma cinta)
  - Infantil Avanzados:   Marrón + Roja + Negra juntos   (solo misma cinta)
  - Infantil Básicos:     Blanca / Amarilla / Verde / Azul (un bloque por cinta)
  - Pre-Taekwondo:        Blanca a Azul                  (solo misma cinta)

AGRUPACIÓN INICIAL (v4):
  La clave de grupo incluye SIEMPRE la cinta exacta. Los niveles de relajación
  solo aflojan peso/edad/estatura — nunca la cinta. El campo `mezcla_cintas`
  de RELAX_LEVELS ya no tiene efecto; `cintas_permitidas` es la única fuente
  de verdad para qué cintas pueden competir juntas.

  (Se conservan FIX-G1 a G5 y FIX-R1/R2 de versiones anteriores.)
================================================================================
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

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTES GLOBALES
# =============================================================================

BLOCK_ORDER = [
    "Adultos Grupo 1", "Adultos Grupo 2",
    "Infantil Avanzados",
    "Infantil Azul", "Infantil Verde", "Infantil Amarilla", "Infantil Blanca",
    "Pre-Taekwondo",
]

BLOCK_PREFIXES = {
    "Adultos Grupo 1":   "AD1",
    "Adultos Grupo 2":   "AD2",
    "Infantil Avanzados":"IAV",
    "Infantil Azul":     "AZ",
    "Infantil Verde":    "VD",
    "Infantil Amarilla": "AM",
    "Infantil Blanca":   "BC",
    "Pre-Taekwondo":     "PT",
}

# Cintas que pertenecen al bloque Infantil Avanzados
CINTAS_INFANTIL_AVANZADO = {"Marrón", "Roja", "Negra (Poom)", "Negra (Dan)"}

# Cintas de Adultos Grupo 1
CINTAS_ADULTO_G1 = {"Marrón", "Roja", "Negra (Poom)", "Negra (Dan)"}

# Cintas de Adultos Grupo 2
CINTAS_ADULTO_G2 = {"Blanca", "Amarilla", "Verde", "Azul", "Desconocido"}

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

CATEGORIAS_ADULTO = {"Cadete", "Juvenil", "Adulto", "Sub_Master", "Master"}

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

CINTA_ADYACENTE = {
    "Blanca": ["Amarilla"],
    "Amarilla": ["Blanca", "Verde"],
    "Verde": ["Amarilla", "Azul"],
    "Azul": ["Verde", "Marrón"],
    "Marrón": ["Azul", "Roja", "Negra"],
    "Roja": ["Marrón", "Negra"],
    "Negra": ["Roja", "Marrón"],
    "Negra (Poom)": ["Roja"],
    "Negra (Dan)": ["Roja"],
}

CINTA_A_BLOQUE_INFANTIL = {
    "Blanca":       "Infantil Blanca",
    "Amarilla":     "Infantil Amarilla",
    "Verde":        "Infantil Verde",
    "Azul":         "Infantil Azul",
    # Avanzados: Marrón + Roja + Negra comparten un solo bloque
    "Marrón":       "Infantil Avanzados",
    "Roja":         "Infantil Avanzados",
    "Negra (Poom)": "Infantil Avanzados",
    "Negra (Dan)":  "Infantil Avanzados",
    "Desconocido":  None,
}

MAX_PESO_ABS     = 7.5
MAX_ESTATURA_ABS = 14.0
MAX_EDAD_INFANTIL_ABS = 2.5
MAX_EDAD_ADULTO_ABS   = 6.0

# FIX-G4 – score_min diferenciado: grupos grandes requieren menos score para
# aprobarse, pares requieren más. Esto hace que el algoritmo prefiera grupos
# de 4/3 aunque sean menos "perfectos" que un par.
# IMPORTANTE: Mínimo 80% para emparejamiento válido
RELAX_LEVELS = [
    {"nivel": 1, "peso": 5.0, "edad_inf": 1.0, "edad_adulto": 1.0, "estatura": 10,
     "mezcla_cintas": False, "score_min_par": 80, "score_min_trio": 80, "score_min_cuarteto": 80, "mezcla_adultos": False},
    {"nivel": 2, "peso": 5.5, "edad_inf": 1.1, "edad_adulto": 1.1, "estatura": 11,
     "mezcla_cintas": False, "score_min_par": 80, "score_min_trio": 80, "score_min_cuarteto": 80, "mezcla_adultos": False},
    {"nivel": 3, "peso": 6.0, "edad_inf": 1.2, "edad_adulto": 1.2, "estatura": 12,
     "mezcla_cintas": False, "score_min_par": 75, "score_min_trio": 78, "score_min_cuarteto": 80, "mezcla_adultos": False},
    {"nivel": 4, "peso": 6.0, "edad_inf": 2.0, "edad_adulto": 2.0, "estatura": 12,
     "mezcla_cintas": True,  "score_min_par": 70, "score_min_trio": 75, "score_min_cuarteto": 78, "mezcla_adultos": False},
    {"nivel": 5, "peso": 6.5, "edad_inf": 2.0, "edad_adulto": 3.0, "estatura": 13,
     "mezcla_cintas": True,  "score_min_par": 65, "score_min_trio": 72, "score_min_cuarteto": 75, "mezcla_adultos": False},
    {"nivel": 6, "peso": 7.0, "edad_inf": 2.5, "edad_adulto": 4.0, "estatura": 14,
     "mezcla_cintas": True,  "score_min_par": 60, "score_min_trio": 68, "score_min_cuarteto": 72, "mezcla_adultos": False},
    {"nivel": 7, "peso": 7.5, "edad_inf": 2.5, "edad_adulto": 6.0, "estatura": 14,
     "mezcla_cintas": True,  "score_min_par": 50, "score_min_trio": 60, "score_min_cuarteto": 65, "mezcla_adultos": True},
]

# Acceso rápido a score_min para compatibilidad con código que usa "score_min" simple
def _get_score_min(config: Dict, tipo: str = "par") -> float:
    """Retorna score_min según tipo de grupo."""
    if tipo == "cuarteto":
        return config.get("score_min_cuarteto", config.get("score_min", 50))
    if tipo == "trio":
        return config.get("score_min_trio", config.get("score_min", 50))
    return config.get("score_min_par", config.get("score_min", 50))

_score_cache: Dict[Tuple, float] = {}


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def get_categoria_edad(edad: int) -> str:
    for cat, (lo, hi) in EDAD_CATEGORIAS.items():
        if lo <= edad <= hi:
            return cat
    return "Adulto"

def get_cinta_normalizada(cinta: str) -> str:
    return cinta

def es_bloque_adulto(bloque: str) -> bool:
    return bloque in ("Adultos Grupo 1", "Adultos Grupo 2")

def es_bloque_infantil_avanzado(bloque: str) -> bool:
    return bloque == "Infantil Avanzados"

def asignar_bloque_correcto(c: Competidor) -> None:
    if c.edad <= 5:
        c.bloque = "Pre-Taekwondo"
    elif c.edad >= 18:
        cinta = get_cinta_normalizada(c.cinta_block)
        if cinta in CINTAS_ADULTO_G1:
            c.bloque = "Adultos Grupo 1"
        else:
            c.bloque = "Adultos Grupo 2"
    elif c.edad >= 14:
        # Cadetes (14-15) y Juveniles (16-17) van a bloque adulto según cinta
        cinta = get_cinta_normalizada(c.cinta_block)
        if cinta in CINTAS_ADULTO_G1:
            bloque_nuevo = "Adultos Grupo 1"
        else:
            bloque_nuevo = "Adultos Grupo 2"
        if c.bloque != bloque_nuevo:
            logger.debug("FIX5: %s edad=%d reasignado de %s a %s",
                         c.nombre, c.edad, c.bloque, bloque_nuevo)
            c.bloque = bloque_nuevo
    else:
        # Infantil (6-13): asignar según cinta, respetando el nuevo bloque avanzado unificado
        bloque_correcto = CINTA_A_BLOQUE_INFANTIL.get(c.cinta_block)
        if bloque_correcto is not None and c.bloque != bloque_correcto:
            logger.debug("FIX4: %s reasignado de %s a %s por cinta %s",
                         c.nombre, c.bloque, bloque_correcto, c.cinta_block)
            c.bloque = bloque_correcto

def misma_categoria_edad(
    c1: Competidor,
    c2: Competidor,
    permitir_adyacente: bool = False,
    colapsar_adultos: bool = False,
) -> bool:
    if colapsar_adultos and es_bloque_adulto(c1.bloque) and es_bloque_adulto(c2.bloque):
        return True
    if c1.categoria_edad == c2.categoria_edad:
        return True
    if not permitir_adyacente:
        return False
    cat_order = list(EDAD_CATEGORIAS.keys())
    if c1.categoria_edad not in cat_order or c2.categoria_edad not in cat_order:
        return False
    idx1 = cat_order.index(c1.categoria_edad)
    idx2 = cat_order.index(c2.categoria_edad)
    return abs(idx1 - idx2) == 1

def mismo_sexo(c1: Competidor, c2: Competidor) -> bool:
    return c1.sexo == c2.sexo

def bloques_adultos_compatibles(c1: Competidor, c2: Competidor, permitir_mezcla: bool = False) -> bool:
    if permitir_mezcla:
        return True
    bloques = {"Adultos Grupo 1", "Adultos Grupo 2"}
    if c1.bloque in bloques and c2.bloque in bloques:
        return c1.bloque == c2.bloque
    return True

def cintas_permitidas(c1: Competidor, c2: Competidor, nivel: int) -> bool:
    """
    Regla de cintas v4 — ESTRICTA.

    El nivel de relajación (1-7) ya NO afloja restricciones de cinta.
    Los niveles solo relajan peso/edad/estatura.

    Reglas por bloque:
    - Misma cinta exacta:          siempre OK en cualquier bloque.
    - Adultos Grupo 1 (diff == 1): Marrón+Roja y Roja+Negra son OK automático.
                                   Marrón+Negra (diff 2) → BLOQUEADO.
    - Todo lo demás:               BLOQUEADO — el algoritmo NO mezcla cintas.
                                   La mezcla es responsabilidad del humano.
    """
    c1b = c1.cinta_block
    c2b = c2.cinta_block

    # Misma cinta exacta — siempre permitido
    if c1b == c2b:
        return True

    # "Desconocido" solo puede competir con otra "Desconocido"
    if c1b == "Desconocido" or c2b == "Desconocido":
        return False

    # Única excepción reglamentaria: Adultos Grupo 1, diferencia de nivel == 1
    # Marrón(5)+Roja(6) = diff 1 → OK
    # Roja(6)+Negra(7/8) = diff 1/2 → Roja+NegraPoom(7)=1 OK, Roja+NegraDan(8)=2 bloqueado
    # Marrón(5)+Negra(7/8) = diff 2/3 → BLOQUEADO
    ambos_adulto_g1 = (c1.bloque == "Adultos Grupo 1" and c2.bloque == "Adultos Grupo 1")
    if ambos_adulto_g1:
        n1 = CINTA_NIVEL.get(c1b, 0)
        n2 = CINTA_NIVEL.get(c2b, 0)
        return abs(n1 - n2) == 1  # solo diff exactamente 1

    # Cualquier otra combinación de cintas distintas → BLOQUEADO
    return False

def limites_fisicos_ok(c1: Competidor, c2: Competidor, limits: Dict, nivel: int) -> Tuple[bool, str]:
    dp = abs(c1.peso_kg - c2.peso_kg)
    de = abs(c1.edad - c2.edad)

    # FIX-R1: Si cualquiera tiene estatura 0 (dato faltante), omitir validación
    # de estatura por completo — no penalizar datos ausentes como diferencia real.
    estatura_valida = c1.estatura_cm > 0 and c2.estatura_cm > 0
    ds = abs(c1.estatura_cm - c2.estatura_cm) if estatura_valida else 0.0

    # FIX-R2: Límite de peso absoluto relativo al peso base del competidor más ligero.
    # Un 12% de diferencia es razonable a cualquier peso; el piso es 7.5 kg
    # para no aflojar demasiado en categorías infantiles ligeras.
    peso_base = min(c1.peso_kg, c2.peso_kg)
    max_peso_abs_efectivo = max(MAX_PESO_ABS, peso_base * 0.12)

    if dp > max_peso_abs_efectivo:
        return False, f"peso_abs: {dp:.1f}>{max_peso_abs_efectivo:.1f}"
    if estatura_valida and ds > MAX_ESTATURA_ABS:
        return False, f"est_abs: {ds}>{MAX_ESTATURA_ABS}"

    if es_bloque_adulto(c1.bloque) and es_bloque_adulto(c2.bloque):
        max_edad_abs = MAX_EDAD_ADULTO_ABS
    else:
        cat = c1.categoria_edad
        max_edad_abs = MAX_EDAD_ADULTO_ABS if cat in ("Sub_Master", "Master") else MAX_EDAD_INFANTIL_ABS

    if de > max_edad_abs:
        return False, f"edad_abs: {de}>{max_edad_abs}"

    if dp > limits["peso"]:
        return False, f"peso_nivel: {dp:.1f}>{limits['peso']}"
    if estatura_valida and ds > limits["estatura"]:
        return False, f"est_nivel: {ds}>{limits['estatura']}"
    edad_limite = limits["edad"]
    if de > edad_limite:
        return False, f"edad_nivel: {de}>{edad_limite}"
    return True, ""

def modalidad_par_ok(c1: Competidor, c2: Competidor) -> bool:
    return c1.modalidad == c2.modalidad

def modalidad_grupo_ok(competidores: List[Competidor]) -> bool:
    n = len(competidores)
    if n < 2:
        return True
    if n == 2:
        return modalidad_par_ok(competidores[0], competidores[1])
    dobles = sum(1 for c in competidores if c.modalidad == "Doble")
    return dobles != 1

def puede_emparejarse(
    c1: Competidor,
    c2: Competidor,
    limits: Dict,
    nivel: int,
    permitir_mezcla_adultos: bool = False,
    permitir_categoria_adyacente: bool = False,
    colapsar_adultos: bool = False,
) -> Tuple[bool, str]:
    if not mismo_sexo(c1, c2):
        return False, "sexo_diferente"
    if not misma_categoria_edad(c1, c2, permitir_categoria_adyacente, colapsar_adultos):
        return False, f"edad_cat: {c1.categoria_edad} != {c2.categoria_edad}"
    if not bloques_adultos_compatibles(c1, c2, permitir_mezcla_adultos):
        return False, "adultos_grupo_mix"
    if not cintas_permitidas(c1, c2, nivel):
        return False, f"cintas: {c1.cinta_block}/{c2.cinta_block}"
    ok, motivo = limites_fisicos_ok(c1, c2, limits, nivel)
    if not ok:
        return False, motivo
    if not modalidad_par_ok(c1, c2):
        return False, f"modalidad: {c1.modalidad}!={c2.modalidad}"
    return True, ""

def puede_grupo(
    competidores: List[Competidor],
    limits: Dict,
    nivel: int,
    permitir_mezcla_adultos: bool = False,
    permitir_categoria_adyacente: bool = False,
    colapsar_adultos: bool = False,
) -> Tuple[bool, str]:
    if not modalidad_grupo_ok(competidores):
        return False, "modalidad_grupo_invalida"
    for i in range(len(competidores)):
        for j in range(i + 1, len(competidores)):
            ok, motivo = puede_emparejarse(
                competidores[i], competidores[j], limits, nivel,
                permitir_mezcla_adultos, permitir_categoria_adyacente, colapsar_adultos,
            )
            if not ok:
                return False, f"par {i}-{j}: {motivo}"
    return True, ""

def score(c1: Competidor, c2: Competidor, limits: Dict, nivel: int) -> float:
    ok, _ = puede_emparejarse(c1, c2, limits, nivel)
    if not ok:
        return 0.0
    dp = abs(c1.peso_kg - c2.peso_kg)
    de = abs(c1.edad - c2.edad)
    estatura_valida = c1.estatura_cm > 0 and c2.estatura_cm > 0
    ds = abs(c1.estatura_cm - c2.estatura_cm) if estatura_valida else 0.0
    peso_max = limits["peso"]
    edad_max = limits["edad"]
    est_max  = limits["estatura"]
    pen_peso  = 40 * (dp / peso_max) ** 1.8 if peso_max > 0 else 0
    pen_edad  = 30 * (de / edad_max) ** 1.8 if edad_max > 0 else 0
    pen_est   = 20 * (ds / est_max)  ** 1.8 if (est_max > 0 and estatura_valida) else 0
    pen_doyang = 10 if c1.doyang == c2.doyang else 0
    n1 = CINTA_NIVEL.get(c1.cinta_block, 0)
    n2 = CINTA_NIVEL.get(c2.cinta_block, 0)
    pen_cinta = 3 * abs(n1 - n2)
    total = 100 - (pen_peso + pen_edad + pen_est + pen_doyang + pen_cinta)
    return max(0.0, min(100.0, total))

def calcular_bracket_score(
    competidores: List[Competidor],
    limits: Dict,
    nivel: int,
    permitir_mezcla_adultos: bool = False,
    permitir_categoria_adyacente: bool = False,
) -> Tuple[float, Dict, List[str]]:
    if len(competidores) < 2:
        empty = {k: 0 for k in ("modalidad_ok", "edad_diff", "edad_score", "peso_diff", "peso_score", "estatura_diff", "estatura_score", "doyang_penalty", "cinta_penalty", "total")}
        empty["modalidad_ok"] = True
        return 0.0, empty, []
    if not modalidad_grupo_ok(competidores):
        bd = {k: 0 for k in ("modalidad_ok", "edad_diff", "edad_score", "peso_diff", "peso_score", "estatura_diff", "estatura_score", "doyang_penalty", "cinta_penalty", "total")}
        bd["modalidad_ok"] = False
        return 0.0, bd, ["modalidad_invalida"]
    scores = []
    breakdowns = []
    for i in range(len(competidores)):
        for j in range(i + 1, len(competidores)):
            s = score(competidores[i], competidores[j], limits, nivel)
            scores.append(s)
            breakdowns.append({
                "edad_diff":     abs(competidores[i].edad      - competidores[j].edad),
                "peso_diff":     abs(competidores[i].peso_kg   - competidores[j].peso_kg),
                "estatura_diff": abs(competidores[i].estatura_cm - competidores[j].estatura_cm),
            })
    avg_score = sum(scores) / len(scores)
    if len(competidores) == 4:
        dobles = sum(1 for c in competidores if c.modalidad == "Doble")
        if dobles == 2:
            avg_score = min(100.0, avg_score + 5.0)
    bd = {
        "modalidad_ok":   True,
        "edad_diff":      int(sum(b["edad_diff"] for b in breakdowns) / len(breakdowns)),
        "edad_score":     round(100 - 30 * (sum(b["edad_diff"] for b in breakdowns) / len(breakdowns) / limits["edad"]) ** 1.8, 2),
        "peso_diff":      round(sum(b["peso_diff"] for b in breakdowns) / len(breakdowns), 2),
        "peso_score":     round(100 - 40 * (sum(b["peso_diff"] for b in breakdowns) / len(breakdowns) / limits["peso"]) ** 1.8, 2),
        "estatura_diff":  int(sum(b["estatura_diff"] for b in breakdowns) / len(breakdowns)),
        "estatura_score": round(100 - 20 * (sum(b["estatura_diff"] for b in breakdowns) / len(breakdowns) / limits["estatura"]) ** 1.8, 2),
        "doyang_penalty": 0,
        "cinta_penalty":  0,
        "total":          round(avg_score, 2),
    }
    return avg_score, bd, []


# =============================================================================
# MATCHING HÚNGARO – FIX-G1
# =============================================================================

def matching_hungaro(
    competitors: List[Competidor],
    limits: Dict,
    score_min: float,
    nivel: int,
    permitir_mezcla_adultos: bool = False,
    permitir_categoria_adyacente: bool = False,
    colapsar_adultos: bool = False,
    solo_grupos_grandes: bool = False,   # FIX-G1
) -> List[Tuple[int, int]]:
    # FIX-G1: si solo_grupos_grandes=True, no formar pares ahora.
    # Los competidores restantes pasarán al siguiente nivel de relajación
    # donde pueden encontrar compañeros para grupos de 3 o 4.
    if solo_grupos_grandes:
        return []

    n = len(competitors)
    if n < 2:
        return []
    cost = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            s = score(competitors[i], competitors[j], limits, nivel)
            if s >= score_min:
                cost[i][j] = s
                cost[j][i] = s
    if cost.max() == 0:
        return []
    row, col = linear_sum_assignment(-cost)
    used = set()
    result = []
    for i, j in zip(row, col):
        if i < j and i not in used and j not in used and cost[i][j] >= score_min:
            result.append((i, j))
            used.add(i)
            used.add(j)
    return result


# =============================================================================
# FIX-G5 – Segunda pasada de cuartetos con ventana global
# =============================================================================

def _segunda_pasada_cuartetos(
    competitors: List[Competidor],
    limits: Dict,
    nivel: int,
    score_min: float,
    permitir_mezcla_adultos: bool = False,
    colapsar_adultos: bool = False,
) -> Tuple[List[Bracket], List[Competidor]]:
    """
    Busca cuartetos en el conjunto completo de competidores restantes,
    sin ventana limitada, para maximizar grupos de 4 antes de pasar a tríos.
    """
    disponibles = sorted(competitors, key=lambda c: c.peso_kg)
    n = len(disponibles)
    used: Set[int] = set()
    brackets = []

    for i in range(n - 3):
        if i in used:
            continue
        c1 = disponibles[i]
        mejor = None
        for j in range(i + 1, n - 2):
            if j in used:
                continue
            c2 = disponibles[j]
            ok_ij, _ = puede_emparejarse(c1, c2, limits, nivel, permitir_mezcla_adultos, False, colapsar_adultos)
            if not ok_ij:
                continue
            for k in range(j + 1, n - 1):
                if k in used:
                    continue
                c3 = disponibles[k]
                ok_ik, _ = puede_emparejarse(c1, c3, limits, nivel, permitir_mezcla_adultos, False, colapsar_adultos)
                ok_jk, _ = puede_emparejarse(c2, c3, limits, nivel, permitir_mezcla_adultos, False, colapsar_adultos)
                if not (ok_ik and ok_jk):
                    continue
                for l in range(k + 1, n):
                    if l in used:
                        continue
                    c4 = disponibles[l]
                    cuarteto = [c1, c2, c3, c4]
                    ok, _ = puede_grupo(cuarteto, limits, nivel, permitir_mezcla_adultos, False, colapsar_adultos)
                    if not ok:
                        continue
                    s = sum(score(a, b, limits, nivel) for a in cuarteto for b in cuarteto if a.id < b.id) / 6
                    if s >= score_min:
                        if mejor is None or s > mejor[0]:
                            mejor = (s, [i, j, k, l], cuarteto)
        if mejor:
            s, indices, cuarteto = mejor
            avg, bd, _ = calcular_bracket_score(cuarteto, limits, nivel, permitir_mezcla_adultos)
            color = "verde" if nivel <= 2 else "amarillo" if nivel == 3 else "naranja" if nivel == 4 else "rojo"
            brackets.append(Bracket(
                id=0, numero=0, area=0,
                competidores=cuarteto,
                tipo=f"nivel{nivel}",
                score=round(avg, 2),
                score_breakdown=ScoreBreakdown(**bd),
                nivel_aprobacion=color,
                requiere_aprobacion=nivel >= 3,
                aprobador_requerido="coordinadora" if nivel >= 5 else ("colaborador" if nivel >= 3 else None),
                ronda_origen=f"segunda_pasada_cuarteto_{nivel}",
                failure_reasons=[],
            ))
            for idx in indices:
                used.add(idx)

    restantes = [c for idx, c in enumerate(disponibles) if idx not in used]
    return brackets, restantes


# =============================================================================
# FORMACIÓN DE GRUPOS
# =============================================================================

def formar_grupos(
    competitors: List[Competidor],
    limits: Dict,
    score_min_cuarteto: float,
    score_min_trio: float,
    nivel: int,
    permitir_mezcla_adultos: bool = False,
    permitir_categoria_adyacente: bool = False,
    colapsar_adultos: bool = False,
) -> Tuple[List[Bracket], List[Competidor]]:
    """
    Prioridad: 4 competidores > 3 competidores > 2 competidores
    Mínimo 80% de score para emparejamiento válido
    """
    disponibles = sorted(competitors, key=lambda c: c.peso_kg)
    used = set()
    brackets = []
    window = min(25, len(disponibles))

    # PRIORIDAD 1: Cuartetos (buscar primero, más importante)
    i = 0
    while i < len(disponibles) - 3:
        c1 = disponibles[i]
        mejor = None
        for j in range(i + 1, min(i + window, len(disponibles) - 2)):
            c2 = disponibles[j]
            for k in range(j + 1, min(j + window, len(disponibles) - 1)):
                c3 = disponibles[k]
                for l in range(k + 1, min(k + window, len(disponibles))):
                    c4 = disponibles[l]
                    grupo = [c1, c2, c3, c4]
                    if any(c.id in used for c in grupo):
                        continue
                    ok, _ = puede_grupo(grupo, limits, nivel, permitir_mezcla_adultos, permitir_categoria_adyacente, colapsar_adultos)
                    if not ok:
                        continue
                    s = sum(score(a, b, limits, nivel) for a in grupo for b in grupo if a.id < b.id) / 6
                    # IMPORTANTE: Mínimo 80% para emparejamiento válido
                    if s >= max(score_min_cuarteto, 80):
                        if mejor is None or s > mejor[0]:
                            mejor = (s, grupo)
        if mejor:
            s, grupo = mejor
            avg, bd, _ = calcular_bracket_score(grupo, limits, nivel, permitir_mezcla_adultos, permitir_categoria_adyacente)
            color = "verde" if nivel <= 2 else "amarillo" if nivel == 3 else "naranja" if nivel == 4 else "rojo"
            brackets.append(Bracket(
                id=0, numero=0, area=0,
                competidores=grupo,
                tipo=f"nivel{nivel}",
                score=round(avg, 2),
                score_breakdown=ScoreBreakdown(**bd),
                nivel_aprobacion=color,
                requiere_aprobacion=nivel >= 3,
                aprobador_requerido="coordinadora" if nivel >= 5 else ("colaborador" if nivel >= 3 else None),
                ronda_origen=f"grupo_{nivel}",
                failure_reasons=[],
            ))
            for c in grupo:
                used.add(c.id)
            disponibles = [c for c in disponibles if c.id not in used]
            i = 0
            continue
        i += 1

    # PRIORIDAD 2: Tríos (después de cuartetos)
    i = 0
    while i < len(disponibles) - 2:
        c1 = disponibles[i]
        mejor = None
        for j in range(i + 1, min(i + window, len(disponibles) - 1)):
            c2 = disponibles[j]
            for k in range(j + 1, min(j + window, len(disponibles))):
                c3 = disponibles[k]
                grupo = [c1, c2, c3]
                if any(c.id in used for c in grupo):
                    continue
                ok, _ = puede_grupo(grupo, limits, nivel, permitir_mezcla_adultos, permitir_categoria_adyacente, colapsar_adultos)
                if not ok:
                    continue
                s = sum(score(a, b, limits, nivel) for a in grupo for b in grupo if a.id < b.id) / 3
                # IMPORTANTE: Mínimo 80% para emparejamiento válido
                if s >= max(score_min_trio, 80):
                    if mejor is None or s > mejor[0]:
                        mejor = (s, grupo)
        if mejor:
            s, grupo = mejor
            avg, bd, _ = calcular_bracket_score(grupo, limits, nivel, permitir_mezcla_adultos, permitir_categoria_adyacente)
            color = "verde" if nivel <= 2 else "amarillo" if nivel == 3 else "naranja" if nivel == 4 else "rojo"
            brackets.append(Bracket(
                id=0, numero=0, area=0,
                competidores=grupo,
                tipo=f"nivel{nivel}",
                score=round(avg, 2),
                score_breakdown=ScoreBreakdown(**bd),
                nivel_aprobacion=color,
                requiere_aprobacion=nivel >= 3,
                aprobador_requerido="coordinadora" if nivel >= 5 else ("colaborador" if nivel >= 3 else None),
                ronda_origen=f"grupo_{nivel}",
                failure_reasons=[],
            ))
            for c in grupo:
                used.add(c.id)
            disponibles = [c for c in disponibles if c.id not in used]
            i = 0
            continue
        i += 1

    restantes = [c for c in competitors if c.id not in used]
    return brackets, restantes


# =============================================================================
# PROCESAMIENTO POR NIVEL – FIX-G2
# =============================================================================

def procesar_nivel(
    competitors: List[Competidor],
    nivel: int,
    colapsar_adultos: bool = False,
) -> Tuple[List[Bracket], List[Competidor]]:
    config = RELAX_LEVELS[nivel - 1]

    primer = competitors[0]
    if es_bloque_adulto(primer.bloque) or colapsar_adultos:
        edad_limite = config["edad_adulto"]
    else:
        edad_limite = config["edad_inf"] if primer.categoria_edad not in ("Sub_Master", "Master") else config["edad_adulto"]

    limits = {
        "peso":     config["peso"],
        "edad":     edad_limite,
        "estatura": config["estatura"],
    }

    score_min_cuarteto = _get_score_min(config, "cuarteto")
    score_min_trio     = _get_score_min(config, "trio")
    score_min_par      = _get_score_min(config, "par")

    permitir_mezcla_adultos = config.get("mezcla_adultos", False)

    brackets, restantes = formar_grupos(
        competitors, limits,
        score_min_cuarteto, score_min_trio,
        nivel,
        permitir_mezcla_adultos,
        colapsar_adultos=colapsar_adultos,
    )

    # FIX-G5: segunda pasada de cuartetos con ventana global sobre los restantes
    if len(restantes) >= 4:
        b2, restantes = _segunda_pasada_cuartetos(
            restantes, limits, nivel, score_min_cuarteto,
            permitir_mezcla_adultos, colapsar_adultos,
        )
        brackets.extend(b2)

    # FIX-G2: solo crear pares a partir del nivel 6
    # En niveles 1–5 los restantes pasan al siguiente nivel de relajación
    solo_grupos_grandes = (nivel <= 5)

    if len(restantes) >= 2:
        pares = matching_hungaro(
            restantes, limits, score_min_par, nivel,
            permitir_mezcla_adultos,
            colapsar_adultos=colapsar_adultos,
            solo_grupos_grandes=solo_grupos_grandes,  # FIX-G2
        )
        used = set()
        for i, j in pares:
            c1, c2 = restantes[i], restantes[j]
            avg, bd, _ = calcular_bracket_score([c1, c2], limits, nivel, permitir_mezcla_adultos)
            color = "verde" if nivel <= 2 else "amarillo" if nivel == 3 else "naranja" if nivel == 4 else "rojo"
            brackets.append(Bracket(
                id=0, numero=0, area=0,
                competidores=[c1, c2],
                tipo=f"nivel{nivel}",
                score=round(avg, 2),
                score_breakdown=ScoreBreakdown(**bd),
                nivel_aprobacion=color,
                requiere_aprobacion=nivel >= 3,
                aprobador_requerido="coordinadora" if nivel >= 5 else ("colaborador" if nivel >= 3 else None),
                ronda_origen=f"par_{nivel}",
                failure_reasons=[],
            ))
            used.add(i)
            used.add(j)
        restantes = [c for idx, c in enumerate(restantes) if idx not in used]

    return brackets, restantes


# =============================================================================
# FASE 2.5: REORGANIZACIÓN LOCAL
# =============================================================================

def fase_2_5_reorganizar(brackets: List[Bracket], unpaired: List[Competidor]) -> Tuple[List[Bracket], List[Competidor]]:
    limits = {"peso": 5.0, "edad": 1.0, "estatura": 10}
    nivel = 1
    new_brackets = []
    new_unpaired = list(unpaired)

    for u in new_unpaired[:]:
        mejor = None
        for b in brackets[:]:
            if len(b.competidores) != 4:
                continue
            comps = b.competidores
            for i in range(4):
                for j in range(i + 1, 4):
                    if not mismo_sexo(comps[i], u) or not mismo_sexo(comps[j], u):
                        continue
                    trio = [comps[i], comps[j], u]
                    resto = [comps[k] for k in range(4) if k not in (i, j)]
                    ok_trio, _ = puede_grupo(trio, limits, nivel)
                    ok_resto, _ = puede_grupo(resto, limits, nivel)
                    if not (ok_trio and ok_resto):
                        continue
                    s_trio  = sum(score(a, b, limits, nivel) for a in trio  for b in trio  if a.id < b.id) / 3
                    s_resto = score(resto[0], resto[1], limits, nivel)
                    if s_trio >= 50 and s_resto >= 50:
                        if mejor is None or min(s_trio, s_resto) > mejor[0]:
                            mejor = (min(s_trio, s_resto), b, trio, resto)
            if mejor:
                _, b_old, trio, resto = mejor
                brackets.remove(b_old)
                for grupo, origen in [(trio, "fase2_5_trio"), (resto, "fase2_5_par")]:
                    avg, bd, _ = calcular_bracket_score(grupo, limits, nivel)
                    new_brackets.append(Bracket(
                        id=0, numero=0, area=0,
                        competidores=grupo,
                        tipo="normal",
                        score=round(avg, 2),
                        score_breakdown=ScoreBreakdown(**bd),
                        nivel_aprobacion="amarillo",
                        requiere_aprobacion=True,
                        aprobador_requerido="coordinadora",
                        ronda_origen=origen,
                        failure_reasons=[],
                    ))
                new_unpaired.remove(u)
                break

    new_brackets.extend(brackets)

    for u in new_unpaired[:]:
        mejor = None
        for b in new_brackets[:]:
            if len(b.competidores) != 3:
                continue
            comps = b.competidores
            for i in range(3):
                cp = comps[i]
                if not mismo_sexo(cp, u):
                    continue
                par  = [cp, u]
                resto = [comps[k] for k in range(3) if k != i]
                ok_par,  _ = puede_grupo(par,  limits, nivel)
                ok_resto, _ = puede_grupo(resto, limits, nivel)
                if not (ok_par and ok_resto):
                    continue
                s_par   = score(par[0],  par[1],  limits, nivel)
                s_resto = score(resto[0], resto[1], limits, nivel)
                if s_par >= 50 and s_resto >= 50:
                    if mejor is None or min(s_par, s_resto) > mejor[0]:
                        mejor = (min(s_par, s_resto), b, par, resto)
            if mejor:
                _, b_old, par, resto = mejor
                new_brackets.remove(b_old)
                for grupo, origen in [(par, "fase2_5_par"), (resto, "fase2_5_par")]:
                    avg, bd, _ = calcular_bracket_score(grupo, limits, nivel)
                    new_brackets.append(Bracket(
                        id=0, numero=0, area=0,
                        competidores=grupo,
                        tipo="normal",
                        score=round(avg, 2),
                        score_breakdown=ScoreBreakdown(**bd),
                        nivel_aprobacion="amarillo",
                        requiere_aprobacion=True,
                        aprobador_requerido="coordinadora",
                        ronda_origen=origen,
                        failure_reasons=[],
                    ))
                new_unpaired.remove(u)
                break

    return new_brackets, new_unpaired


# =============================================================================
# FASE DE POST-PROCESAMIENTO
# =============================================================================

def fase_post_procesamiento_sin_rival(unpaired: List[Competidor]) -> Tuple[List[Bracket], List[Competidor]]:
    if len(unpaired) < 2:
        return [], unpaired

    limits      = {"peso": 7.0, "edad": 4.0, "estatura": 13.0}
    nivel       = 8
    permitir_mezcla_adultos = True
    score_min   = 20
    colapsar_adultos = True

    grupos = {}
    for c in unpaired:
        if es_bloque_adulto(c.bloque):
            key = (c.bloque, c.sexo)
        else:
            key = (c.categoria_edad, c.sexo)
        grupos.setdefault(key, []).append(c)

    nuevos_brackets = []
    restantes = []

    for key, grupo in grupos.items():
        grupo_ordenado = sorted(grupo, key=lambda x: x.peso_kg)
        window = min(15, len(grupo_ordenado))

        # Cuartetos
        i = 0
        while i < len(grupo_ordenado) - 3:
            c1 = grupo_ordenado[i]
            mejor = None
            for j in range(i + 1, min(i + window, len(grupo_ordenado) - 2)):
                c2 = grupo_ordenado[j]
                for k in range(j + 1, min(j + window, len(grupo_ordenado) - 1)):
                    c3 = grupo_ordenado[k]
                    for l in range(k + 1, min(k + window, len(grupo_ordenado))):
                        c4 = grupo_ordenado[l]
                        cuarteto = [c1, c2, c3, c4]
                        ok, _ = puede_grupo(cuarteto, limits, nivel, permitir_mezcla_adultos, colapsar_adultos=colapsar_adultos)
                        if not ok:
                            continue
                        s = sum(score(a, b, limits, nivel) for a in cuarteto for b in cuarteto if a.id < b.id) / 6
                        if s >= score_min:
                            if mejor is None or s > mejor[0]:
                                mejor = (s, cuarteto)
            if mejor:
                s, cuarteto = mejor
                avg, bd, _ = calcular_bracket_score(cuarteto, limits, nivel, permitir_mezcla_adultos)
                nuevos_brackets.append(Bracket(
                    id=0, numero=0, area=0,
                    competidores=cuarteto,
                    tipo="nivel8",
                    score=round(avg, 2),
                    score_breakdown=ScoreBreakdown(**bd),
                    nivel_aprobacion="rojo",
                    requiere_aprobacion=True,
                    aprobador_requerido="coordinadora",
                    ronda_origen="post_procesamiento_cuarteto",
                    failure_reasons=[],
                ))
                ids_usados = {c.id for c in cuarteto}
                grupo_ordenado = [c for c in grupo_ordenado if c.id not in ids_usados]
                i = 0
                continue
            i += 1

        # Tríos
        i = 0
        while i < len(grupo_ordenado) - 2:
            c1 = grupo_ordenado[i]
            mejor = None
            for j in range(i + 1, min(i + window, len(grupo_ordenado) - 1)):
                c2 = grupo_ordenado[j]
                for k in range(j + 1, min(k + window, len(grupo_ordenado))):
                    c3 = grupo_ordenado[k]
                    trio = [c1, c2, c3]
                    ok, _ = puede_grupo(trio, limits, nivel, permitir_mezcla_adultos, colapsar_adultos=colapsar_adultos)
                    if not ok:
                        continue
                    s = sum(score(a, b, limits, nivel) for a in trio for b in trio if a.id < b.id) / 3
                    if s >= score_min:
                        if mejor is None or s > mejor[0]:
                            mejor = (s, trio)
            if mejor:
                s, trio = mejor
                avg, bd, _ = calcular_bracket_score(trio, limits, nivel, permitir_mezcla_adultos)
                nuevos_brackets.append(Bracket(
                    id=0, numero=0, area=0,
                    competidores=trio,
                    tipo="nivel8",
                    score=round(avg, 2),
                    score_breakdown=ScoreBreakdown(**bd),
                    nivel_aprobacion="rojo",
                    requiere_aprobacion=True,
                    aprobador_requerido="coordinadora",
                    ronda_origen="post_procesamiento_trio",
                    failure_reasons=[],
                ))
                ids_usados = {c.id for c in trio}
                grupo_ordenado = [c for c in grupo_ordenado if c.id not in ids_usados]
                i = 0
                continue
            i += 1

        # Pares (ahora siempre permitidos en post-procesamiento)
        if len(grupo_ordenado) >= 2:
            limits_par = {"peso": 7.0, "edad": 5.0, "estatura": 13}
            pares = matching_hungaro(grupo_ordenado, limits_par, score_min, nivel, permitir_mezcla_adultos, colapsar_adultos=colapsar_adultos)
            used = set()
            for i, j in pares:
                c1, c2 = grupo_ordenado[i], grupo_ordenado[j]
                avg, bd, _ = calcular_bracket_score([c1, c2], limits_par, nivel, permitir_mezcla_adultos)
                nuevos_brackets.append(Bracket(
                    id=0, numero=0, area=0,
                    competidores=[c1, c2],
                    tipo="nivel8",
                    score=round(avg, 2),
                    score_breakdown=ScoreBreakdown(**bd),
                    nivel_aprobacion="rojo",
                    requiere_aprobacion=True,
                    aprobador_requerido="coordinadora",
                    ronda_origen="post_procesamiento_par",
                    failure_reasons=[],
                ))
                used.add(i)
                used.add(j)
            restantes.extend([c for idx, c in enumerate(grupo_ordenado) if idx not in used])
        else:
            restantes.extend(grupo_ordenado)

    return nuevos_brackets, restantes


# =============================================================================
# FUSIÓN DE BRACKETS PEQUEÑOS – FIX-G3
# =============================================================================

def fusionar_brackets_pequenos(brackets: List[Bracket]) -> List[Bracket]:
    """
    FIX-G3: Fusión agresiva y repetida de brackets pequeños.
    Usa criterios relajados (nivel 5) y también fusiona par+trío → cuarteto.
    Repite hasta que no haya más fusiones posibles.
    """
    # Límites relajados para la fusión (antes: peso=5, edad=1, estatura=10, nivel=1)
    limits = {"peso": 7.0, "edad": 4.0, "estatura": 13}
    nivel  = 5
    permitir_mezcla_adultos = True

    MAX_ITER_FUSION = 5
    for _ in range(MAX_ITER_FUSION):
        brackets_2 = [b for b in brackets if len(b.competidores) == 2]
        brackets_3 = [b for b in brackets if len(b.competidores) == 3]
        brackets_resto = [b for b in brackets if len(b.competidores) not in (2, 3)]

        improved = False

        # ── 2 + 2 → 4 ────────────────────────────────────────────────────────
        pares = list(enumerate(brackets_2))
        usados: Set[int] = set()
        nuevos_cuartetos: List[Bracket] = []

        for i in range(len(pares)):
            if i in usados:
                continue
            b1 = pares[i][1]
            c1, c2 = b1.competidores
            mejor_j, mejor_score = None, -1
            for j in range(i + 1, len(pares)):
                if j in usados:
                    continue
                b2 = pares[j][1]
                c3, c4 = b2.competidores
                grupo = [c1, c2, c3, c4]
                ok, _ = puede_grupo(grupo, limits, nivel, permitir_mezcla_adultos)
                if not ok:
                    continue
                s = sum(score(a, b, limits, nivel) for a in grupo for b in grupo if a.id < b.id) / 6
                if s > mejor_score:
                    mejor_score = s
                    mejor_j = j
            if mejor_j is not None:
                b2 = pares[mejor_j][1]
                grupo = [c1, c2, b2.competidores[0], b2.competidores[1]]
                avg, bd, _ = calcular_bracket_score(grupo, limits, nivel, permitir_mezcla_adultos)
                color = "verde" if avg >= 70 else "amarillo" if avg >= 50 else "naranja" if avg >= 30 else "rojo"
                nuevos_cuartetos.append(Bracket(
                    id=0, numero=0, area=0,
                    competidores=grupo,
                    tipo="fusion_2+2",
                    score=round(avg, 2),
                    score_breakdown=ScoreBreakdown(**bd),
                    nivel_aprobacion=color,
                    requiere_aprobacion=avg < 70,
                    aprobador_requerido="coordinadora" if avg < 50 else None,
                    ronda_origen="fusion_2+2",
                    failure_reasons=[],
                ))
                usados.add(i)
                usados.add(mejor_j)
                improved = True

        brackets_2_rest = [b for idx, b in pares if idx not in usados]

        # ── 2 + 3 → cuarteto (nuevo en FIX-G3) con trío separado ────────────
        nuevos_de_fusion_23: List[Bracket] = []
        usados_2: Set[int] = set()
        usados_3: Set[int] = set()

        for i2, b2 in enumerate(brackets_2_rest):
            if i2 in usados_2:
                continue
            cp = b2.competidores
            for i3, b3 in enumerate(brackets_3):
                if i3 in usados_3:
                    continue
                ct = b3.competidores
                # Intentar añadir el par al trío → cuarteto
                cuarteto = ct + list(cp)
                ok, _ = puede_grupo(cuarteto, limits, nivel, permitir_mezcla_adultos)
                if ok:
                    s = sum(score(a, b, limits, nivel) for a in cuarteto for b in cuarteto if a.id < b.id) / 6
                    if s >= 15:
                        avg, bd, _ = calcular_bracket_score(cuarteto, limits, nivel, permitir_mezcla_adultos)
                        color = "verde" if avg >= 70 else "amarillo" if avg >= 50 else "naranja" if avg >= 30 else "rojo"
                        nuevos_de_fusion_23.append(Bracket(
                            id=0, numero=0, area=0,
                            competidores=cuarteto,
                            tipo="fusion_2+3",
                            score=round(avg, 2),
                            score_breakdown=ScoreBreakdown(**bd),
                            nivel_aprobacion=color,
                            requiere_aprobacion=True,
                            aprobador_requerido="coordinadora",
                            ronda_origen="fusion_2+3",
                            failure_reasons=[],
                        ))
                        usados_2.add(i2)
                        usados_3.add(i3)
                        improved = True
                        break

        brackets_2_final = [b for idx, b in enumerate(brackets_2_rest) if idx not in usados_2]
        brackets_3_final = [b for idx, b in enumerate(brackets_3)      if idx not in usados_3]

        brackets = (
            brackets_2_final
            + brackets_3_final
            + brackets_resto
            + nuevos_cuartetos
            + nuevos_de_fusion_23
        )

        if not improved:
            break

    return brackets


# =============================================================================
# REORGANIZACIÓN AVANZADA
# =============================================================================

def reorganizacion_avanzada(brackets: List[Bracket], unpaired: List[Competidor]) -> Tuple[List[Bracket], List[Competidor]]:
    MAX_ITER = 10
    limits = {"peso": 5.0, "edad": 1.0, "estatura": 10}
    nivel  = 1
    permitir_mezcla_adultos = False

    for _ in range(MAX_ITER):
        if not unpaired:
            break
        improved = False

        for u in unpaired[:]:
            best = None
            for b in brackets[:]:
                if len(b.competidores) == 2:
                    nuevo_grupo = b.competidores + [u]
                    ok, _ = puede_grupo(nuevo_grupo, limits, nivel, permitir_mezcla_adultos)
                    if not ok:
                        continue
                    s = sum(score(a, b, limits, nivel) for a in nuevo_grupo for b in nuevo_grupo if a.id < b.id) / 3
                    if s >= 60:
                        if best is None or s > best[0]:
                            best = (s, b, nuevo_grupo)
            if best:
                s, b_old, nuevo_grupo = best
                avg, bd, _ = calcular_bracket_score(nuevo_grupo, limits, nivel, permitir_mezcla_adultos)
                brackets.remove(b_old)
                brackets.append(Bracket(
                    id=0, numero=0, area=0,
                    competidores=nuevo_grupo,
                    tipo="expandido",
                    score=round(avg, 2),
                    score_breakdown=ScoreBreakdown(**bd),
                    nivel_aprobacion="amarillo",
                    requiere_aprobacion=True,
                    aprobador_requerido="coordinadora",
                    ronda_origen="exp_2a3",
                    failure_reasons=[],
                ))
                unpaired.remove(u)
                improved = True
                break

        if not unpaired:
            break

        for u in unpaired[:]:
            best = None
            for b in brackets[:]:
                if len(b.competidores) == 3:
                    nuevo_grupo = b.competidores + [u]
                    ok, _ = puede_grupo(nuevo_grupo, limits, nivel, permitir_mezcla_adultos)
                    if not ok:
                        continue
                    s = sum(score(a, b, limits, nivel) for a in nuevo_grupo for b in nuevo_grupo if a.id < b.id) / 6
                    if s >= 60:
                        if best is None or s > best[0]:
                            best = (s, b, nuevo_grupo)
            if best:
                s, b_old, nuevo_grupo = best
                avg, bd, _ = calcular_bracket_score(nuevo_grupo, limits, nivel, permitir_mezcla_adultos)
                brackets.remove(b_old)
                brackets.append(Bracket(
                    id=0, numero=0, area=0,
                    competidores=nuevo_grupo,
                    tipo="expandido",
                    score=round(avg, 2),
                    score_breakdown=ScoreBreakdown(**bd),
                    nivel_aprobacion="amarillo",
                    requiere_aprobacion=True,
                    aprobador_requerido="coordinadora",
                    ronda_origen="exp_3a4",
                    failure_reasons=[],
                ))
                unpaired.remove(u)
                improved = True
                break

        if not unpaired:
            break

        for u in unpaired[:]:
            best = None
            for b in brackets[:]:
                if len(b.competidores) != 4:
                    continue
                comps = b.competidores
                for i in range(4):
                    trio = [comps[j] for j in range(4) if j != i]
                    nuevo_trio = trio + [u]
                    ok, _ = puede_grupo(nuevo_trio, limits, nivel, permitir_mezcla_adultos)
                    if not ok:
                        continue
                    s_trio = sum(score(a, b, limits, nivel) for a in nuevo_trio for b in nuevo_trio if a.id < b.id) / 3
                    if s_trio >= 60:
                        if best is None or s_trio > best[0]:
                            best = (s_trio, b, i, nuevo_trio, comps[i])
            if best:
                s, b_old, idx, nuevo_trio, liberado = best
                avg, bd, _ = calcular_bracket_score(nuevo_trio, limits, nivel, permitir_mezcla_adultos)
                brackets.remove(b_old)
                brackets.append(Bracket(
                    id=0, numero=0, area=0,
                    competidores=nuevo_trio,
                    tipo="reorganizado",
                    score=round(avg, 2),
                    score_breakdown=ScoreBreakdown(**bd),
                    nivel_aprobacion="naranja",
                    requiere_aprobacion=True,
                    aprobador_requerido="coordinadora",
                    ronda_origen="split_4to3_absorb",
                    failure_reasons=[],
                ))
                unpaired.remove(u)
                unpaired.append(liberado)
                improved = True
                break

        if not improved:
            break

    return brackets, unpaired


# =============================================================================
# ROBO DE BRACKETS
# =============================================================================

def robar_de_brackets(brackets: List[Bracket], unpaired: List[Competidor]) -> Tuple[List[Bracket], List[Competidor]]:
    candidatos = [b for b in brackets if len(b.competidores) in (2, 3)]
    if not candidatos or not unpaired:
        return brackets, unpaired

    candidatos.sort(key=lambda b: b.score)
    nuevos_brackets = [b for b in brackets if b not in candidatos]
    nuevos_unpaired = list(unpaired)

    for b in candidatos:
        grupo_original = b.competidores
        mejor = None
        for u in nuevos_unpaired[:]:
            trio = grupo_original + [u]
            ok, _ = puede_grupo(trio, {"peso": 7, "edad": 4, "estatura": 13}, 7, True, True)
            if ok:
                s = sum(score(a, b, {"peso": 7, "edad": 4, "estatura": 13}, 7) for a in trio for b in trio if a.id < b.id) / 3
                if s >= 30:
                    mejor = ("trio", trio, [u])
                    break
            if len(grupo_original) == 3:
                cuarteto = grupo_original + [u]
                ok, _ = puede_grupo(cuarteto, {"peso": 7, "edad": 4, "estatura": 13}, 7, True, True)
                if ok:
                    s = sum(score(a, b, {"peso": 7, "edad": 4, "estatura": 13}, 7) for a in cuarteto for b in cuarteto if a.id < b.id) / 6
                    if s >= 30:
                        mejor = ("cuarteto", cuarteto, [u])
                        break
        if mejor:
            tipo, nuevo_grupo, usado = mejor
            avg, bd, _ = calcular_bracket_score(nuevo_grupo, {"peso": 7, "edad": 4, "estatura": 13}, 7, True, True)
            nuevos_brackets.append(Bracket(
                id=0, numero=0, area=0,
                competidores=nuevo_grupo,
                tipo="robado",
                score=round(avg, 2),
                score_breakdown=ScoreBreakdown(**bd),
                nivel_aprobacion="rojo",
                requiere_aprobacion=True,
                aprobador_requerido="coordinadora",
                ronda_origen="robo_bracket",
                failure_reasons=[],
            ))
            nuevos_unpaired = [c for c in nuevos_unpaired if c.id not in [x.id for x in usado]]
        else:
            nuevos_brackets.append(b)
    return nuevos_brackets, nuevos_unpaired


# =============================================================================
# LOOP GLOBAL DE REASIGNACIÓN
# =============================================================================

def loop_reasignacion_global(brackets: List[Bracket], unpaired: List[Competidor]) -> Tuple[List[Bracket], List[Competidor]]:
    MAX_ITER = 10
    RESCUE_LIMITS = {"peso": 7.5, "edad": 6.0, "estatura": 14}
    nivel_rescate = 7
    permitir_mezcla_adultos = True

    for iteration in range(MAX_ITER):
        if len(unpaired) < 2:
            break
        improved = False

        permitir_cat_ady = (iteration >= MAX_ITER - 2)
        score_min_rescate = 0 if permitir_cat_ady else 20

        grupos = {}
        for c in unpaired:
            if es_bloque_adulto(c.bloque):
                key = (c.bloque, c.sexo)
            else:
                key = (c.categoria_edad, c.sexo)
            grupos.setdefault(key, []).append(c)

        nuevos_brackets = []
        nuevos_unpaired = []

        for grupo in grupos.values():
            grupo = sorted(grupo, key=lambda x: x.peso_kg)
            colapsar = es_bloque_adulto(grupo[0].bloque)

            i = 0
            while i < len(grupo) - 3:
                c1 = grupo[i]
                mejor = None
                window = min(20, len(grupo))
                for j in range(i + 1, min(i + window, len(grupo) - 2)):
                    c2 = grupo[j]
                    for k in range(j + 1, min(j + window, len(grupo) - 1)):
                        c3 = grupo[k]
                        for l in range(k + 1, min(k + window, len(grupo))):
                            c4 = grupo[l]
                            subset = [c1, c2, c3, c4]
                            ok, _ = puede_grupo(subset, RESCUE_LIMITS, nivel_rescate, permitir_mezcla_adultos, permitir_cat_ady, colapsar)
                            if ok:
                                avg, bd, _ = calcular_bracket_score(subset, RESCUE_LIMITS, nivel_rescate, permitir_mezcla_adultos, permitir_cat_ady)
                                if avg >= score_min_rescate:
                                    if mejor is None or avg > mejor[0]:
                                        mejor = (avg, subset, bd)
                if mejor:
                    avg, subset, bd = mejor
                    nuevos_brackets.append(Bracket(
                        id=0, numero=0, area=0,
                        competidores=subset,
                        tipo="rescate_4",
                        score=round(avg, 2),
                        score_breakdown=ScoreBreakdown(**bd),
                        nivel_aprobacion="rojo",
                        requiere_aprobacion=True,
                        aprobador_requerido="coordinadora",
                        ronda_origen="loop_global_cuarteto",
                        failure_reasons=[],
                    ))
                    ids_usados = {c.id for c in subset}
                    grupo = [c for c in grupo if c.id not in ids_usados]
                    i = 0
                    improved = True
                    continue
                i += 1

            i = 0
            while i < len(grupo) - 2:
                c1 = grupo[i]
                mejor = None
                window = min(20, len(grupo))
                for j in range(i + 1, min(i + window, len(grupo) - 1)):
                    c2 = grupo[j]
                    for k in range(j + 1, min(k + window, len(grupo))):
                        c3 = grupo[k]
                        subset = [c1, c2, c3]
                        ok, _ = puede_grupo(subset, RESCUE_LIMITS, nivel_rescate, permitir_mezcla_adultos, permitir_cat_ady, colapsar)
                        if ok:
                            avg, bd, _ = calcular_bracket_score(subset, RESCUE_LIMITS, nivel_rescate, permitir_mezcla_adultos, permitir_cat_ady)
                            if avg >= score_min_rescate:
                                if mejor is None or avg > mejor[0]:
                                    mejor = (avg, subset, bd)
                if mejor:
                    avg, subset, bd = mejor
                    nuevos_brackets.append(Bracket(
                        id=0, numero=0, area=0,
                        competidores=subset,
                        tipo="rescate_3",
                        score=round(avg, 2),
                        score_breakdown=ScoreBreakdown(**bd),
                        nivel_aprobacion="rojo",
                        requiere_aprobacion=True,
                        aprobador_requerido="coordinadora",
                        ronda_origen="loop_global_trio",
                        failure_reasons=[],
                    ))
                    ids_usados = {c.id for c in subset}
                    grupo = [c for c in grupo if c.id not in ids_usados]
                    i = 0
                    improved = True
                    continue
                i += 1

            if len(grupo) >= 2:
                pares = matching_hungaro(grupo, RESCUE_LIMITS, score_min_rescate, nivel_rescate, permitir_mezcla_adultos, colapsar_adultos=colapsar)
                usados = set()
                for i, j in pares:
                    subset = [grupo[i], grupo[j]]
                    avg, bd, _ = calcular_bracket_score(subset, RESCUE_LIMITS, nivel_rescate, permitir_mezcla_adultos)
                    nuevos_brackets.append(Bracket(
                        id=0, numero=0, area=0,
                        competidores=subset,
                        tipo="rescate_2",
                        score=round(avg, 2),
                        score_breakdown=ScoreBreakdown(**bd),
                        nivel_aprobacion="rojo",
                        requiere_aprobacion=True,
                        aprobador_requerido="coordinadora",
                        ronda_origen="loop_global_par",
                        failure_reasons=[],
                    ))
                    usados.add(i)
                    usados.add(j)
                    improved = True
                grupo = [c for idx, c in enumerate(grupo) if idx not in usados]
            nuevos_unpaired.extend(grupo)

        brackets.extend(nuevos_brackets)
        unpaired = nuevos_unpaired

        if improved and unpaired:
            brackets, unpaired = robar_de_brackets(brackets, unpaired)

        if not improved:
            break

    return brackets, unpaired


# =============================================================================
# MOTOR PRINCIPAL
# =============================================================================

def generar_brackets(competitors: List[Competidor]) -> Results:
    global _score_cache
    _score_cache.clear()

    if not competitors:
        return _resultado_vacio()

    for c in competitors:
        c.categoria_edad = get_categoria_edad(c.edad)
        asignar_bloque_correcto(c)

    competitors.sort(key=lambda c: (c.bloque, c.sexo, c.cinta_block, c.categoria_edad, c.edad, c.peso_kg))

    # -------------------------------------------------------------------------
    # Agrupación inicial v4: la clave SIEMPRE incluye cinta exacta.
    # Los niveles 1-7 solo relajan peso/edad/estatura, NUNCA la cinta.
    # Adultos G1: Marrón+Roja y Roja+Negra se pueden agrupar juntos en la misma
    # key porque cintas_permitidas() lo permite — la key NO los separa por cinta
    # para que el algoritmo los considere juntos dentro del mismo grupo.
    # -------------------------------------------------------------------------
    def _clave_grupo(c: Competidor) -> tuple:
        bloque = c.bloque
        cinta  = c.cinta_block
        sexo   = c.sexo
        if bloque == "Adultos Grupo 1":
            # G1: Marrón, Roja, Negra van en el mismo pool para que diff==1 sea posible.
            # La restricción fina la pone cintas_permitidas().
            return (bloque, sexo)
        if bloque == "Adultos Grupo 2":
            # G2: cada cinta es su propio silo — nunca se mezclan
            return (bloque, sexo, cinta)
        if bloque == "Infantil Avanzados":
            # Avanzados: Marrón+Roja+Negra en un pool, cintas_permitidas bloquea mezcla
            return (bloque, c.categoria_edad, sexo)
        if es_bloque_adulto(bloque):
            return (bloque, sexo, cinta)
        # Infantiles básicos y Pre-Tae: cada cinta es su propio silo
        return (bloque, c.categoria_edad, sexo, cinta)

    grupos_iniciales: Dict[tuple, List[Competidor]] = {}
    for c in competitors:
        grupos_iniciales.setdefault(_clave_grupo(c), []).append(c)

    todos_brackets: List[Bracket] = []
    no_emparejados: List[Competidor] = []

    # Niveles 1 a 7 — cinta nunca se cruza; solo se relajan físicos
    for nivel in range(1, 8):
        if nivel == 1:
            source = grupos_iniciales
        else:
            if not no_emparejados:
                break
            source = {}
            for c in no_emparejados:
                source.setdefault(_clave_grupo(c), []).append(c)
            no_emparejados = []

        for key, grupo in source.items():
            es_adulto = es_bloque_adulto(grupo[0].bloque)
            b, r = procesar_nivel(grupo, nivel, colapsar_adultos=es_adulto)
            todos_brackets.extend(b)
            no_emparejados.extend(r)

        if nivel == 1:
            # Fase 2.5 solo después del nivel 1
            todos_brackets, no_emparejados = fase_2_5_reorganizar(todos_brackets, no_emparejados)

    # Fusión de pares → cuartetos (respeta cintas porque puede_grupo() la valida)
    todos_brackets = fusionar_brackets_pequenos(todos_brackets)

    # Reorganización avanzada (también respeta cintas vía puede_grupo)
    todos_brackets, no_emparejados = reorganizacion_avanzada(todos_brackets, no_emparejados)

    # Loop global de rescate (respeta cintas)
    todos_brackets, no_emparejados = loop_reasignacion_global(todos_brackets, no_emparejados)

    # Segunda ronda de fusión
    todos_brackets = fusionar_brackets_pequenos(todos_brackets)

    # NOTA: fase_post_procesamiento_sin_rival() ha sido ELIMINADA intencionalmente.
    # En v4 el algoritmo NO mezcla cintas en ningún caso de post-proceso.
    # Los competidores sin rival de misma cinta quedan como "sin rival" para el humano.

    asignar_numeracion(todos_brackets, competitors)

    sin_rival_final = []
    for c in no_emparejados:
        razon = "Sin rival de misma cinta — requiere asignación manual"
        sin_rival_final.append(Unpaired(competidor=c, razon=razon))

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
        brackets_bloque = [b for b in brackets if b.competidores[0].bloque == bloque]
        for b in sorted(brackets_bloque, key=lambda x: x.id):
            b.numero = graf_num
            b.area = ((graf_num - 1) % 12) + 1
            graf_num += 1


def _construir_results(competitors, brackets, unpaired):
    total_comp  = len(competitors)
    total_brack = len(brackets)
    brackets_2  = sum(1 for b in brackets if len(b.competidores) == 2)
    brackets_3  = sum(1 for b in brackets if len(b.competidores) == 3)
    brackets_4  = sum(1 for b in brackets if len(b.competidores) == 4)
    excellent   = sum(1 for b in brackets if b.score >= 70)
    low_quality = sum(1 for b in brackets if b.score < 30)
    all_scores  = [b.score for b in brackets]
    avg_score   = sum(all_scores) / len(all_scores) if all_scores else 0
    emp_count   = total_comp - len(unpaired)
    emp_pct     = (emp_count / total_comp * 100) if total_comp > 0 else 0
    avg_size    = sum(len(b.competidores) for b in brackets) / total_brack if total_brack > 0 else 0

    gs = GlobalStats(
        total_competidores=total_comp,
        total_brackets=total_brack,
        avg_bracket_size=round(avg_size, 1),
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
        etapa2_count=0,
        ronda1_count=0,
        ronda2_count=0,
        ronda3_count=0,
        ronda4_count=0,
        fase2_5_count=0,
        nivel5_count=0,
        nivel6_count=0,
        nivel7_count=0,
        avg_score=round(avg_score, 2),
        emparejamiento_pct=round(emp_pct, 1),
    )
    return Results(global_stats=gs, block_stats=[], brackets=brackets, unpaired=unpaired)


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


def generate_results(competitors: List[Competidor]) -> Results:
    return generar_brackets(competitors)