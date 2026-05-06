from __future__ import annotations

import math
import re
from typing import List, Tuple, Optional

import pandas as pd

from app.models import Competidor

# =============================================================================
# ALIASES Y MAPEOS
# =============================================================================

SHEET_ALIASES = {
    "ADULTOS": "Adultos",
    "ADULTOS BLOQUE 1": "Adultos Grupo 1",
    "ADULTOS GRUPO 1": "Adultos Grupo 1",
    "ADULTOS GRUPO 2": "Adultos Grupo 2",
    "INFANTIL AZUL": "Infantil Azul",
    "INFANTIL VERDE": "Infantil Verde",
    "INFANTIL AMARILLA": "Infantil Amarilla",
    "INFANTIL BLANCA": "Infantil Blanca",
    "INFANTIL MARRON": "Infantil Marrón",
    "INFANTIL MARRÓN": "Infantil Marrón",
    "INFANTIL ROJA": "Infantil Roja",
    "INFANTIL NEGRA": "Infantil Negra",
    "PRETKD": "Pre-Taekwondo",
    "PRE-TKD": "Pre-Taekwondo",
    "PRE TAEKWONDO": "Pre-Taekwondo",
    "PRE-TAEKWONDO": "Pre-Taekwondo",
}

COLUMN_ALIASES = {
    "NO": "No",
    "NOMBRE": "Nombre",
    "NOMBRE ": "Nombre",
    "APELLIDO": "Apellido",
    "APELLIDOS": "Apellido",
    "EDAD": "Edad",
    "H / M": "H/M",
    "H/M": "H/M",
    "SEXO": "H/M",
    "GRADO": "Grado",
    "PESO": "Peso",
    "ESTATURA": "Estatura",
    "MODALIDAD": "Modalidad",
    "DOYANG": "Doyang",
    "ESCUELA": "Doyang",
    "CATEGORIA": "Categoria",
    "CATEGORÍA": "Categoria",
}

SECTION_TITLE_ALIASES = {
    "PRETAEKWONDO": "Pre-Taekwondo",
    "PRE TAEKWONDO": "Pre-Taekwondo",
    "PRE-TAEKWONDO": "Pre-Taekwondo",
    "PRETKD": "Pre-Taekwondo",

    "CINTA BLANCA INFANTIL": "Infantil Blanca",
    "INFANTIL CINTA BLANCA": "Infantil Blanca",
    "CINTA AMARILLA INFANTIL": "Infantil Amarilla",
    "INFANTIL CINTA AMARILLA": "Infantil Amarilla",
    "CINTA VERDE INFANTIL": "Infantil Verde",
    "INFANTIL CINTA VERDE": "Infantil Verde",
    "CINTA AZUL INFANTIL": "Infantil Azul",
    "INFANTIL CINTA AZUL": "Infantil Azul",
    "CINTA MARRON INFANTIL": "Infantil Marrón",
    "CINTA MARRÓN INFANTIL": "Infantil Marrón",
    "INFANTIL CINTA MARRON": "Infantil Marrón",
    "INFANTIL CINTA MARRÓN": "Infantil Marrón",
    "CINTA ROJA INFANTIL": "Infantil Roja",
    "INFANTIL CINTA ROJA": "Infantil Roja",
    "CINTA NEGRA INFANTIL": "Infantil Negra",
    "INFANTIL CINTA NEGRA": "Infantil Negra",

    "CADETE JUVENIL Y ADULTO": "Adultos",
    "CADETE - JUVENIL - ADULTO": "Adultos",
    "JUVENIL ADULTO": "Adultos",
}

POSITIONAL_COLUMNS = [
    "Nombre",
    "Apellido",
    "Edad",
    "H/M",
    "Grado",
    "Peso",
    "Estatura",
    "Categoria",
    "Modalidad",
    "Doyang",
]

# =============================================================================
# NORMALIZADORES
# =============================================================================

def _norm_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).replace("\n", " ").replace("\r", " ").replace("\t", " ").strip()

def _norm_key(value: str) -> str:
    v = _norm_text(value).upper()
    v = v.replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")
    v = re.sub(r"\s+", " ", v)
    return v.strip()

def normalize_sheet_name(name: str) -> Optional[str]:
    key = _norm_key(name)

    if key in SHEET_ALIASES:
        return SHEET_ALIASES[key]

    if "ADULTOS" in key and "GRUPO 1" in key:
        return "Adultos Grupo 1"
    if "ADULTOS" in key and "GRUPO 2" in key:
        return "Adultos Grupo 2"
    if key == "ADULTOS":
        return "Adultos"

    if "INFANTIL" in key and "AZUL" in key:
        return "Infantil Azul"
    if "INFANTIL" in key and "VERDE" in key:
        return "Infantil Verde"
    if "INFANTIL" in key and "AMARILLA" in key:
        return "Infantil Amarilla"
    if "INFANTIL" in key and "BLANCA" in key:
        return "Infantil Blanca"
    if "INFANTIL" in key and ("MARRON" in key or "MARRÓN" in key):
        return "Infantil Marrón"
    if "INFANTIL" in key and "ROJA" in key:
        return "Infantil Roja"
    if "INFANTIL" in key and "NEGRA" in key:
        return "Infantil Negra"

    if "PRE" in key and ("TKD" in key or "TAEKWONDO" in key):
        return "Pre-Taekwondo"

    return "General"

def normalize_column_name(name: str) -> str:
    key = _norm_key(name)
    return COLUMN_ALIASES.get(key, _norm_text(name))

def normalize_section_title(text: str) -> Optional[str]:
    key = _norm_key(text)
    return SECTION_TITLE_ALIASES.get(key)

def normalize_sexo(value: str) -> str:
    v = _norm_key(value)
    if v in ("H", "HOMBRE", "MASCULINO"):
        return "H"
    if v in ("M", "F", "MUJER", "FEMENINO"):
        return "M"
    return _norm_text(value)

def normalize_modalidad(value: str) -> str:
    v = _norm_key(value)
    if "DOBLE" in v:
        return "Doble"
    if "FORMA" in v or "POOMSAE" in v:
        return "Formas"
    if "COMBATE" in v:
        return "Combate"
    if "SENCILLO" in v:
        return "Sencillo"
    return _norm_text(value).title()

def normalize_categoria_texto(value: str) -> str:
    v = _norm_key(value)
    if "PRESCOLAR" in v or "PREESCOLAR" in v:
        return "Prescolar"
    if "INFANTIL" in v:
        return "Infantil"
    if "JUVENIL" in v or "ADULTO" in v:
        return "Juvenil/Adulto"
    return _norm_text(value)

def normalize_grado(grado_raw: str) -> Tuple[str, str]:
    raw = _norm_text(grado_raw)
    v = _norm_key(grado_raw)

    v = v.replace("IEBY POM", "IEBY POOM")
    v = v.replace("IEBY  POOM", "IEBY POOM")
    v = v.replace("IEBY  DAN", "IEBY DAN")
    v = v.replace("1 DAN", "1 DAN")
    v = v.replace("2 DAN", "2 DAN")
    v = v.replace("3 DAN", "3 DAN")
    v = v.replace("1 POOM", "1 POOM")
    v = v.replace("2 POOM", "2 POOM")
    v = v.replace("3 POOM", "3 POOM")

    if "IEBY POOM" in v or re.search(r"\b\d+\s*POOM\b", v):
        return raw, "Negra (Poom)"
    if "IEBY DAN" in v or re.search(r"\b\d+\s*DAN\b", v):
        return raw, "Negra (Dan)"

    if "BLANCA" in v:
        return raw, "Blanca"
    if "AMARILLA" in v:
        return raw, "Amarilla"
    if "VERDE" in v:
        return raw, "Verde"
    if "AZUL" in v:
        return raw, "Azul"
    if "MARRON" in v or "MARRÓN" in v:
        return raw, "Marrón"
    if "ROJA" in v:
        return raw, "Roja"

    kup_match = re.search(r"(\d+)\s*KUP", v)
    if kup_match:
        kup = int(kup_match.group(1))
        if kup == 10:
            return raw, "Blanca"
        elif kup in (8, 9):
            return raw, "Amarilla"
        elif kup in (6, 7):
            return raw, "Verde"
        elif kup in (4, 5):
            return raw, "Azul"
        elif kup in (2, 3):
            return raw, "Marrón"
        elif kup == 1:
            return raw, "Roja"

    if "PRINCIPIANTE" in v:
        return raw, "Blanca"

    return raw, "Desconocido"

def _to_float(value) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None

    txt = _norm_text(value)
    txt = txt.replace(",", ".")
    txt = txt.replace(" ", "")
    txt = re.sub(r"[^0-9.\-]", "", txt)

    if txt == "":
        return None

    try:
        val = float(txt)
        # corregir posible estatura en metros o peso absurdo
        return val
    except Exception:
        return None

def _to_int(value) -> Optional[int]:
    n = _to_float(value)
    if n is None:
        return None
    return int(round(n))

def _normalize_estatura(estatura: Optional[float]) -> float:
    if estatura is None:
        return 0.0
    # si viene en metros tipo 1.59 -> 159
    if 0.5 < estatura < 2.5:
        return round(estatura * 100, 2)
    return float(estatura)

def _normalize_peso(peso: Optional[float]) -> Optional[float]:
    if peso is None:
        return None
    # descartar casos absurdos tipo 3840
    if peso > 300:
        return None
    return float(peso)

def _find_header_row(df: pd.DataFrame) -> Optional[int]:
    for idx in range(min(len(df), 40)):
        row_values = [normalize_column_name(v) for v in df.iloc[idx].tolist()]
        normalized = {v for v in row_values if v}
        if {"Nombre", "Apellido", "Edad", "Grado", "Peso", "Estatura"}.issubset(normalized):
            return idx
    return None

def _looks_like_positional_row(values: List) -> bool:
    if len(values) < 10:
        return False

    nombre = _norm_text(values[0])
    apellido = _norm_text(values[1])
    edad = _to_int(values[2])
    sexo = normalize_sexo(values[3])
    grado = _norm_text(values[4])
    peso = _normalize_peso(_to_float(values[5]))
    est = _normalize_estatura(_to_float(values[6]))

    if not nombre or not apellido:
        return False
    if edad is None:
        return False
    if sexo not in ("H", "M"):
        return False
    if not grado:
        return False
    if peso is None or est <= 0:
        return False

    return True

def _is_observation_row(values: List) -> bool:
    combined = " ".join(_norm_text(v) for v in values).upper()
    markers = [
        "CITAR CON BLOQUE",
        "CAMBIO A BLOQUE",
        "SE MOVIO A BLOQUE",
        "SE MOVIÓ A BLOQUE",
        "ELIMINAR DE LA GRAFICA",
        "ELIMINAR DE LA GRÁFICA",
        "<<<",
    ]
    return any(m in combined for m in markers)

def _row_empty(values: List) -> bool:
    return all(_norm_text(v) == "" for v in values)

def _infer_initial_block(sheet_name: str, edad: int, cinta_block: str, categoria_txt: str) -> str:
    categoria_txt = normalize_categoria_texto(categoria_txt)

    if sheet_name == "Adultos Grupo 1":
        return "Adultos Grupo 1"
    if sheet_name == "Adultos Grupo 2":
        return "Adultos Grupo 2"
    if sheet_name == "Infantil Azul":
        return "Infantil Azul"
    if sheet_name == "Infantil Verde":
        return "Infantil Verde"
    if sheet_name == "Infantil Amarilla":
        return "Infantil Amarilla"
    if sheet_name == "Infantil Blanca":
        return "Infantil Blanca"
    if sheet_name in ("Infantil Marrón", "Infantil Roja", "Infantil Negra"):
        return "Infantil Avanzados"
    if sheet_name == "Pre-Taekwondo":
        return "Pre-Taekwondo"

    if categoria_txt == "Prescolar" or edad <= 5:
        return "Pre-Taekwondo"

    if categoria_txt == "Infantil" or edad <= 13:
        if cinta_block == "Blanca":
            return "Infantil Blanca"
        if cinta_block == "Amarilla":
            return "Infantil Amarilla"
        if cinta_block == "Verde":
            return "Infantil Verde"
        if cinta_block == "Azul":
            return "Infantil Azul"
        if cinta_block in ("Marrón", "Roja", "Negra (Poom)", "Negra (Dan)"):
            return "Infantil Avanzados"
        return "Infantil Blanca"

    if cinta_block in ("Marrón", "Roja", "Negra (Poom)", "Negra (Dan)"):
        return "Adultos Grupo 1"
    return "Adultos Grupo 2"

# =============================================================================
# PARSERS
# =============================================================================

def _build_competidor(
    nombre: str,
    apellido: str,
    edad: int,
    sexo: str,
    grado_raw: str,
    peso: float,
    estatura: float,
    modalidad: str,
    doyang: str,
    bloque: str,
    cid: int,
) -> Competidor:
    grado_norm, cinta_block = normalize_grado(grado_raw)
    return Competidor(
        id=f"C{cid}",
        nombre=nombre,
        apellido=apellido,
        edad=int(edad),
        sexo=sexo,
        grado_raw=grado_norm,
        cinta_block=cinta_block,
        peso_kg=float(peso),
        estatura_cm=float(estatura),
        modalidad=modalidad,
        doyang=doyang if doyang else "Desconocido",
        bloque=bloque,
        categoria_edad=None,
        numero_competidor=None,
    )

def _parse_with_header(df: pd.DataFrame, original_sheet_name: str, canonical_sheet_name: str, start_id: int):
    competitors = []
    errors = []

    header_row = _find_header_row(df)
    if header_row is None:
        return [], [f"Could not find header row in sheet '{original_sheet_name}'"], start_id

    headers = [normalize_column_name(v) for v in df.iloc[header_row].tolist()]
    data = df.iloc[header_row + 1:].copy()
    data.columns = headers
    data = data.reset_index(drop=True)

    required_cols = {"Nombre", "Apellido", "Edad", "H/M", "Grado", "Peso", "Estatura", "Modalidad", "Doyang"}
    missing = required_cols - set(data.columns)
    if missing:
        return [], [f"Missing columns in sheet '{original_sheet_name}': {sorted(missing)}"], start_id

    current_id = start_id

    for _, row in data.iterrows():
        values = list(row.values)
        if _row_empty(values) or _is_observation_row(values):
            continue

        nombre = _norm_text(row.get("Nombre"))
        apellido = _norm_text(row.get("Apellido"))
        edad = _to_int(row.get("Edad"))
        sexo = normalize_sexo(row.get("H/M"))
        grado_raw = _norm_text(row.get("Grado"))
        peso = _normalize_peso(_to_float(row.get("Peso")))
        estatura = _normalize_estatura(_to_float(row.get("Estatura")))
        modalidad = normalize_modalidad(row.get("Modalidad"))
        doyang = _norm_text(row.get("Doyang"))
        categoria_txt = _norm_text(row.get("Categoria"))

        if not nombre or not apellido or edad is None or peso is None:
            continue

        bloque = _infer_initial_block(canonical_sheet_name, edad, normalize_grado(grado_raw)[1], categoria_txt)

        comp = _build_competidor(
            nombre, apellido, edad, sexo, grado_raw, peso, estatura,
            modalidad, doyang, bloque, current_id
        )
        competitors.append(comp)
        current_id += 1

    return competitors, errors, current_id

def _parse_positional(df: pd.DataFrame, original_sheet_name: str, canonical_sheet_name: str, start_id: int):
    competitors = []
    errors = []
    current_id = start_id

    for _, row in df.iterrows():
        values = row.tolist()

        if _row_empty(values) or _is_observation_row(values):
            continue

        while len(values) < 10:
            values.append("")

        if not _looks_like_positional_row(values):
            continue

        nombre = _norm_text(values[0])
        apellido = _norm_text(values[1])
        edad = _to_int(values[2])
        sexo = normalize_sexo(values[3])
        grado_raw = _norm_text(values[4])
        peso = _normalize_peso(_to_float(values[5]))
        estatura = _normalize_estatura(_to_float(values[6]))
        categoria_txt = _norm_text(values[7])
        modalidad = normalize_modalidad(values[8])
        doyang = _norm_text(values[9])

        if edad is None or peso is None:
            continue

        bloque = _infer_initial_block(canonical_sheet_name, edad, normalize_grado(grado_raw)[1], categoria_txt)

        comp = _build_competidor(
            nombre, apellido, edad, sexo, grado_raw, peso, estatura,
            modalidad, doyang, bloque, current_id
        )
        competitors.append(comp)
        current_id += 1

    return competitors, errors, current_id

def _parse_multi_section_sheet(df: pd.DataFrame, original_sheet_name: str, canonical_sheet_name: str, start_id: int):
    """
    Nuevo: soporta hojas donde hay varios bloques internos en la misma pestaña.
    """
    competitors = []
    errors = []
    current_id = start_id

    current_section_block = canonical_sheet_name if canonical_sheet_name != "General" else None
    current_header = None

    for idx in range(len(df)):
        row_values = df.iloc[idx].tolist()

        if _row_empty(row_values):
            continue

        # 1) detectar título de sección
        joined = " ".join(_norm_text(v) for v in row_values if _norm_text(v)).strip()
        section_name = normalize_section_title(joined)
        if section_name:
            current_section_block = section_name
            current_header = None
            continue

        # 2) detectar encabezado interno
        normalized_row = [normalize_column_name(v) for v in row_values]
        normalized_set = {v for v in normalized_row if v}
        if {"Nombre", "Apellido", "Edad", "Grado", "Peso", "Estatura"}.issubset(normalized_set):
            current_header = normalized_row
            continue

        # 3) si hay encabezado, intentar parsear fila de esa sección
        if current_header is not None:
            row_dict = {}
            for c_idx, col_name in enumerate(current_header):
                if not col_name:
                    continue
                row_dict[col_name] = row_values[c_idx] if c_idx < len(row_values) else ""

            if _is_observation_row(list(row_dict.values())):
                continue

            nombre = _norm_text(row_dict.get("Nombre"))
            apellido = _norm_text(row_dict.get("Apellido"))
            edad = _to_int(row_dict.get("Edad"))
            sexo = normalize_sexo(row_dict.get("H/M"))
            grado_raw = _norm_text(row_dict.get("Grado"))
            peso = _normalize_peso(_to_float(row_dict.get("Peso")))
            estatura = _normalize_estatura(_to_float(row_dict.get("Estatura")))
            modalidad = normalize_modalidad(row_dict.get("Modalidad"))
            doyang = _norm_text(row_dict.get("Doyang"))
            categoria_txt = _norm_text(row_dict.get("Categoria"))

            if not nombre or not apellido or edad is None or peso is None:
                continue

            section_block = current_section_block or canonical_sheet_name
            bloque = _infer_initial_block(section_block, edad, normalize_grado(grado_raw)[1], categoria_txt)

            comp = _build_competidor(
                nombre, apellido, edad, sexo, grado_raw, peso, estatura,
                modalidad, doyang, bloque, current_id
            )
            competitors.append(comp)
            current_id += 1
            continue

        # 4) si no hay header interno, intentar posicional (por si la hoja es general)
        values = row_values[:]
        while len(values) < 10:
            values.append("")

        if _looks_like_positional_row(values):
            nombre = _norm_text(values[0])
            apellido = _norm_text(values[1])
            edad = _to_int(values[2])
            sexo = normalize_sexo(values[3])
            grado_raw = _norm_text(values[4])
            peso = _normalize_peso(_to_float(values[5]))
            estatura = _normalize_estatura(_to_float(values[6]))
            categoria_txt = _norm_text(values[7])
            modalidad = normalize_modalidad(values[8])
            doyang = _norm_text(values[9])

            if edad is None or peso is None:
                continue

            section_block = current_section_block or canonical_sheet_name
            bloque = _infer_initial_block(section_block, edad, normalize_grado(grado_raw)[1], categoria_txt)

            comp = _build_competidor(
                nombre, apellido, edad, sexo, grado_raw, peso, estatura,
                modalidad, doyang, bloque, current_id
            )
            competitors.append(comp)
            current_id += 1

    return competitors, errors, current_id

# =============================================================================
# API PRINCIPAL
# =============================================================================

def parse_excel(filepath: str) -> Tuple[List[Competidor], List[str]]:
    competitors: List[Competidor] = []
    errors: List[str] = []

    try:
        xls = pd.ExcelFile(filepath)
    except Exception as e:
        return [], [f"Could not open Excel file: {e}"]

    current_id = 1

    for original_sheet_name in xls.sheet_names:
        canonical_sheet_name = normalize_sheet_name(original_sheet_name)

        try:
            df = pd.read_excel(filepath, sheet_name=original_sheet_name, header=None)
        except Exception as e:
            errors.append(f"Error reading sheet '{original_sheet_name}': {e}")
            continue

        # 1) intentar formato con header clásico
        header_row = _find_header_row(df)
        if header_row is not None:
            parsed, local_errors, current_id = _parse_with_header(
                df, original_sheet_name, canonical_sheet_name, current_id
            )
            competitors.extend(parsed)
            errors.extend(local_errors)

            # además intentar secciones internas por si la hoja mezcla varios bloques
            parsed_sections, local_errors2, current_id = _parse_multi_section_sheet(
                df, original_sheet_name, canonical_sheet_name, current_id
            )

            # evitar duplicados exactos
            existing_keys = {
                (c.nombre, c.apellido, c.edad, c.sexo, c.grado_raw, c.peso_kg, c.estatura_cm, c.doyang)
                for c in competitors
            }
            for c in parsed_sections:
                key = (c.nombre, c.apellido, c.edad, c.sexo, c.grado_raw, c.peso_kg, c.estatura_cm, c.doyang)
                if key not in existing_keys:
                    competitors.append(c)
                    existing_keys.add(key)

            errors.extend(local_errors2)
            continue

        # 2) intentar multi-sección
        parsed_multi, local_errors_multi, current_id = _parse_multi_section_sheet(
            df, original_sheet_name, canonical_sheet_name, current_id
        )
        if parsed_multi:
            competitors.extend(parsed_multi)
            errors.extend(local_errors_multi)
            continue

        # 3) intentar posicional
        parsed, local_errors, current_id = _parse_positional(
            df, original_sheet_name, canonical_sheet_name, current_id
        )
        competitors.extend(parsed)
        errors.extend(local_errors)

    return competitors, errors

