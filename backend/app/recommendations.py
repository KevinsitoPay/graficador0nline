from typing import List, Dict, Tuple, Optional
from datetime import datetime
import uuid

from app.models import (
    Competidor,
    Bracket,
    ScoreBreakdown,
    Recomendacion,
    ActionRecord,
)
from app.algorithm import (
    RELAX_LEVELS,
    puede_grupo,
    calcular_bracket_score,
)

class RecomendacionManager:
    def __init__(self):
        self.historial: List[ActionRecord] = []

    def _limits_from_nivel(self, nivel: int) -> Dict:
        config = RELAX_LEVELS[nivel - 1]
        return {
            "peso": config["peso"],
            "edad_inf": config["edad_inf"],
            "edad_adulto": config["edad_adulto"],
            "estatura": config["estatura"],
        }

    def _score_min_for_size(self, nivel: int, size: int) -> float:
        config = RELAX_LEVELS[nivel - 1]
        if size == 4:
            return config["score_min_cuarteto"]
        if size == 3:
            return config["score_min_trio"]
        return config["score_min_par"]

    def generar_recomendaciones(
        self,
        unpaired: List[Competidor],
        brackets: List[Bracket]
    ) -> List[Recomendacion]:
        recomendaciones: List[Recomendacion] = []

        # PRIORIDAD 1: completar 3 -> 4
        for competidor in unpaired:
            recomendaciones.extend(self.sugerir_integracion(competidor, brackets, target_size=4))

        # PRIORIDAD 2: completar 2 -> 3
        for competidor in unpaired:
            recomendaciones.extend(self.sugerir_integracion(competidor, brackets, target_size=3))

        # PRIORIDAD 3: formar nuevos brackets 4
        recomendaciones.extend(self.sugerir_nuevo_bracket(unpaired, target_size=4))

        # PRIORIDAD 4: formar nuevos brackets 3
        recomendaciones.extend(self.sugerir_nuevo_bracket(unpaired, target_size=3))

        # PRIORIDAD 5: pares solo al final
        recomendaciones.extend(self.sugerir_nuevo_bracket(unpaired, target_size=2))

        recomendaciones.sort(
            key=lambda r: (
                len(r.competidores_propuestos),
                r.score_esperado,
                -r.nivel_relajacion
            ),
            reverse=True
        )

        # Evitar recomendaciones duplicadas exactas
        seen = set()
        filtradas = []
        for r in recomendaciones:
            ids = tuple(sorted(c.id for c in r.competidores_propuestos))
            key = (r.tipo, ids)
            if key in seen:
                continue
            seen.add(key)
            filtradas.append(r)

        return filtradas

    def sugerir_integracion(
        self,
        competidor: Competidor,
        brackets: List[Bracket],
        target_size: int
    ) -> List[Recomendacion]:
        recomendaciones = []

        for nivel in range(1, 8):
            limits = self._limits_from_nivel(nivel)

            for bracket in brackets:
                if len(bracket.competidores) != target_size - 1:
                    continue

                nuevos_comps = list(bracket.competidores) + [competidor]

                ok, _ = puede_grupo(nuevos_comps, limits, nivel)
                if not ok:
                    continue

                s, bd, _ = calcular_bracket_score(nuevos_comps, limits, nivel)
                score_min = self._score_min_for_size(nivel, target_size)

                if s >= score_min:
                    recomendaciones.append(Recomendacion(
                        id=str(uuid.uuid4()),
                        tipo="integracion",
                        competidor=competidor,
                        bracket_origen_id=None,
                        bracket_destino_id=bracket.id,
                        competidores_propuestos=nuevos_comps,
                        score_esperado=round(s, 2),
                        justificacion=f"Integrar a bracket #{bracket.id} para completar grupo de {target_size}",
                        limites_usados=limits,
                        nivel_relajacion=nivel
                    ))

        return recomendaciones

    def sugerir_nuevo_bracket(
        self,
        competidores_sin_rival: List[Competidor],
        target_size: int
    ) -> List[Recomendacion]:
        recomendaciones = []

        if len(competidores_sin_rival) < target_size:
            return recomendaciones

        from itertools import combinations

        for nivel in range(1, 8):
            limits = self._limits_from_nivel(nivel)
            score_min = self._score_min_for_size(nivel, target_size)

            grupos_por_pool: Dict[Tuple, List[Competidor]] = {}
            for c in competidores_sin_rival:
                key = (c.bloque, c.categoria_edad, c.sexo, c.cinta_block)
                grupos_por_pool.setdefault(key, []).append(c)

            for _, comps in grupos_por_pool.items():
                if len(comps) < target_size:
                    continue

                comps = sorted(comps, key=lambda c: (c.peso_kg, c.edad))
                window = 10 if target_size == 4 else 8 if target_size == 3 else 6

                seen = set()
                for i in range(len(comps)):
                    local = comps[i:min(i + window, len(comps))]
                    if len(local) < target_size:
                        continue

                    for subset in combinations(local, target_size):
                        ids = tuple(sorted(c.id for c in subset))
                        if ids in seen:
                            continue
                        seen.add(ids)

                        grupo = list(subset)
                        ok, _ = puede_grupo(grupo, limits, nivel)
                        if not ok:
                            continue

                        s, bd, _ = calcular_bracket_score(grupo, limits, nivel)
                        if s < score_min:
                            continue

                        recomendaciones.append(Recomendacion(
                            id=str(uuid.uuid4()),
                            tipo="nuevo_bracket",
                            competidor=grupo[0],
                            bracket_origen_id=None,
                            bracket_destino_id=None,
                            competidores_propuestos=grupo,
                            score_esperado=round(s, 2),
                            justificacion=f"Formar nuevo bracket de {target_size} competidores",
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
                    s, bd, _ = calcular_bracket_score(
                        nuevos_comps,
                        recomendacion.limites_usados,
                        recomendacion.nivel_relajacion
                    )

                    brackets[i] = Bracket(
                        id=b.id,
                        numero=b.numero,
                        area=b.area,
                        competidores=nuevos_comps,
                        tipo="manual",
                        score=round(s, 2),
                        score_breakdown=ScoreBreakdown(**bd),
                        nivel_aprobacion="rojo",
                        requiere_aprobacion=True,
                        aprobador_requerido=usuario,
                        ronda_origen="manual_integracion",
                        failure_reasons=[]
                    )
                    break

            unpaired = [u for u in unpaired if u.id != recomendacion.competidor.id]

        elif recomendacion.tipo == "nuevo_bracket":
            new_id = max((b.id for b in brackets), default=0) + 1
            nuevos_comps = recomendacion.competidores_propuestos

            s, bd, _ = calcular_bracket_score(
                nuevos_comps,
                recomendacion.limites_usados,
                recomendacion.nivel_relajacion
            )

            brackets.append(Bracket(
                id=new_id,
                numero=0,
                area=0,
                competidores=nuevos_comps,
                tipo="manual",
                score=round(s, 2),
                score_breakdown=ScoreBreakdown(**bd),
                nivel_aprobacion="rojo",
                requiere_aprobacion=True,
                aprobador_requerido=usuario,
                ronda_origen="manual_nuevo",
                failure_reasons=[]
            ))

            usados = {c.id for c in nuevos_comps}
            unpaired = [u for u in unpaired if u.id not in usados]

        action = ActionRecord(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            tipo=f"apply_{recomendacion.tipo}",
            competidor_id=recomendacion.competidor.id,
            bracket_origen_id=recomendacion.bracket_origen_id,
            bracket_destino_id=recomendacion.bracket_destino_id,
            competidores_ids=[c.id for c in recomendacion.competidores_propuestos],
            usuario=usuario,
            justificacion=recomendacion.justificacion,
            reversed=False
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
                nivel = 7
                limits = self._limits_from_nivel(nivel)
                s, bd, _ = calcular_bracket_score(nuevos_comps, limits, nivel)

                brackets[i] = Bracket(
                    id=b.id,
                    numero=b.numero,
                    area=b.area,
                    competidores=nuevos_comps,
                    tipo="manual",
                    score=round(s, 2),
                    score_breakdown=ScoreBreakdown(**bd),
                    nivel_aprobacion="rojo",
                    requiere_aprobacion=True,
                    aprobador_requerido=usuario,
                    ronda_origen="manual_assign",
                    failure_reasons=[]
                )
                break

        unpaired = [u for u in unpaired if u.id != competidor.id]

        action = ActionRecord(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            tipo="manual_assign",
            competidor_id=competidor.id,
            bracket_origen_id=None,
            bracket_destino_id=bracket.id,
            competidores_ids=[c.id for c in nuevos_comps],
            usuario=usuario,
            justificacion="Asignación manual por colaborador",
            reversed=False
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

recommendation_manager = RecomendacionManager()
