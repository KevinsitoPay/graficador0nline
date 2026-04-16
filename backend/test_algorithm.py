import sys
sys.path.insert(0, ".")

from app.parser import parse_excel
from app.algorithm import generate_results
import json

comps, errs = parse_excel("C:/Users/USUARIO/Desktop/sitiosLocales/Graficador/template/competidores_ejemplo.xlsx")
print(f"Competitors: {len(comps)}")

results = generate_results(comps)

print(f"Total brackets: {results.global_stats.total_brackets}")
print(f"Sin rival: {results.global_stats.sin_rival_total}")
print(f"Brackets 2: {results.global_stats.brackets_2}")
print(f"Brackets 3: {results.global_stats.brackets_3}")
print(f"Brackets 4: {results.global_stats.brackets_4}")
print(f"Excellent: {results.global_stats.excellent_brackets}")
print(f"Low quality: {results.global_stats.low_quality_brackets}")

print("\nBlock stats:")
for bs in results.block_stats:
    print(f"  {bs.bloque}: {bs.competidores} comps, {bs.brackets} brackets, {bs.sin_rival} sin rival")