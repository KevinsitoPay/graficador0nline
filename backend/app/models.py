from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class Sexo(str, Enum):
    MASCULINO = "M"
    FEMENINO = "F"

class Modalidad(str, Enum):
    DOBLE = "Doble"
    SENCILLO = "Sencillo"
    COMBATE = "Combate"
    POOMSAE = "Poomsae"

class CintaBlock(str, Enum):
    PRE_TAEKWONDO = "Pre-Taekwondo"
    BLANCA = "Blanca"
    AMARILLA = "Amarilla"
    VERDE = "Verde"
    AZUL = "Azul"
    MARRON = "Marrón"
    ROJA = "Roja"
    NEGRA_POOM = "Negra (Poom)"
    NEGRA_DAN = "Negra (Dan)"

class BracketType(str, Enum):
    NORMAL = "normal"
    RELAXED_AGE = "relaxed_age"
    RELAXED_LIMITS = "relaxed_limits"

class Competidor(BaseModel):
    id: str
    nombre: str
    apellido: str
    edad: int
    sexo: str
    grado_raw: str
    cinta_block: str
    peso_kg: float
    estatura_cm: float
    modalidad: str
    doyang: str
    bloque: str
    categoria_edad: Optional[str] = None
    numero_competidor: Optional[str] = None

class ScoreBreakdown(BaseModel):
    modalidad_ok: bool
    edad_diff: int
    edad_score: float
    peso_diff: float
    peso_score: float
    estatura_diff: int
    estatura_score: float
    doyang_penalty: float = 0
    cinta_penalty: float = 0
    total: float


class Bracket(BaseModel):
    id: int
    numero: int
    area: int
    competidores: List[Competidor]
    tipo: str
    score: float
    score_breakdown: Optional[ScoreBreakdown] = None
    nivel_aprobacion: Optional[str] = None  # verde_claro, amarillo, naranja, rojo
    requiere_aprobacion: bool = False
    aprobador_requerido: Optional[str] = None  # colaborador, coordenadora
    ronda_origen: Optional[str] = None  # etapa2, etapa3_ronda1, etc.
    failure_reasons: Optional[List[str]] = None  # razones por las cuales el score es 0

class Unpaired(BaseModel):
    competidor: Competidor
    razon: str

class BlockStats(BaseModel):
    bloque: str
    competidores: int
    brackets: int
    avg_size: float
    sin_rival: int
    relaxed_count: int

class GlobalStats(BaseModel):
    total_competidores: int
    total_brackets: int
    avg_bracket_size: float
    brackets_2: int
    brackets_3: int
    brackets_4: int
    sin_rival_total: int
    excellent_brackets: int
    low_quality_brackets: int
    brackets_verde: int = 0
    brackets_amarillo: int = 0
    brackets_naranja: int = 0
    brackets_rojo: int = 0
    etapa2_count: int = 0
    ronda1_count: int = 0
    ronda2_count: int = 0
    ronda3_count: int = 0
    ronda4_count: int = 0
    fase2_5_count: int = 0
    nivel5_count: int = 0
    nivel6_count: int = 0
    nivel7_count: int = 0
    avg_score: float = 0.0
    emparejamiento_pct: float = 0.0

class Results(BaseModel):
    global_stats: GlobalStats
    block_stats: List[BlockStats]
    brackets: List[Bracket]
    unpaired: List[Unpaired]

class UploadResponse(BaseModel):
    success: bool
    message: str
    results: Optional[Results] = None