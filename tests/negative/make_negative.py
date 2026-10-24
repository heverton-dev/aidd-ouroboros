"""Gera um projeto sabotado a partir de tests/smoke para provar que as auditorias reprovam."""
import json
import shutil
import sys
from pathlib import Path

smoke, neg = Path(sys.argv[1]), Path(sys.argv[2])
proj = neg / "proj"
if proj.exists():
    shutil.rmtree(proj)
proj.mkdir(parents=True)
shutil.copytree(smoke / "evidence", proj / "evidence")
shutil.copy(smoke / "step-map.json", proj / "step-map.json")

sb = json.loads((smoke / "storyboard.json").read_text(encoding="utf-8"))
sc = sb["scenes"]
sc[1]["start"] += 0.4                       # buraco entre c01 e c02
sc[2]["steps"] = ["s01"]                    # s01 em duas cenas, s02 em nenhuma
sc[2]["on_screen_text"] = ["um texto de tela longo demais para qualquer pessoa ler"]
sc[3]["narration"] = " ".join(["palavra"] * 40)  # não cabe em ~3,5 s
sc[3]["layout"] = "carrossel"               # fora do menu
(proj / "storyboard.json").write_text(json.dumps(sb, ensure_ascii=False, indent=2), encoding="utf-8")

# transcrição com retake da frase da c03 e sem a frase da c02
good = []
for s in sb["scenes"]:
    f = smoke / "audio" / f"{s['id']}.words.json"
    if f.exists():
        ws = json.loads(f.read_text(encoding="utf-8"))
        good.append({"start": ws[0]["start"], "end": ws[-1]["end"], "text": " ".join(w["text"] for w in ws)})
bad = [s for s in good if "menu" not in s["text"] and "Clique" not in s["text"]]
retake = [dict(s, start=s["start"] + 20, end=s["end"] + 20) for s in good if "tabela" in s["text"]]
(proj / "transcript.json").write_text(json.dumps({"segments": bad + retake}, ensure_ascii=False), encoding="utf-8")
print(proj)
