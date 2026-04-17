from typing import List, Dict, Tuple, Optional, Set
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.models import Competidor, Bracket, ScoreBreakdown
from app.algorithm import (
    score, puede_emparejarse, _calcular_bracket_score,
    CINTA_ADYACENTE, RELAXATION_LEVELS, get_cinta_normalizada,
    _bloques_adultos_compatibles, _modalidad_grupo_ok
)

RELAXATION_LEVELS_EXTENDED = RELAXATION_LEVELS + [
    {"nivel": 6, "peso": 7.0, "edad": 3.0, "estatura": 16, "mezcla_cintas": True, "score_min": 50, "color": "rojo_oscuro"},
]


class Recomendacion(BaseModel):
    id: str
    tipo: str
    competidor: Competidor
    bracket_origen_id: Optional[int]
    bracket_destino_id: Optional[int]
    competidores_propuestos: List[Competidor]
    score_esperado: float
    justificacion: str
    limites_usados: Dict
    nivel_relajacion: int


class ActionRecord(BaseModel):
    id: str
    timestamp: datetime
    tipo: str
    competidor_id: str
    bracket_origen_id: Optional[int]
    bracket_destino_id: Optional[int]
    competidores_ids: List[str]
    usuario: str = "colaborador"
    justificacion: Optional[str]
    reversed: bool = False


class RecomendacionManager:
    def __init__(self):
        self.historial: List[ActionRecord] = []
    
    def generar_recomendaciones(
        self, 
        unpaired: List[Competidor], 
        brackets: List[Bracket]
    ) -> List[Recomendacion]:
        recomendaciones = []
        
        for competidor in unpaired:
            integraciones = self.sugerir_integracion(competidor, brackets)
            recomendaciones.extend(integraciones)
            
            if not integraciones:
                divisiones = self.sugerir_division(competidor, brackets)
                recomendaciones.extend(divisiones)
        
        nuevos_brackets = self.sugerir_nuevo_bracket(unpaired)
        recomendaciones.extend(nuevos_brackets)
        
        return sorted(recomendaciones, key=lambda r: r.score_esperado, reverse=True)
    
    def sugerir_integracion(
        self, 
        competidor: Competidor, 
        brackets: List[Bracket]
    ) -> List[Recomendacion]:
        recomendaciones = []
        limites_base = {"peso": 6.5, "edad": 2.5, "estatura": 14}
        
        for nivel in range(1, 7):
            config = RELAXATION_LEVELS_EXTENDED[nivel - 1]
            limits = {"peso": config["peso"], "edad": config["edad"], "estatura": config["estatura"]}
            
            for bracket in brackets:
                if len(bracket.competidores) >= 4:
                    continue
                
                comps = bracket.competidores
                if not all(c.sexo == competidor.sexo for c in comps):
                    continue
                if not all(c.bloque == competidor.bloque for c in comps):
                    continue
                if not all(c.categoria_edad == competidor.categoria_edad for c in comps):
                    continue
                
                nuevos_comps = comps + [competidor]
                
                if not _validar_grupo(nuevos_comps, limits):
                    continue
                
                s, bd, _ = _calcular_bracket_score(nuevos_comps, limits)
                
                if s >= config["score_min"]:
                    recomendaciones.append(Recomendacion(
                        id=str(uuid.uuid4()),
                        tipo="integracion",
                        competidor=competidor,
                        bracket_origen_id=None,
                        bracket_destino_id=bracket.id,
                        competidores_propuestos=nuevos_comps,
                        score_esperado=round(s, 2),
                        justificacion=f"Integrar a bracket #{bracket.id} ({len(comps)}→{len(nuevos_comps)} competidores)",
                        limites_usados=limits,
                        nivel_relajacion=nivel
                    ))
                    break
        
        return recomendaciones
    
    def sugerir_division(
        self, 
        competidor: Competidor, 
        brackets: List[Bracket]
    ) -> List[Recomendacion]:
        recomendaciones = []
        
        for nivel in range(1, 7):
            config = RELAXATION_LEVELS_EXTENDED[nivel - 1]
            limits = {"peso": config["peso"], "edad": config["edad"], "estatura": config["estatura"]}
            
            brackets_4 = [b for b in brackets if len(b.competidores) == 4]
            
            for bracket in brackets_4:
                comps = bracket.competidores
                
                if not _es_homogeneo_amplio(comps):
                    continue
                
                if not all(c.sexo == competidor.sexo for c in comps):
                    continue
                if not all(c.categoria_edad == competidor.categoria_edad for c in comps):
                    continue
                
                comps_sorted = sorted(comps, key=lambda c: c.peso_kg)
                
                for i in range(len(comps_sorted) - 1):
                    for j in range(i + 1, len(comps_sorted)):
                        grupo1 = [comps_sorted[i], comps_sorted[j], competidor]
                        grupo2 = [c for idx, c in enumerate(comps_sorted) if idx not in (i, j)]
                        
                        if len(grupo2) != 2:
                            continue
                        
                        if not _validar_grupo(grupo1, limits) or not _validar_grupo(grupo2, limits):
                            continue
                        
                        s1, _, _ = _calcular_bracket_score(grupo1, limits)
                        s2, _, _ = _calcular_bracket_score(grupo2, limits)
                        
                        if s1 >= config["score_min"] and s2 >= config["score_min"]:
                            min_score = min(s1, s2)
                            recomendaciones.append(Recomendacion(
                                id=str(uuid.uuid4()),
                                tipo="division",
                                competidor=competidor,
                                bracket_origen_id=bracket.id,
                                bracket_destino_id=None,
                                competidores_propuestos=grupo1 + grupo2,
                                score_esperado=round(min_score, 2),
                                justificacion=f"Dividir bracket #{bracket.id} ({len(comps)}→2+{len(grupo1)})",
                                limites_usados=limits,
                                nivel_relajacion=nivel
                            ))
                            break
                    if recomendaciones:
                        break
                if recomendaciones:
                    break
        
        return recomendaciones
    
    def sugerir_nuevo_bracket(
        self, 
        competidores_sin_rival: List[Competidor]
    ) -> List[Recomendacion]:
        recomendaciones = []
        
        if len(competidores_sin_rival) < 2:
            return recomendaciones
        
        for nivel in range(1, 7):
            config = RELAXATION_LEVELS_EXTENDED[nivel - 1]
            limits = {"peso": config["peso"], "edad": config["edad"], "estatura": config["estatura"]}
            
            competidores_por_grupo: Dict[Tuple, List[Competidor]] = {}
            for c in competidores_sin_rival:
                key = (c.bloque, c.categoria_edad, c.sexo)
                competidores_por_grupo.setdefault(key, []).append(c)
            
            for key, comps in competidores_por_grupo.items():
                if len(comps) < 2:
                    continue
                
                comps_sorted = sorted(comps, key=lambda c: c.peso_kg)
                
                for i in range(len(comps_sorted) - 1):
                    for j in range(i + 1, len(comps_sorted)):
                        nuevo_grupo = [comps_sorted[i], comps_sorted[j]]
                        
                        puede, razon = puede_emparejarse(comps_sorted[i], comps_sorted[j], limits)
                        if not puede:
                            continue
                        
                        s, bd, _ = _calcular_bracket_score(nuevo_grupo, limits)
                        
                        if s >= config["score_min"]:
                            recomendaciones.append(Recomendacion(
                                id=str(uuid.uuid4()),
                                tipo="nuevo_bracket",
                                competidor=comps_sorted[i],
                                bracket_origen_id=None,
                                bracket_destino_id=None,
                                competidores_propuestos=nuevo_grupo,
                                score_esperado=round(s, 2),
                                justificacion=f"Nuevo bracket con {comps_sorted[i].nombre} y {comps_sorted[j].nombre}",
                                limites_usados=limits,
                                nivel_relajacion=nivel
                            ))
        
        return recomendaciones
    
    def aplicar_recomendacion(
        self,
        recomendacion: Recomendacion,
        brackets: List[Bracket],
        unpaired: List[Competidor],
        usuario: str = "colaborador"
    ) -> Tuple[List[Bracket], List[Competidor]]:
        
        if recomendacion.tipo == "integracion":
            for i, b in enumerate(brackets):
                if b.id == recomendacion.bracket_destino_id:
                    nuevos_comps = list(b.competidores) + [recomendacion.competidor]
                    s, bd, _ = _calcular_bracket_score(nuevos_comps, recomendacion.limites_usados)
                    brackets[i] = Bracket(
                        id=b.id,
                        numero=b.numero,
                        area=b.area,
                        competidores=nuevos_comps,
                        tipo="manual",
                        score=round(s, 2),
                        score_breakdown=ScoreBreakdown(**bd),
                        nivel_aprobacion="rojo_oscuro",
                        requiere_aprobacion=True,
                        aprobador_requerido=usuario,
                        ronda_origen="manual_integracion",
                        failure_reasons=[]
                    )
                    break
            unpaired = [u for u in unpaired if u.id != recomendacion.competidor.id]
        
        elif recomendacion.tipo == "division":
            for i, b in enumerate(brackets):
                if b.id == recomendacion.bracket_origen_id:
                    competidores = recomendacion.competidores_propuestos
                    grupo1 = competidores[:3]
                    grupo2 = competidores[3:]
                    
                    s1, bd1, _ = _calcular_bracket_score(grupo1, recomendacion.limites_usados)
                    s2, bd2, _ = _calcular_bracket_score(grupo2, recomendacion.limites_usados)
                    
                    new_id1 = b.id
                    new_id2 = max((br.id for br in brackets), default=0) + 1
                    
                    brackets[i] = Bracket(
                        id=new_id1,
                        numero=b.numero,
                        area=b.area,
                        competidores=grupo1,
                        tipo="manual",
                        score=round(s1, 2),
                        score_breakdown=ScoreBreakdown(**bd1),
                        nivel_aprobacion="rojo_oscuro",
                        requiere_aprobacion=True,
                        aprobador_requerido=usuario,
                        ronda_origen="manual_division",
                        failure_reasons=[]
                    )
                    
                    brackets.append(Bracket(
                        id=new_id2,
                        numero=0,
                        area=0,
                        competidores=grupo2,
                        tipo="manual",
                        score=round(s2, 2),
                        score_breakdown=ScoreBreakdown(**bd2),
                        nivel_aprobacion="rojo_oscuro",
                        requiere_aprobacion=True,
                        aprobador_requerido=usuario,
                        ronda_origen="manual_division",
                        failure_reasons=[]
                    ))
                    break
            unpaired = [u for u in unpaired if u.id != recomendacion.competidor.id]
        
        elif recomendacion.tipo == "nuevo_bracket":
            new_id = max((b.id for b in brackets), default=0) + 1
            nuevos_comps = recomendacion.competidores_propuestos
            s, bd, _ = _calcular_bracket_score(nuevos_comps, recomendacion.limites_usados)
            
            brackets.append(Bracket(
                id=new_id,
                numero=0,
                area=0,
                competidores=nuevos_comps,
                tipo="manual",
                score=round(s, 2),
                score_breakdown=ScoreBreakdown(**bd),
                nivel_aprobacion="rojo_oscuro",
                requiere_aprobacion=True,
                aprobador_requerido=usuario,
                ronda_origen="manual_nuevo",
                failure_reasons=[]
            ))
            
            nuevos_ids = {c.id for c in nuevos_comps}
            unpaired = [u for u in unpaired if u.id not in nuevos_ids]
        
        action = ActionRecord(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            tipo=f"apply_{recomendacion.tipo}",
            competidor_id=recomendacion.competidor.id,
            bracket_origen_id=recomendacion.bracket_origen_id,
            bracket_destino_id=recomendacion.bracket_destino_id,
            competidores_ids=[c.id for c in recomendacion.competidores_propuestos],
            usuario=usuario,
            justificacion=recomendacion.justificacion
        )
        self.historial.append(action)
        
        return brackets, unpaired
    
    def asignacion_manual(
        self,
        competidor: Competidor,
        bracket: Bracket,
        brackets: List[Bracket],
        unpaired: List[Competidor],
        usuario: str = "colaborador"
    ) -> Tuple[List[Bracket], List[Competidor]]:
        
        for i, b in enumerate(brackets):
            if b.id == bracket.id:
                nuevos_comps = list(b.competidores) + [competidor]
                s, bd, _ = _calcular_bracket_score(nuevos_comps, {"peso": 7.0, "edad": 3.0, "estatura": 16})
                brackets[i] = Bracket(
                    id=b.id,
                    numero=b.numero,
                    area=b.area,
                    competidores=nuevos_comps,
                    tipo="manual",
                    score=round(s, 2),
                    score_breakdown=ScoreBreakdown(**bd),
                    nivel_aprobacion="rojo_oscuro",
                    requiere_aprobacion=True,
                    aprobador_requerido=usuario,
                    ronda_origen="manual_assign",
                    failure_reasons=[]
                )
                break
        
        unpaired = [u for u in unpaired if u.id != competidor.id]
        
        action = ActionRecord(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            tipo="manual_assign",
            competidor_id=competidor.id,
            bracket_origen_id=None,
            bracket_destino_id=bracket.id,
            competidores_ids=[c.id for c in nuevos_comps],
            usuario=usuario,
            justificacion="Asignación manual por colaborador"
        )
        self.historial.append(action)
        
        return brackets, unpaired
    
    def deshacer_ultima(self) -> Optional[ActionRecord]:
        if not self.historial:
            return None
        
        for action in reversed(self.historial):
            if not action.reversed:
                action.reversed = True
                return action
        return None
    
    def obtener_historial(self) -> List[ActionRecord]:
        return self.historial


def _validar_grupo(competidores: List[Competidor], limits: Dict) -> bool:
    if len(competidores) < 2:
        return True
    
    sexos = set(c.sexo for c in competidores)
    if len(sexos) > 1:
        return False
    
    bloques = set(c.bloque for c in competidores)
    if len(bloques) > 1:
        return False
    
    categorias = set(c.categoria_edad for c in competidores)
    if len(categorias) > 1:
        return False
    
    for i in range(len(competidores)):
        for j in range(i + 1, len(competidores)):
            puede, _ = puede_emparejarse(competidores[i], competidores[j], limits)
            if not puede:
                return False
    
    return True


def _es_homogeneo_amplio(competidores: List[Competidor]) -> bool:
    if len(competidores) < 2:
        return True
    pesos = [c.peso_kg for c in competidores]
    edades = [c.edad for c in competidores]
    estaturas = [c.estatura_cm for c in competidores]
    return (max(pesos) - min(pesos)) / 2 < 2.0 and max(edades) - min(edades) < 1 and (max(estaturas) - min(estaturas)) / 2 < 4


recommendation_manager = RecomendacionManager()