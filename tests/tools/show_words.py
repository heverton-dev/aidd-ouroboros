"""Mostra o início/fim de cada cena e o tempo de cada palavra (para posicionar cliques)."""
import json
import sys
from pathlib import Path

proj = Path(sys.argv[1])
sb = json.loads((proj / "storyboard.json").read_text(encoding="utf-8"))
for s in sb["scenes"]:
    f = proj / "audio" / f"{s['id']}.words.json"
    ws = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
    print(s["id"], s["start"], s["end"], " ".join(f"{w['text']}@{w['start']}" for w in ws))
