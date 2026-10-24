"""Resume o JSON do `hyperframes check`: status, contagens e achados que não são informativos."""
import json
import sys

d = json.load(open(sys.argv[1], encoding="utf-8-sig"))
groups = ("lint", "runtime", "layout", "contrast", "craft")
print("check ok" if d.get("ok") else "check FALHOU", [(k, d[k]["errorCount"], d[k]["warningCount"]) for k in groups if k in d])
for k in groups:
    for f in d.get(k, {}).get("findings") or []:
        if f.get("severity") in ("error", "warning") and f.get("code") != "nested_structure_needs_subcomposition":
            where = f.get("selector") or ""
            times = f.get("times") or ([f["time"]] if "time" in f else [])
            print(f"- {k} {f['severity']} {f.get('code')} {where} t={times[:4]} :: {str(f.get('message'))[:170]}")
