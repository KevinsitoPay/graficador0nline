import pandas as pd
import uuid
from pathlib import Path
from typing import Dict, List, Tuple
from app.models import Competidor

EDAD_CATEGORIES = {
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

def get_categoria_edad(edad: int) -> str:
    for categoria, (min_edad, max_edad) in EDAD_CATEGORIES.items():
        if min_edad <= edad <= max_edad:
            return categoria
    return "Adulto"

VALID_BLOCKS = [
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

GRADO_TO_CINTA = {
    "pre-taekwondo": "Pre-Taekwondo",
    "pretaekwondo": "Pre-Taekwondo",
    "blanca": "Blanca",
    "10 kup": "Blanca",
    "10kup": "Blanca",
    "9 kup": "Amarilla",
    "9kup": "Amarilla",
    "amarilla": "Amarilla",
    "8 kup": "Verde",
    "8kup": "Verde",
    "verde": "Verde",
    "7 kup": "Azul",
    "7kup": "Azul",
    "azul": "Azul",
    "6 kup": "Azul",
    "6kup": "Azul",
    "5 kup": "Azul",
    "5kup": "Azul",
    "4 kup": "Marrón",
    "4kup": "Marrón",
    "3 kup": "Marrón",
    "3kup": "Marrón",
    "marrón": "Marrón",
    "2 kup": "Roja",
    "2kup": "Roja",
    "1 kup": "Roja",
    "1kup": "Roja",
    "roja": "Roja",
    "1er dan": "Negra (Dan)",
    "1 dan": "Negra (Dan)",
    "1dan": "Negra (Dan)",
    "1er poom": "Negra (Poom)",
    "2do dan": "Negra (Dan)",
    "2dan": "Negra (Dan)",
    "2do poom": "Negra (Poom)",
    "2poom": "Negra (Poom)",
    "3er dan": "Negra (Dan)",
    "3dan": "Negra (Dan)",
    "negra": "Negra (Dan)",
    "negro": "Negra (Dan)",
    "poom": "Negra (Poom)",
    "dan": "Negra (Dan)",
}

REQUIRED_COLUMNS = ["Nombre", "Apellido", "Edad", "H/M", "Grado", "Peso", "Estatura", "Modalidad", "Doyang"]


def normalize_grado(grado: str, edad: int) -> str:
    if not grado:
        return "Desconocido"
    
    grado_lower = grado.lower().strip()
    
    cinta = GRADO_TO_CINTA.get(grado_lower)
    
    if cinta:
        if "poom" in grado_lower or "dan" not in grado_lower and grado_lower.endswith("poom"):
            if edad < 15:
                return "Negra (Poom)"
            else:
                return "Negra (Dan)"
        elif "dan" in grado_lower:
            return "Negra (Dan)"
        return cinta
    
    if "negra" in grado_lower:
        if edad < 15:
            return "Negra (Poom)"
        return "Negra (Dan)"
    
    return "Desconocido"


def parse_float(value) -> float:
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    value_str = str(value).strip().replace(",", ".")
    try:
        return float(value_str)
    except:
        return 0.0


def parse_int(value) -> int:
    if pd.isna(value):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    try:
        return int(str(value).strip())
    except:
        return 0


def normalize_modalidad(modalidad: str) -> str:
    if not modalidad:
        return "Doble"
    
    mod_lower = modalidad.lower().strip()
    
    if mod_lower == "sencillo":
        return "Poomsae"
    if mod_lower == "combate":
        return "Combate"
    if mod_lower in ["doble", "dobles"]:
        return "Doble"
    
    return "Doble"


def validate_columns(df: pd.DataFrame, sheet_name: str) -> Tuple[bool, str]:
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        return False, f"Missing columns {missing} in sheet '{sheet_name}'"
    return True, ""


def parse_excel(file_path: str) -> Tuple[List[Competidor], List[Dict]]:
    all_competitors = []
    errors = []
    
    excel_file = pd.ExcelFile(file_path)
    
    for sheet_name in excel_file.sheet_names:
        if sheet_name not in VALID_BLOCKS:
            errors.append(f"Unknown block sheet: '{sheet_name}' - ignoring")
            continue
        
        try:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
        except Exception as e:
            errors.append(f"Error reading sheet '{sheet_name}': {str(e)}")
            continue
        
        valid, error_msg = validate_columns(df, sheet_name)
        if not valid:
            errors.append(error_msg)
            continue
        
        for idx, row in df.iterrows():
            try:
                edad = parse_int(row.get("Edad"))
                grado_raw = str(row.get("Grado", "")).strip()
                
                if not row.get("Nombre") or not row.get("Apellido"):
                    continue
                
                numero = str(row.get("No", ""))
                
                sexo_raw = str(row.get("H/M", "")).strip().upper()
                sexo = sexo_raw
                if sexo_raw == "H":
                    sexo = "M"
                
                comp = Competidor(
                    id=str(uuid.uuid4()),
                    nombre=str(row.get("Nombre", "")).strip(),
                    apellido=str(row.get("Apellido", "")).strip(),
                    edad=edad,
                    sexo=sexo,
                    grado_raw=grado_raw,
                    cinta_block=normalize_grado(grado_raw, edad),
                    peso_kg=parse_float(row.get("Peso")),
                    estatura_cm=parse_float(row.get("Estatura")),
                    modalidad=normalize_modalidad(str(row.get("Modalidad", "Doble"))),
                    doyang=str(row.get("Doyang", "")).strip(),
                    bloque=sheet_name,
                    categoria_edad=get_categoria_edad(edad),
                )
                
                if comp.sexo not in ["M", "F"]:
                    continue
                if comp.peso_kg <= 0 or comp.estatura_cm <= 0:
                    continue
                
                all_competitors.append(comp)
                
            except Exception as e:
                errors.append(f"Row {idx + 2} in '{sheet_name}': {str(e)}")
    
    return all_competitors, errors