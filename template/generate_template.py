import random
import xlsxwriter
from pathlib import Path

BLOCKS = [
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
    "MARCOS", "HECTOR", "JONATHAN", "ALFREDO", "VICTOR", "ERNESTO", "RENE", "JULIAN", "SALVADOR", "ARTURO",
]

FIRST_NAMES_F = [
    "SOFIA", "MARIA", "CAMILA", "VALENTINA", "LUCIA", "PAULA", "ANA", "LAURA", "KARLA", "GABRIELA",
    "ADRIANA", "MONSERRAT", "DANIELA", "ALEXANDRA", "ELIZABETH", "PATRICIA", "ANGELICA", "VERONICA", "DIANA", "LIZBETH",
]

LAST_NAMES = [
    "LOPEZ", "GARCIA", "MARTINEZ", "RODRIGUEZ", "HERNANDEZ", "PEREZ", "SANCHEZ", "RAMIREZ", "TORRES", "FLORES",
    "RIVERA", "GOMEZ", "DIAZ", "REYES", "MORALES", "CRUZ", "ORTIZ", "GUTIERREZ", "CHAVEZ", "RAMOS",
    "RUIZ", "VARGAS", "MEDINA", "CASTRO", "DELGADO", "MORENO", "ROMERO", "HERRERA", "MEDRANO", "NAVARRO",
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

EDAD_RANGES = {
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
}

PESO_RANGES = {
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
}

ESTATURA_RANGES = {
    "Adultos Grupo 1": (150, 195),
    "Adultos Grupo 2": (145, 200),
    "Infantil Azul": (130, 175),
    "Infantil Verde": (125, 165),
    "Infantil Amarilla": (115, 155),
    "Infantil Blanca": (105, 140),
    "Infantil Marrón": (120, 165),
    "Infantil Roja": (115, 160),
    "Infantil Negra": (130, 180),
    "Pre-Taekwondo": (95, 125),
}

MODALIDADES = [("Doble", 0.6), ("Sencillo", 0.4)]

def weighted_choice(choices):
    items, weights = zip(*choices)
    return random.choices(items, weights=weights)[0]

def generate_competitors(block, count):
    competitors = []
    edad_min, edad_max = EDAD_RANGES[block]
    peso_min, peso_max = PESO_RANGES[block]
    estatura_min, estatura_max = ESTATURA_RANGES[block]
    
    for i in range(count):
        sexo = random.choice(["H", "M"])
        if sexo == "H":
            nombre = random.choice(FIRST_NAMES_M)
        else:
            nombre = random.choice(FIRST_NAMES_F)
        
        nombre = nombre.upper()
        last_name = random.choice(LAST_NAMES)
        edad = random.randint(edad_min, edad_max)
        grado = weighted_choice(GRADOS[block])
        peso = round(random.uniform(peso_min, peso_max), 2)
        estatura = random.randint(estatura_min, estatura_max)
        modalidad = weighted_choice(MODALIDADES)
        doyang = random.choice(SCHOOLS)
        
        competitors.append({
            "No": i + 1,
            "Nombre": nombre,
            "Apellido": last_name,
            "Edad": edad,
            "H/M": sexo,
            "Grado": grado,
            "Peso": peso,
            "Estatura": estatura,
            "Modalidad": modalidad,
            "Doyang": doyang,
        })
    
    return competitors

def main():
    output = Path(__file__).parent / "competidores_ejemplo.xlsx"
    workbook = xlsxwriter.Workbook(output)
    
    for block in BLOCKS:
        worksheet = workbook.add_worksheet(block)
        
        headers = ["No", "Nombre", "Apellido", "Edad", "H/M", "Grado", "Peso", "Estatura", "Modalidad", "Doyang"]
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)
        
        competitors = generate_competitors(block, 100)
        
        for row_idx, comp in enumerate(competitors):
            for col_idx, header in enumerate(headers):
                value = comp[header]
                worksheet.write(row_idx + 1, col_idx, value)
    
    workbook.close()
    print(f"Created: {output}")
    print(f"Sheets: {len(BLOCKS)} blocks with 100 competitors each")

if __name__ == "__main__":
    main()