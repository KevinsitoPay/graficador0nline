import sys
sys.path.insert(0, ".")

from app.parser import parse_excel

comps, errs = parse_excel("C:/Users/USUARIO/Desktop/sitiosLocales/Graficador/template/competidores_ejemplo.xlsx")
print(f"Competitors: {len(comps)}, Errors: {len(errs)}")
if errs:
    print("Errors:", errs[:3])