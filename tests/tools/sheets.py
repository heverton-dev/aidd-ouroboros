"""Gera uma folha de contato por perfil a partir das telas exploradas (explorar.summary.json)."""
import json
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
for summ in sorted(root.glob("*/explorar.summary.json")):
    d = json.loads(summ.read_text(encoding="utf-8"))
    pngs = [summ.parent / t["screenshot"] for t in d["telas"] if t.get("screenshot") and (summ.parent / t["screenshot"]).exists()]
    if not pngs:
        continue
    lst = summ.parent / "sheet.txt"
    lst.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in pngs), encoding="utf-8")
    cols = 4
    rows = (len(pngs) + cols - 1) // cols
    out = summ.parent / "contact-sheet.jpg"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-vf", f"scale=480:-2,tile={cols}x{rows}:padding=6:color=white", "-frames:v", "1", "-update", "1",
                    str(out)], check=True)
    lst.unlink()
    print(out, len(pngs))
