from typing import List, Dict, Tuple, Optional
from app.models import Competidor, Bracket, BlockStats, GlobalStats, Unpaired, Results, ScoreBreakdown

def compute_peso_score(peso_i: float, peso_j: float) -> float:
    diff = abs(peso_i - peso_j)
    return max(0, 1 - diff / 5.0)

def compute_estatura_score(est_i: float, est_j: float) -> float:
    diff = abs(est_i - est_j)
    return max(0, 1 - diff / 10.0)

def get_estatura_hard_limit(categoria: str) -> float:
    """Get maximum allowed height difference before rejecting pair"""
    if categoria == "preescolar":
        return 5.0
    elif categoria == "infantil":
        return 14.0
    else:
        return 20.0

def get_peso_hard_limit() -> float:
    """Maximum allowed weight difference before rejecting pair (5kg for all)"""
    return 5.0

def compute_edad_score(edad_i: int, edad_j: int, bloque: str = "") -> float:
    diff = abs(edad_i - edad_j)
    
    # Preescolar (3-5): strict exact age matching only
    if edad_i <= 5 and edad_j <= 5:
        if diff == 0:
            return 1.0
        return 0  # No compatibility if age differs
    
    # Get age categories
    categoria_i = get_edad_category(edad_i)
    categoria_j = get_edad_category(edad_j)
    
    # If different main categories, no compatibility
    if categoria_i != categoria_j:
        return 0
    
    # INFANTIL (6-13): HARD LIMIT - max 2 years difference
    if categoria_i == "infantil":
        if diff > 2:
            return 0  # Reject if more than 2 years apart
        if diff <= 1:
            return 1.0
        return max(0, 1 - (diff - 1) / 2)  # 2 years = 0.5
    
    # Adults (CADETE through MASTER): softer scoring, prefer closer ages
    # But allow wider range with good score reduction
    if diff <= 2:
        return 1.0
    elif diff <= 5:
        return 0.7
    elif diff <= 10:
        return 0.4
    elif diff <= 15:
        return 0.2
    else:
        return 0

def get_edad_category(edad: int) -> str:
    """Get age category for grouping in brackets"""
    if edad <= 5:  # Preescolar: 3, 4, 5 years
        return "preescolar"
    elif edad <= 13:  # Infantil: 6 to 13 years
        return "infantil"
    elif edad <= 15:  # Cadete: 14, 15 years
        return "cadete"
    elif edad <= 17:  # Juvenil: 16, 17 years
        return "juvenil"
    elif edad <= 29:  # Adulto: 18 to 29 years
        return "adulto"
    elif edad <= 45:  # Submaster: 30 to 45 years
        return "submaster"
    else:  # Master: 46+ years
        return "master"

def check_modalidad_compatible(modalidad_i: str, modalidad_j: str) -> bool:
    """Check if modalities can be paired in a bracket of 2"""
    # For brackets of 2 - exact match required
    # POOMSAE + POOMSAE ✅
    # COMBATE + COMBATE ✅
    # DOUBLE + DOUBLE ✅
    # Anything else ❌
    
    if modalidad_i == "Poomsae" and modalidad_j == "Poomsae":
        return True
    if modalidad_i == "Combate" and modalidad_j == "Combate":
        return True
    if modalidad_i == "Doble" and modalidad_j == "Doble":
        return True
    
    return False


def validate_bracket_modalidades(modalidades: list) -> bool:
    """Validate modalidad composition for brackets of 3 or 4"""
    if len(modalidades) < 3:
        return True
    
    count_poomsae = modalidades.count("Poomsae")
    count_combate = modalidades.count("Combate")
    count_doble = modalidades.count("Doble")
    
    # Bracket of 3: 1 POOMSAE + 2 DOUBLE, 1 COMBATE + 2 DOUBLE, or 3 DOUBLE
    if len(modalidades) == 3:
        if count_doble == 3:
            return True  # 3 DOUBLE ✅
        if count_doble == 2:
            if count_poomsae == 1:  # 1 POOMSAE + 2 DOUBLE ✅
                return True
            if count_combate == 1:  # 1 COMBATE + 2 DOUBLE ✅
                return True
        return False
    
    # Bracket of 4
    if count_doble == 4:
        return True  # 4 DOUBLE ✅
    if count_doble == 3 and count_poomsae == 1:
        return True  # 1 POOMSAE + 3 DOUBLE ✅
    if count_doble == 2:
        if count_poomsae == 2:  # 2 POOMSAE + 2 DOUBLE ✅
            return True
        if count_combate == 2:  # 2 COMBATE + 2 DOUBLE ✅
            return True
    
    return False

def compute_compatibility(comp_i: Competidor, comp_j: Competidor) -> float:
    details = compute_compatibility_details(comp_i, comp_j)
    return details["total"]


def compute_compatibility_details(comp_i: Competidor, comp_j: Competidor) -> dict:
    modalidad_ok = check_modalidad_compatible(comp_i.modalidad, comp_j.modalidad)
    
    if not modalidad_ok:
        return {
            "modalidad_ok": False,
            "edad_diff": abs(comp_i.edad - comp_j.edad),
            "edad_score": 0,
            "peso_diff": round(abs(comp_i.peso_kg - comp_j.peso_kg), 2),
            "peso_score": 0,
            "estatura_diff": abs(comp_i.estatura_cm - comp_j.estatura_cm),
            "estatura_score": 0,
            "doyang_bonus": 0,
            "total": 0
        }
    
    edad_diff = abs(comp_i.edad - comp_j.edad)
    edad_score = compute_edad_score(comp_i.edad, comp_j.edad, comp_i.bloque)
    if edad_score == 0:
        return {
            "modalidad_ok": True,
            "edad_diff": edad_diff,
            "edad_score": 0,
            "peso_diff": round(abs(comp_i.peso_kg - comp_j.peso_kg), 2),
            "peso_score": 0,
            "estatura_diff": abs(comp_i.estatura_cm - comp_j.estatura_cm),
            "estatura_score": 0,
            "doyang_bonus": 0,
            "total": 0
        }
    
    estatura_diff = abs(comp_i.estatura_cm - comp_j.estatura_cm)
    categoria = get_edad_category(comp_i.edad)
    
    peso_diff = abs(comp_i.peso_kg - comp_j.peso_kg)
    peso_hard_limit = get_peso_hard_limit()
    
    if peso_diff > peso_hard_limit:
        return {
            "modalidad_ok": True,
            "edad_diff": edad_diff,
            "edad_score": round(edad_score, 2),
            "peso_diff": round(peso_diff, 2),
            "peso_score": 0,
            "estatura_diff": estatura_diff,
            "estatura_score": 0,
            "doyang_bonus": 0,
            "total": 0
        }
    
    estatura_hard_limit = get_estatura_hard_limit(categoria)
    
    if estatura_diff > estatura_hard_limit:
        return {
            "modalidad_ok": True,
            "edad_diff": edad_diff,
            "edad_score": round(edad_score, 2),
            "peso_diff": round(peso_diff, 2),
            "peso_score": round(max(0, 1 - peso_diff / 5.0) * 0.5, 2),
            "estatura_diff": estatura_diff,
            "estatura_score": 0,
            "doyang_bonus": 0,
            "total": 0
        }
    
    peso_score_raw = max(0, 1 - peso_diff / 5.0)
    peso_score = peso_score_raw * 0.5
    
    estatura_score_raw = max(0, 1 - estatura_diff / 10.0)
    estatura_score = estatura_score_raw * 0.2
    
    doyang_bonus = 0.2 if comp_i.doyang != comp_j.doyang else 0
    
    total = peso_score + estatura_score + edad_score + doyang_bonus
    
    return {
        "modalidad_ok": True,
        "edad_diff": edad_diff,
        "edad_score": round(edad_score, 2),
        "peso_diff": round(peso_diff, 2),
        "peso_score": round(peso_score, 2),
        "estatura_diff": estatura_diff,
        "estatura_score": round(estatura_score, 2),
        "doyang_bonus": doyang_bonus,
        "total": round(total, 2)
    }


def get_bracket_modalidades(bracket_members):
    """Get list of modalidades in a bracket"""
    return [c.modalidad for c in bracket_members]

def group_by_sex_cinta(competitors: List[Competidor]) -> Dict[Tuple[str, str], List[Competidor]]:
    groups = {}
    for comp in competitors:
        key = (comp.sexo, comp.cinta_block)
        if key not in groups:
            groups[key] = []
        groups[key].append(comp)
    return groups

def check_bracket_height_compatible(new_comp, existing_bracket, max_diff=10):
    """Check if new competitor fits height threshold with existing bracket members"""
    if not existing_bracket:
        return True
    
    heights = [c.estatura_cm for c in existing_bracket]
    heights.append(new_comp.estatura_cm)
    
    height_range = max(heights) - min(heights)
    return height_range <= max_diff

def check_bracket_weight_compatible(new_comp, existing_bracket, max_diff=5):
    """Check if new competitor fits weight threshold with existing bracket members"""
    if not existing_bracket:
        return True
    
    weights = [c.peso_kg for c in existing_bracket]
    weights.append(new_comp.peso_kg)
    
    weight_range = max(weights) - min(weights)
    return weight_range <= max_diff

def etapa1_filter(groups: Dict[Tuple[str, str], List[Competidor]]) -> Tuple[List[Competidor], List[Unpaired]]:
    paired = []
    unpaired = []
    
    for key, comps in groups.items():
        if len(comps) >= 2:
            paired.extend(comps)
        else:
            for comp in comps:
                unpaired.append(Unpaired(
                    competidor=comp,
                    razon="No rival in same sex & cinta block"
                ))
    
    return paired, unpaired

def etapa2_pair(competitors: List[Competidor]) -> Tuple[List[Bracket], List[Competidor]]:
    if len(competitors) < 2:
        return [], competitors
    
    competitors = sorted(competitors, key=lambda c: c.edad)
    available = list(competitors)
    brackets = []
    bracket_id = 1
    
    while len(available) >= 2:
        best_score = -1
        best_pair = None
        best_idx = None
        
        for i in range(len(available)):
            for j in range(i + 1, len(available)):
                score = compute_compatibility(available[i], available[j])
                if score > best_score:
                    best_score = score
                    best_pair = (i, j)
        
        if best_pair is None or best_score <= 0:
            break
        
        i, j = best_pair
        comp1 = available[i]
        comp2 = available[j]
        
        current_bracket = [comp1, comp2]
        remaining = [available[k] for k in range(len(available)) if k != i and k != j]
        
        while remaining and len(current_bracket) < 4:
            best_third = None
            best_avg = 0
            
            for idx, comp in enumerate(remaining):
                # FIRST check height range compatibility for the group
                if not check_bracket_height_compatible(comp, current_bracket, max_diff=10):
                    continue
                if not check_bracket_weight_compatible(comp, current_bracket, max_diff=5):
                    continue
                
                scores = [compute_compatibility(c, comp) for c in current_bracket]
                avg = sum(scores) / len(scores)
                
                if len(current_bracket) == 2 and avg >= 0.6:
                    if avg > best_avg:
                        best_avg = avg
                        best_third = idx
                elif len(current_bracket) == 3 and avg >= 0.5:
                    if avg > best_avg:
                        best_avg = avg
                        best_third = idx
            
            if best_third is not None:
                current_bracket.append(remaining.pop(best_third))
                # Validate modalidad composition for bracket of 3 or 4
                if len(current_bracket) >= 3:
                    modalidades = [c.modalidad for c in current_bracket]
                    if not validate_bracket_modalidades(modalidades):
                        # Remove the added competitor - invalid modality composition
                        removed = current_bracket.pop()
                        remaining.append(removed)
                        break
            else:
                break
        
        bracket_score = sum(compute_compatibility(c1, c2) for c1, c2 in zip(current_bracket, current_bracket[1:])) / (len(current_bracket) - 1) if len(current_bracket) > 1 else best_score
        
        all_details = []
        for c1, c2 in zip(current_bracket, current_bracket[1:]):
            details = compute_compatibility_details(c1, c2)
            all_details.append(details)
        
        if all_details:
            avg_breakdown = {
                "modalidad_ok": all_details[0]["modalidad_ok"],
                "edad_diff": int(sum(d["edad_diff"] for d in all_details) / len(all_details)),
                "edad_score": round(sum(d["edad_score"] for d in all_details) / len(all_details), 2),
                "peso_diff": round(sum(d["peso_diff"] for d in all_details) / len(all_details), 2),
                "peso_score": round(sum(d["peso_score"] for d in all_details) / len(all_details), 2),
                "estatura_diff": int(sum(d["estatura_diff"] for d in all_details) / len(all_details)),
                "estatura_score": round(sum(d["estatura_score"] for d in all_details) / len(all_details), 2),
                "doyang_bonus": round(sum(d["doyang_bonus"] for d in all_details) / len(all_details), 2),
                "total": round(sum(d["total"] for d in all_details) / len(all_details), 2)
            }
            score_breakdown = ScoreBreakdown(**avg_breakdown)
        else:
            score_breakdown = None
        
        bracket = Bracket(
            id=bracket_id,
            numero=bracket_id,
            area=((bracket_id - 1) % 12) + 1,
            competidores=current_bracket,
            tipo="normal",
            score=round(bracket_score, 2),
            score_breakdown=score_breakdown
        )
        brackets.append(bracket)
        bracket_id += 1
        
        available = remaining
    
    return brackets, available

def etapa3_relaxed_pair(competitors: List[Competidor]) -> Tuple[List[Bracket], List[Competidor]]:
    if len(competitors) < 2:
        return [], competitors
    
    all_brackets = []
    all_unpaired = []
    bracket_id = 1
    
    cinta_groups = {}
    for comp in competitors:
        key = (comp.sexo, comp.cinta_block)
        if key not in cinta_groups:
            cinta_groups[key] = []
        cinta_groups[key].append(comp)
    
    for key, comps in cinta_groups.items():
        if len(comps) < 2:
            for comp in comps:
                all_unpaired.append(comp)
            continue
        
        comps_sorted = sorted(comps, key=lambda c: c.edad)
        available = list(comps_sorted)
        
        while len(available) >= 2:
            paired = None
            
            for ronda in ["ronda1", "ronda2"]:
                if paired:
                    break
                
                for i in range(len(available)):
                    for j in range(i + 1, len(available)):
                        c1, c2 = available[i], available[j]
                        
                        if c1.cinta_block != c2.cinta_block:
                            continue
                        
                        edad_diff = abs(c1.edad - c2.edad)
                        
                        if ronda == "ronda1":
                            if edad_diff > 2:
                                continue
                            peso_diff = abs(c1.peso_kg - c2.peso_kg)
                            est_diff = abs(c1.estatura_cm - c2.estatura_cm)
                            if peso_diff > 5 or est_diff > 10:
                                continue
                            score = compute_compatibility(c1, c2)
                            if score >= 0.5:
                                paired = (i, j, "relaxed_age", score)
                        else:
                            max_edad = 3 if c1.edad >= 15 or c2.edad >= 15 else 2
                            if edad_diff > max_edad:
                                continue
                            peso_diff = abs(c1.peso_kg - c2.peso_kg)
                            est_diff = abs(c1.estatura_cm - c2.estatura_cm)
                            if peso_diff > 6 or est_diff > 12:
                                continue
                            score = compute_compatibility(c1, c2)
                            if score >= 0.4:
                                paired = (i, j, "relaxed_limits", score)
            
            if paired:
                i, j, tipo, score = paired
                c1, c2 = available[i], available[j]
                details = compute_compatibility_details(c1, c2)
                score_breakdown = ScoreBreakdown(**details)
                
                bracket = Bracket(
                    id=bracket_id,
                    numero=bracket_id,
                    area=((bracket_id - 1) % 12) + 1,
                    competidores=[available[i], available[j]],
                    tipo=tipo,
                    score=round(score, 2),
                    score_breakdown=score_breakdown
                )
                all_brackets.append(bracket)
                bracket_id += 1
                
                available = [c for idx, c in enumerate(available) if idx != i and idx != j]
            else:
                break
        
        for comp in available:
            all_unpaired.append(comp)
    
    return all_brackets, all_unpaired

def assign_competitor_numbers(brackets: List[Bracket], block: str) -> None:
    prefixes = {
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
    prefix = prefixes.get(block, "XX")
    
    count = 1
    for bracket in brackets:
        for comp in bracket.competidores:
            comp.numero_competidor = f"{prefix} {count}"
            count += 1

def process_block(block: str, competitors: List[Competidor]) -> Tuple[List[Bracket], List[Unpaired]]:
    groups = group_by_sex_cinta(competitors)
    paired, unpaired_etapa1 = etapa1_filter(groups)
    
    brackets_etapa2, remaining_etapa2 = etapa2_pair(paired)
    
    brackets_etapa3, remaining_etapa3 = etapa3_relaxed_pair(remaining_etapa2)
    
    all_brackets = brackets_etapa2 + brackets_etapa3
    
    for bracket in all_brackets:
        assign_competitor_numbers([bracket], block)
    
    unpaired = unpaired_etapa1.copy()
    for comp in remaining_etapa3:
        unpaired.append(Unpaired(
            competidor=comp,
            razon="No compatible partner after Etapa 3"
        ))
    
    return all_brackets, unpaired

def generate_results(competitors: List[Competidor]) -> Results:
    block_competitors = {}
    for comp in competitors:
        if comp.bloque not in block_competitors:
            block_competitors[comp.bloque] = []
        block_competitors[comp.bloque].append(comp)
    
    all_brackets = []
    all_unpaired = []
    
    for block, comps in block_competitors.items():
        brackets, unpaired = process_block(block, comps)
        all_brackets.extend(brackets)
        all_unpaired.extend(unpaired)
    
    total_compet = len(competitors)
    total_brackets = len(all_brackets)
    avg_size = total_compet / total_brackets if total_brackets > 0 else 0
    
    brackets_2 = sum(1 for b in all_brackets if len(b.competidores) == 2)
    brackets_3 = sum(1 for b in all_brackets if len(b.competidores) == 3)
    brackets_4 = sum(1 for b in all_brackets if len(b.competidores) == 4)
    
    excellent = sum(1 for b in all_brackets if b.score >= 0.7)
    low_quality = sum(1 for b in all_brackets if b.score < 0.5)
    
    global_stats = GlobalStats(
        total_competidores=total_compet,
        total_brackets=total_brackets,
        avg_bracket_size=round(avg_size, 2),
        brackets_2=brackets_2,
        brackets_3=brackets_3,
        brackets_4=brackets_4,
        sin_rival_total=len(all_unpaired),
        excellent_brackets=excellent,
        low_quality_brackets=low_quality
    )
    
    block_stats = []
    for block, comps in block_competitors.items():
        brackets = [b for b in all_brackets if b.competidores[0].bloque == block]
        unpaired = [u for u in all_unpaired if u.competidor.bloque == block]
        relaxed = sum(1 for b in brackets if b.tipo != "normal")
        
        avg = len(comps) / len(brackets) if brackets else 0
        block_stats.append(BlockStats(
            bloque=block,
            competidores=len(comps),
            brackets=len(brackets),
            avg_size=round(avg, 2),
            sin_rival=len(unpaired),
            relaxed_count=relaxed
        ))
    
    return Results(
        global_stats=global_stats,
        block_stats=block_stats,
        brackets=all_brackets,
        unpaired=all_unpaired
    )