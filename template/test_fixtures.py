import random
import xlsxwriter
from pathlib import Path

BASE_BLOCKS = [
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

SCHOOLS = [
    "MDK FLORIDO",
    "MDK CASA BLANCA",
    "MDK EL DORADO",
    "KUK SUL",
    "CHAMPIONS",
    "TAEKWONDO PLUS",
    "OLIMPICO",
    "VICTORY",
    "KORYO",
    "PAQUI",
]

FIRST_NAMES_M = [
    "JESUS", "DAMIAN", "ALEX", "DIEGO", "MIGUEL", "LUIS", "CARLOS", "JUAN", "PEDRO", "GABRIEL",
    "ADRIAN", "BRANDON", "KEVIN", "JOSE", "ANGEL", "DANIEL", "ESTEBAN", "IVAN", "OSCAR", "RAUL",
]

FIRST_NAMES_F = [
    "SOFIA", "MARIA", "CAMILA", "VALENTINA", "LUCIA", "PAULA", "ANA", "LAURA", "KARLA", "GABRIELA",
    "ADRIANA", "MONSERRAT", "DANIELA", "ALEXANDRA", "ELIZABETH", "PATRICIA", "ANGELICA", "VERONICA", "DIANA", "LIZBETH",
]

LAST_NAMES = [
    "LOPEZ", "GARCIA", "MARTINEZ", "RODRIGUEZ", "HERNANDEZ", "PEREZ", "SANCHEZ", "RAMIREZ", "TORRES", "FLORES",
    "RIVERA", "GOMEZ", "DIAZ", "REYES", "MORALES", "CRUZ", "ORTIZ", "GUTIERREZ", "CHAVEZ", "RAMOS",
]

GRADOS = {
    "Adultos Grupo 1": [("1er Dan", 0.5), ("2do Dan", 0.3), ("3er Dan", 0.2)],
    "Adultos Grupo 2": [("1er Dan", 0.4), ("2do Dan", 0.4), ("3er Dan", 0.2)],
    "Infantil Azul": [("7 KUP", 0.4), ("6 KUP", 0.3), ("5 KUP", 0.3)],
    "Infantil Verde": [("8 KUP", 0.4), ("7 KUP", 0.3), ("6 KUP", 0.3)],
    "Infantil Amarilla": [("9 KUP", 0.4), ("8 KUP", 0.3), ("7 KUP", 0.3)],
    "Infantil Blanca": [("10 KUP", 0.5), ("Blanca", 0.5)],
    "Infantil Marrón": [("4 KUP", 0.4), ("3 KUP", 0.6)],
    "Infantil Roja": [("2 KUP", 0.5), ("1 KUP", 0.5)],
    "Infantil Negra": [("1er Poom", 0.5), ("1er Dan", 0.5)],
    "Pre-Taekwondo": [("Pre-Taekwondo", 1.0)],
}

def weighted_choice(choices):
    items, weights = zip(*choices)
    return random.choices(items, weights=weights)[0]

def generate_competitor(block, i, sexo=None):
    edad_min, edad_max = {
        "Adultos Grupo 1": (15, 30),
        "Adultos Grupo 2": (15, 40),
        "Infantil Azul": (10, 14),
        "Infantil Verde": (9, 13),
        "Infantil Amarilla": (8, 12),
        "Infantil Blanca": (6, 10),
        "Infantil Marrón": (8, 13),
        "Infantil Roja": (9, 14),
        "Infantil Negra": (10, 15),
        "Pre-Taekwondo": (5, 7),
    }[block]
    
    peso_min, peso_max = {
        "Adultos Grupo 1": (45, 90),
        "Adultos Grupo 2": (50, 100),
        "Infantil Azul": (30, 60),
        "Infantil Verde": (28, 55),
        "Infantil Amarilla": (25, 50),
        "Infantil Blanca": (20, 40),
        "Infantil Marrón": (28, 55),
        "Infantil Roja": (25, 50),
        "Infantil Negra": (30, 65),
        "Pre-Taekwondo": (15, 30),
    }[block]
    
    return {
        "No": i + 1,
        "Nombre": random.choice(FIRST_NAMES_M if sexo == "H" else FIRST_NAMES_F),
        "Apellido": random.choice(LAST_NAMES),
        "Edad": random.randint(edad_min, edad_max),
        "H/M": sexo or random.choice(["H", "M"]),
        "Grado": weighted_choice(GRADOS[block]),
        "Peso": round(random.uniform(peso_min, peso_max), 2),
        "Estatura": random.randint(peso_min + 80, peso_max + 80),
        "Modalidad": random.choice(["Doble", "Sencillo"]).capitalize(),
        "Doyang": random.choice(SCHOOLS),
    }

def create_excel(filename, blocks_data):
    workbook = xlsxwriter.Workbook(filename)
    
    for block, data in blocks_data.items():
        # Handle both integer count and list of competitors
        if isinstance(data, int):
            count = data
            competitors = [generate_competitor(block, i) for i in range(count)]
        else:
            competitors = data
            count = len(competitors)
        
        worksheet = workbook.add_worksheet(block)
        headers = ["No", "Nombre", "Apellido", "Edad", "H/M", "Grado", "Peso", "Estatura", "Modalidad", "Doyang"]
        
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)
        
        for i, comp in enumerate(competitors):
            for col, header in enumerate(headers):
                worksheet.write(i + 1, col, comp[header])
    
    workbook.close()

# ============= FIXTURE GENERATORS =============

def fix_standard_100(out_dir):
    blocks = {}
    for block in BASE_BLOCKS:
        blocks[block] = [generate_competitor(block, i) for i in range(10)]
    create_excel(out_dir / "standard_100.xlsx", blocks)

def fix_all_males(out_dir):
    blocks = {}
    for block in BASE_BLOCKS[:5]:
        comps = []
        for i in range(10):
            c = generate_competitor(block, i, "H")
            comps.append(c)
        blocks[block] = comps
    create_excel(out_dir / "all_males.xlsx", blocks)

def fix_all_females(out_dir):
    blocks = {}
    for block in BASE_BLOCKS[:5]:
        comps = []
        for i in range(10):
            c = generate_competitor(block, i, "F")
            comps.append(c)
        blocks[block] = comps
    create_excel(out_dir / "all_females.xlsx", blocks)

def fix_same_cinta(out_dir):
    blocks = {"Infantil Marrón": []}
    for i in range(20):
        c = generate_competitor("Infantil Marrón", i)
        c["H/M"] = "H"
        blocks["Infantil Marrón"].append(c)
    create_excel(out_dir / "same_cinta.xlsx", blocks)

def fix_extreme_weights_min(out_dir):
    blocks = {"Infantil Marrón": []}
    for i in range(20):
        c = generate_competitor("Infantil Marrón", i)
        c["Peso"] = 25.0 + (i * 0.5)  # 25-35kg spread
        blocks["Infantil Marrón"].append(c)
    create_excel(out_dir / "extreme_weights_min.xlsx", blocks)

def fix_extreme_weights_max(out_dir):
    blocks = {"Infantil Marrón": []}
    for i in range(20):
        c = generate_competitor("Infantil Marrón", i)
        c["Peso"] = 20.0 + (i * 4)  # 20-100kg spread
        blocks["Infantil Marrón"].append(c)
    create_excel(out_dir / "extreme_weights_max.xlsx", blocks)

def fix_extreme_weights_same(out_dir):
    blocks = {"Infantil Marrón": []}
    for i in range(20):
        c = generate_competitor("Infantil Marrón", i)
        c["Peso"] = 30.0  # All same weight
        blocks["Infantil Marrón"].append(c)
    create_excel(out_dir / "extreme_weights_same.xlsx", blocks)

def fix_same_age(out_dir):
    blocks = {"Infantil Marrón": []}
    for i in range(20):
        c = generate_competitor("Infantil Marrón", i)
        c["Edad"] = 10
        blocks["Infantil Marrón"].append(c)
    create_excel(out_dir / "extreme_ages_same.xlsx", blocks)

def fix_age_diff_1(out_dir):
    blocks = {"Infantil Marrón": []}
    for i in range(20):
        c = generate_competitor("Infantil Marrón", i)
        c["Edad"] = 10 if i % 2 == 0 else 11
        blocks["Infantil Marrón"].append(c)
    create_excel(out_dir / "extreme_ages_diff1.xlsx", blocks)

def fix_age_diff_3(out_dir):
    blocks = {"Infantil Marrón": []}
    for i in range(20):
        c = generate_competitor("Infantil Marrón", i)
        c["Edad"] = 8 + (i % 5)
        blocks["Infantil Marrón"].append(c)
    create_excel(out_dir / "extreme_ages_diff3.xlsx", blocks)

def fix_same_doyang(out_dir):
    blocks = {"Infantil Marrón": []}
    for i in range(20):
        c = generate_competitor("Infantil Marrón", i)
        c["Doyang"] = "MDK FLORIDO"
        blocks["Infantil Marrón"].append(c)
    create_excel(out_dir / "same_doyang.xlsx", blocks)

def fix_different_doyang(out_dir):
    blocks = {"Infantil Marrón": []}
    for i in range(20):
        c = generate_competitor("Infantil Marrón", i)
        c["Doyang"] = SCHOOLS[i % len(SCHOOLS)]
        blocks["Infantil Marrón"].append(c)
    create_excel(out_dir / "different_doyang.xlsx", blocks)

def fix_mix_modalidad(out_dir):
    blocks = {"Infantil Marrón": []}
    for i in range(20):
        c = generate_competitor("Infantil Marrón", i)
        c["Modalidad"] = "Doble" if i % 2 == 0 else "Sencillo"
        blocks["Infantil Marrón"].append(c)
    create_excel(out_dir / "mix_modalidad.xlsx", blocks)

def fix_single_competitor(out_dir):
    blocks = {block: 1 for block in BASE_BLOCKS[:3]}
    create_excel(out_dir / "single_competitor.xlsx", blocks)

def fix_pairs_only(out_dir):
    blocks = {"Infantil Marrón": []}
    for i in range(20):
        c = generate_competitor("Infantil Marrón", i)
        c["Edad"] = 10
        c["Peso"] = 30.0 + (i % 2 * 5)
        c["Estatura"] = 130 + (i % 2 * 10)
        blocks["Infantil Marrón"].append(c)
    create_excel(out_dir / "pairs_only.xlsx", blocks)

def fix_triples_only(out_dir):
    blocks = {"Infantil Marrón": []}
    for i in range(21):
        c = generate_competitor("Infantil Marrón", i)
        c["Edad"] = 10
        c["Peso"] = 30.0 + ((i % 3) * 2)
        c["Estatura"] = 130 + ((i % 3) * 5)
        blocks["Infantil Marrón"].append(c)
    create_excel(out_dir / "triples_only.xlsx", blocks)

def fix_quads_only(out_dir):
    blocks = {"Infantil Marrón": []}
    for i in range(20):
        c = generate_competitor("Infantil Marrón", i)
        c["Edad"] = 10
        c["Peso"] = 30.0 + ((i % 4) * 2)
        c["Estatura"] = 130 + ((i % 4) * 5)
        blocks["Infantil Marrón"].append(c)
    create_excel(out_dir / "quads_only.xlsx", blocks)

def fix_all_infantil(out_dir):
    blocks = {block: 10 for block in BASE_BLOCKS[2:8]}
    create_excel(out_dir / "all_infantil.xlsx", blocks)

def fix_all_adultos(out_dir):
    blocks = {block: 10 for block in BASE_BLOCKS[:2]}
    create_excel(out_dir / "all_adultos.xlsx", blocks)

def fix_mixed_sizes(out_dir):
    blocks = {"Infantil Marrón": []}
    for i in range(50):
        c = generate_competitor("Infantil Marrón", i)
        c["Edad"] = 10
        blocks["Infantil Marrón"].append(c)
    create_excel(out_dir / "mixed_sizes.xlsx", blocks)

def fix_invalid_grado(out_dir):
    blocks = {"Infantil Marrón": []}
    grados_invalidos = ["INVALIDO", "NINGUNO", "?", "", "  ", "X", "0"]
    for i in range(20):
        c = generate_competitor("Infantil Marrón", i)
        c["Grado"] = grados_invalidos[i % len(grados_invalidos)]
        blocks["Infantil Marrón"].append(c)
    create_excel(out_dir / "invalid_grado.xlsx", blocks)

def fix_empty_sheets(out_dir):
    blocks = {
        "Adultos Grupo 1": [],
        "Adultos Grupo 2": [],
        "Infantil Azul": [],
    }
    blocks["Infantil Marrón"] = [generate_competitor("Infantil Marrón", i) for i in range(10)]
    create_excel(out_dir / "empty_sheets.xlsx", blocks)

def fix_weights_decimal(out_dir):
    blocks = {"Infantil Marrón": []}
    for i in range(20):
        c = generate_competitor("Infantil Marrón", i)
        c["Peso"] = round(25.0 + i * 0.37, 2)
        c["Estatura"] = round(120.0 + i * 0.71, 2)
        blocks["Infantil Marrón"].append(c)
    create_excel(out_dir / "weights_decimal.xlsx", blocks)

def fix_special_chars(out_dir):
    blocks = {"Infantil Marrón": []}
    nombres_especiales = ["JESÚS", "DAMIÁN", "ÁNDRES", "ÓSCAR", "ÉRIC", "ÚRSULA", "MARIÁ", "LUCÍA", "NAÑO", "PEÑA"]
    for i in range(20):
        c = generate_competitor("Infantil Marrón", i)
        c["Nombre"] = nombres_especiales[i % len(nombres_especiales)]
        c["Apellido"] = ["GARCÍA", "PÉREZ", "LÓPEZ", "RÍOS", "SÁENZ"][i % 5]
        blocks["Infantil Marrón"].append(c)
    create_excel(out_dir / "special_chars.xlsx", blocks)

def fix_no_rival_perfect(out_dir):
    blocks = {"Infantil Marrón": []}
    for i in range(21):
        c = generate_competitor("Infantil Marrón", i)
        c["Edad"] = 10
        c["Peso"] = 30.0 + (i % 3 * 0.3)
        c["Estatura"] = 130 + (i % 3 * 2)
        c["Doyang"] = SCHOOLS[i % 2]
        blocks["Infantil Marrón"].append(c)
    create_excel(out_dir / "no_rival_perfect.xlsx", blocks)

def fix_worst_case(out_dir):
    blocks = {"Infantil Marrón": []}
    for i in range(20):
        c = generate_competitor("Infantil Marrón", i)
        c["Edad"] = 6 + i
        c["Peso"] = 20.0 + (i * 4)
        c["Estatura"] = 100 + (i * 5)
        c["Doyang"] = f"ESCUELA_{i}"
        blocks["Infantil Marrón"].append(c)
    create_excel(out_dir / "worst_case.xlsx", blocks)

def fix_cross_cinta(out_dir):
    blocks = {"Infantil Verde": [], "Infantil Azul": [], "Infantil Amarilla": []}
    for i in range(10):
        c_verde = generate_competitor("Infantil Verde", i)
        c_verde["Edad"] = 10
        c_verde["Peso"] = 30.0 + (i % 3 * 2)
        c_verde["Estatura"] = 125 + (i % 3 * 5)
        c_verde["Grado"] = "8 KUP"
        blocks["Infantil Verde"].append(c_verde)
        
        c_azul = generate_competitor("Infantil Azul", i)
        c_azul["Edad"] = 12
        c_azul["Peso"] = 35.0 + (i % 3 * 2)
        c_azul["Estatura"] = 140 + (i % 3 * 5)
        c_azul["Grado"] = "7 KUP"
        blocks["Infantil Azul"].append(c_azul)
        
        c_amarilla = generate_competitor("Infantil Amarilla", i)
        c_amarilla["Edad"] = 9
        c_amarilla["Peso"] = 28.0 + (i % 3 * 2)
        c_amarilla["Estatura"] = 120 + (i % 3 * 5)
        c_amarilla["Grado"] = "9 KUP"
        blocks["Infantil Amarilla"].append(c_amarilla)
    create_excel(out_dir / "cross_cinta.xlsx", blocks)

def fix_edge_grados(out_dir):
    blocks = {"Infantil Verde": []}
    grados_variantes = ["VERDE", "verde", "8 KUP", "8kup", "Verde", "8 kup"]
    for i in range(12):
        c = generate_competitor("Infantil Verde", i)
        c["Grado"] = grados_variantes[i % len(grados_variantes)]
        c["Edad"] = 10
        c["Peso"] = 30.0 + (i * 0.5)
        c["Estatura"] = 125 + (i * 2)
        blocks["Infantil Verde"].append(c)
    create_excel(out_dir / "edge_grados.xlsx", blocks)

def fix_extreme_heights(out_dir):
    blocks = {"Infantil Roja": []}
    names = ["LIZBETH", "ALEXANDRA", "MARIA", "ANA", "PAULA", "LAURA", "CARMEN", "DANIELA"]
    for i in range(8):
        c = {
            "No": i + 1,
            "Nombre": names[i],
            "Apellido": "LOPEZ",
            "Edad": 11 if i % 2 == 0 else 12,
            "H/M": "M",
            "Grado": "1 KUP",
            "Peso": 48.0,
            "Estatura": 117.0 if i < 4 else 150.0,
            "Modalidad": "Poomsae",
            "Doyang": "MDK FLORIDO" if i % 2 == 0 else "CHAMPIONS",
        }
        blocks["Infantil Roja"].append(c)
    create_excel(out_dir / "extreme_heights.xlsx", blocks)

FIXTURES = [
    ("standard_100", fix_standard_100),
    ("all_males", fix_all_males),
    ("all_females", fix_all_females),
    ("same_cinta", fix_same_cinta),
    ("extreme_weights_min", fix_extreme_weights_min),
    ("extreme_weights_max", fix_extreme_weights_max),
    ("extreme_weights_same", fix_extreme_weights_same),
    ("extreme_ages_same", fix_same_age),
    ("extreme_ages_diff1", fix_age_diff_1),
    ("extreme_ages_diff3", fix_age_diff_3),
    ("same_doyang", fix_same_doyang),
    ("different_doyang", fix_different_doyang),
    ("mix_modalidad", fix_mix_modalidad),
    ("single_competitor", fix_single_competitor),
    ("pairs_only", fix_pairs_only),
    ("triples_only", fix_triples_only),
    ("quads_only", fix_quads_only),
    ("all_infantil", fix_all_infantil),
    ("all_adultos", fix_all_adultos),   
    ("mixed_sizes", fix_mixed_sizes),
    ("invalid_grado", fix_invalid_grado),
    ("empty_sheets", fix_empty_sheets),
    ("weights_decimal", fix_weights_decimal),
    ("special_chars", fix_special_chars),
    ("no_rival_perfect", fix_no_rival_perfect),
    ("worst_case", fix_worst_case),
    ("cross_cinta", fix_cross_cinta),
    ("edge_grados", fix_edge_grados),
    ("extreme_heights", fix_extreme_heights),
]

def main():
    out_dir = Path(__file__).parent / "fixtures"
    out_dir.mkdir(exist_ok=True)
    
    for name, generator in FIXTURES:
        print(f"Generating {name}...")
        generator(out_dir)
    
    print(f"\nCreated {len(FIXTURES)} test fixtures in {out_dir}")
    
    # Create index file
    with open(out_dir / "index.txt", "w") as f:
        for i, (name, _) in enumerate(FIXTURES, 1):
            f.write(f"{i}. {name}\n")
    
    print(f"Fixture index in {out_dir / 'index.txt'}")

if __name__ == "__main__":
    main()