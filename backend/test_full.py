import sys
sys.path.insert(0, ".")

import json
from app.parser import parse_excel
from app.algorithm import generate_results
from pathlib import Path

excel_path = Path(__file__).parent.parent / "template" / "competidores_ejemplo.xlsx"

comps, errs = parse_excel(str(excel_path))
print(f"Parsed: {len(comps)} competitors")

results = generate_results(comps)
print(f"Bukrs: {results.global_stats.total_brackets}")

output = {
    "success": True,
    "message": f"Processed {len(comps)} competitors",
    "results": results.model_dump(mode='json')
}

print(json.dumps(output, indent=2, ensure_ascii=False)[:2000])