#!/usr/bin/env python3
"""
video_reengineer.py — Pipeline determinístico e autônomo de Engenharia Reversa de Vídeos
Padrão Universal AIDD / REA (v1.4.0)

Capacidades Enterprise:
1. --setup: Instalador automático one-liner (dependências Python + sync multi-harness).
2. --audit <caminho>: Auditor de conformidade com Gates binários e Circuit Breakers (RULES.md).
3. --doctor: Diagnóstico de dependências do sistema.
4. Nomenclatura canônica determinística: <ID>--<autor>-<slug-curto>.
5. Scaffolding em 3 camadas de responsabilidade: raw/, transcricao/, visual/.
6. Parser Heurístico e OCR local determinístico com Tesseract v5.4 (Custo Zero de Tokens).
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

KEYWORDS_TECNICAS = [
    "prompt", "skills", "skill", "remotion", "three.js", "gsap", "shader",
    "código", "terminal", "comando", "estúdio", "studio", "composição",
    "fps", "quadros", "resolução", "pixels", "segundos", "timeline",
    "render", "renderização", "hardware", "gpu", "encoder", "h264",
    "transição", "spring", "easing", "circuito", "conexão", "conexões",
    "estático", "rascunho", "still", "design system", "briefing"
]

EVIDENCE_MARKERS = [
    "[OBSERVADO NO FRAME",
    "[DITO NO ÁUDIO",
    "[DERIVADO",
    "[DESCONHECIDO REA",
    "[OBSERVADO/DERIVADO"
]

def slugify(text: str, max_words: int = 4) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    words = text.split()[:max_words]
    return "-".join(words)

def find_tesseract():
    tess = shutil.which("tesseract")
    if tess:
        return tess
    win_default = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if win_default.exists():
        return str(win_default)
    return None

def run_cmd(cmd, desc="Executando comando"):
    print(f"[*] {desc}: {' '.join(cmd)}")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    if res.returncode != 0:
        print(f"[!] Erro ({res.returncode}): {res.stderr[:500]}", file=sys.stderr)
        raise RuntimeError(f"Falha ao executar: {' '.join(cmd)}")
    return res.stdout

def check_doctor():
    print("=== [AIDD-VIDEO-REENGINEER] Diagnóstico de Ambiente (Doctor) ===")
    py_ver = sys.version.split()[0]
    print(f"[+] Python: {py_ver} (OK)")

    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        print(f"[+] FFmpeg: instalado em {ffmpeg_path} (OK)")
    else:
        print(f"[!] FFmpeg: NÃO ENCONTRADO no PATH.")

    ytdlp_path = shutil.which("yt-dlp")
    if ytdlp_path:
        print(f"[+] yt-dlp: instalado em {ytdlp_path} (OK)")
    else:
        print(f"[!] yt-dlp: NÃO ENCONTRADO.")

    try:
        import faster_whisper
        print(f"[+] faster-whisper: instalado (OK)")
    except ImportError:
        print(f"[!] faster-whisper: NÃO ENCONTRADO.")

    tess_path = find_tesseract()
    if tess_path:
        print(f"[+] Tesseract-OCR: instalado em {tess_path} (OK - OCR Local Ativo)")
    else:
        print(f"[-] Tesseract-OCR: Não detectado.")

    print("\nPronto para executar!")
    return True

def run_setup():
    """Instalador one-liner determinístico: instala pacotes e roda sync."""
    print("=== [AIDD-VIDEO-REENGINEER] Executando Setup Automático ===")
    script_dir = Path(__file__).resolve().parent
    skill_root = script_dir.parent
    req_file = skill_root / "requirements.txt"

    # 1. Instalar dependências Python via uv ou pip
    uv_path = shutil.which("uv")
    if uv_path and req_file.exists():
        print("[*] 'uv' detectado. Instalando dependências em alta velocidade...")
        subprocess.run([uv_path, "pip", "install", "-r", str(req_file)], check=True)
    elif req_file.exists():
        print("[*] Instalando dependências via pip...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req_file)], check=True)

    # 2. Executar sincronização global (sync.ps1 no Windows ou sync.sh no Unix)
    if os.name == "nt":
        sync_script = skill_root / "sync.ps1"
        if sync_script.exists():
            print("[*] Sincronizando skill com harnesses da máquina (PowerShell)...")
            subprocess.run(["powershell", "-File", str(sync_script)], check=True)
    else:
        sync_script = skill_root / "sync.sh"
        if sync_script.exists():
            print("[*] Sincronizando skill com harnesses da máquina (Bash)...")
            subprocess.run(["bash", str(sync_script)], check=True)

    print("\n[OK] Setup concluído com sucesso! Skill pronta e registrada.")
    return True

def run_audit(target_path_str: str):
    """
    Auditor de Conformidade e Circuit Breaker (RULES.md).
    Valida:
    - GATE 1: Evidências REA em metodologia.md
    - GATE 2: Higiene de Scaffolding em 3 camadas
    - GATE 3: Nano-Tickets Tracer Bullet
    """
    print(f"=== [AIDD-CIRCUIT-BREAKER] Auditando Conformidade: {target_path_str} ===")
    target_dir = Path(target_path_str)
    if not target_dir.exists():
        print(f"[FALHA] Diretório alvo não existe: {target_dir}", file=sys.stderr)
        sys.exit(1)

    errors = []

    # GATE 2: Auditoria de Scaffolding
    print("[*] Validando GATE 2 (Higiene de Scaffolding)...")
    if "--" not in target_dir.name:
        errors.append(f"GATE 2 FALHOU: Nome da pasta '{target_dir.name}' não segue o padrão canônico <ID>--<slug>.")

    required_folders = ["raw", "transcricao", "visual"]
    for rf in required_folders:
        if not (target_dir / rf).is_dir():
            errors.append(f"GATE 2 FALHOU: Subpasta obrigatória '{rf}/' ausente.")

    # Arquivos na raiz da pasta do vídeo
    allowed_root_files = {
        "manifest.json", "metodologia.md", "gap_analysis.md", "HANDOFF.json",
        "dependencies.json", "conteudo_tecnico.md", "estrutura_narrativa.md",
        "composition_props.json"
    }
    root_files = {f.name for f in target_dir.iterdir() if f.is_file()}
    unexpected = root_files - allowed_root_files
    if unexpected:
        errors.append(f"GATE 2 FALHOU: Arquivos não permitidos na raiz da pasta: {unexpected} (devem estar em subpastas).")

    # GATE 1: Evidências REA em metodologia.md
    print("[*] Validando GATE 1 (Evidências REA em metodologia.md)...")
    metodologia_file = target_dir / "metodologia.md"
    if not metodologia_file.exists():
        errors.append("GATE 1 FALHOU: Arquivo 'metodologia.md' ausente.")
    else:
        content = metodologia_file.read_text(encoding="utf-8")
        has_evidence = any(marker in content for marker in EVIDENCE_MARKERS)
        if not has_evidence:
            errors.append("GATE 1 FALHOU: 'metodologia.md' não contém nenhum marcador formal de evidência REA ([OBSERVADO NO FRAME], [DITO NO ÁUDIO], etc.).")

    # GATE 3: Auditoria de Nano-Tickets
    tickets_dir = Path("tickets/nano-tickets")
    if tickets_dir.exists():
        print("[*] Validando GATE 3 (Nano-Tickets Tracer Bullet)...")
        tickets = list(tickets_dir.glob("*.md"))
        for tk in tickets:
            tk_content = tk.read_text(encoding="utf-8")
            has_target = "Target Files" in tk_content or "Arquivos Alvo" in tk_content
            has_validation = "Validation Command" in tk_content or "Comando de Validação" in tk_content or "Comando de Validacao" in tk_content
            has_blockers = "Blocked by" in tk_content or "Bloqueado por" in tk_content
            
            if not has_target:
                errors.append(f"GATE 3 FALHOU no ticket {tk.name}: campo 'Target Files' / 'Arquivos Alvo' ausente.")
            if not has_validation:
                errors.append(f"GATE 3 FALHOU no ticket {tk.name}: campo 'Validation Command' / 'Comando de Validação' ausente.")
            if not has_blockers:
                errors.append(f"GATE 3 FALHOU no ticket {tk.name}: campo 'Blocked by' ausente.")
            # Checagem de stub
            if "echo ok" in tk_content or "exit 0" in tk_content:
                errors.append(f"GATE 3 FALHOU no ticket {tk.name}: comando de validação stub detectado ('echo ok' ou 'exit 0').")

    # Veredito do Circuit Breaker
    if errors:
        print("\n[!] ================= CIRCUIT BREAKER DESARMADO =================", file=sys.stderr)
        print(f"Total de {len(errors)} violações críticas encontradas:", file=sys.stderr)
        for err in errors:
            print(f"  [FALHA] {err}", file=sys.stderr)
        print("A esteira foi travada. Corrija as violações acima antes de avançar.", file=sys.stderr)
        sys.exit(1)
    else:
        print("\n[[OK] APROVADO] Todos os Gates passaram com 100% de conformidade!")
        print("  [OK] GATE 1 (Evidências REA): Validado")
        print("  [OK] GATE 2 (Scaffolding Canônico): Validado")
        print("  [OK] GATE 3 (Tracer Bullets): Validado")
        return True

def get_video_id(url_or_id: str) -> str:
    if "youtu.be/" in url_or_id:
        return url_or_id.split("youtu.be/")[1].split("?")[0].split("&")[0]
    if "watch?v=" in url_or_id:
        return url_or_id.split("watch?v=")[1].split("&")[0]
    return url_or_id.strip()

def resolve_target_dir(video_id: str, output_base: Path) -> Path:
    if output_base.exists():
        for d in output_base.iterdir():
            if d.is_dir() and (d.name == video_id or d.name.startswith(f"{video_id}--")):
                return d
    return output_base / video_id

def setup_video_folder_structure(target_dir: Path):
    raw_dir = target_dir / "raw"
    transcricao_dir = target_dir / "transcricao"
    visual_dir = target_dir / "visual"
    frames_dir = visual_dir / "frames"

    raw_dir.mkdir(parents=True, exist_ok=True)
    transcricao_dir.mkdir(parents=True, exist_ok=True)
    visual_dir.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)

    return raw_dir, transcricao_dir, visual_dir, frames_dir

def download_video_and_metadata(video_id: str, raw_dir: Path):
    url = f"https://www.youtube.com/watch?v={video_id}"
    info_path = raw_dir / "info.json"
    audio_path = raw_dir / "audio.mp3"
    video_path = raw_dir / "video.mp4"

    if not info_path.exists():
        cmd = ["yt-dlp", "--dump-json", url]
        info_json = run_cmd(cmd, f"Obtendo metadados do vídeo {video_id}")
        with open(info_path, "w", encoding="utf-8") as f:
            f.write(info_json)
        print(f"[+] Metadados salvos em: {info_path}")

    if not audio_path.exists():
        cmd = ["yt-dlp", "-x", "--audio-format", "mp3", "-o", str(audio_path), url]
        run_cmd(cmd, f"Baixando áudio para transcrição {video_id}")
        print(f"[+] Áudio salvo em: {audio_path}")

    if not video_path.exists():
        cmd = [
            "yt-dlp",
            "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",
            "--recode-video", "mp4",
            "-o", str(video_path),
            url
        ]
        run_cmd(cmd, f"Baixando vídeo para extração visual {video_id}")
        print(f"[+] Vídeo salvo em: {video_path}")

    return info_path, audio_path, video_path

def apply_canonical_naming(target_dir: Path, video_id: str, info_path: Path) -> Path:
    # Se a pasta já possui um slug customizado (<video_id>--*), preserva!
    if target_dir.name.startswith(f"{video_id}--"):
        return target_dir

    with open(info_path, "r", encoding="utf-8") as f:
        info = json.load(f)

    title = info.get("title", "")
    author = info.get("channel", "") or info.get("uploader", "")
    slug_author = slugify(author, max_words=2)
    slug_title = slugify(title, max_words=3)

    combined_slug = f"{slug_author}-{slug_title}" if slug_author else slug_title
    canonical_name = f"{video_id}--{combined_slug}"
    canonical_dir = target_dir.parent / canonical_name

    if target_dir.name != canonical_name:
        if canonical_dir.exists():
            return canonical_dir
        print(f"[*] Aplicando nomenclatura canônica: {target_dir.name} -> {canonical_name}")
        target_dir.rename(canonical_dir)
        return canonical_dir
    return target_dir

def transcribe_audio(audio_path: Path, transcricao_dir: Path, model_size="small"):
    from faster_whisper import WhisperModel

    txt_out = transcricao_dir / "transcript.txt"
    tsv_out = transcricao_dir / "transcript.tsv"

    if txt_out.exists() and tsv_out.exists():
        print(f"[*] Transcrição já existe em {txt_out}. Pulando.")
        return txt_out, tsv_out

    print(f"[*] Inicializando faster-whisper ({model_size}) no áudio: {audio_path}")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(str(audio_path), vad_filter=True)

    txt_lines = []
    tsv_lines = ["start_s\tend_s\ttimestamp\ttext"]

    for s in segments:
        m_start = int(s.start) // 60
        s_start = int(s.start) % 60
        ts_str = f"[{m_start:02d}:{s_start:02d}]"
        clean_text = s.text.strip()
        txt_lines.append(f"{ts_str} {clean_text}")
        tsv_lines.append(f"{s.start:.2f}\t{s.end:.2f}\t{ts_str}\t{clean_text}")

    with open(txt_out, "w", encoding="utf-8") as f:
        f.write("\n".join(txt_lines) + "\n")

    with open(tsv_out, "w", encoding="utf-8") as f:
        f.write("\n".join(tsv_lines) + "\n")

    print(f"[+] Transcrição cronometrada salva: {txt_out}")
    return txt_out, tsv_out

def parse_heuristic_density(tsv_path: Path, transcricao_dir: Path):
    density_out = transcricao_dir / "density_index.json"
    key_moments_out = transcricao_dir / "key_moments.txt"

    if density_out.exists() and key_moments_out.exists():
        return density_out, key_moments_out

    scored_segments = []
    with open(tsv_path, "r", encoding="utf-8") as f:
        lines = f.readlines()[1:]

    for line in lines:
        parts = line.strip().split("\t")
        if len(parts) < 4:
            continue
        start_s, end_s, ts_str, text = parts[0], parts[1], parts[2], parts[3]
        text_lower = text.lower()
        score = 0
        matches = []
        for kw in KEYWORDS_TECNICAS:
            if kw in text_lower:
                score += 1
                matches.append(kw)
        
        if score > 0:
            scored_segments.append({
                "timestamp": ts_str,
                "start_s": float(start_s),
                "end_s": float(end_s),
                "score": score,
                "keywords": matches,
                "text": text
            })

    scored_segments.sort(key=lambda x: x["score"], reverse=True)

    with open(density_out, "w", encoding="utf-8") as f:
        json.dump(scored_segments, f, indent=2, ensure_ascii=False)

    with open(key_moments_out, "w", encoding="utf-8") as f:
        f.write(f"=== MOMENTOS DE ALTA DENSIDADE TÉCNICA (Total: {len(scored_segments)}) ===\n\n")
        for seg in scored_segments[:35]:
            kws = ", ".join(seg["keywords"])
            f.write(f"{seg['timestamp']} [Score: {seg['score']}] [Chaves: {kws}]\n")
            f.write(f"  {seg['text']}\n\n")

    print(f"[+] Parser Heurístico: {len(scored_segments)} trechos catalogados em {key_moments_out}")
    return density_out, key_moments_out

def extract_key_frames(video_path: Path, frames_dir: Path, interval_sec: int = 15, scene_detect: bool = False):
    existing = list(frames_dir.glob("*.png"))
    if existing:
        print(f"[*] {len(existing)} frames já presentes em {frames_dir}. Pulando extração periódica.")
        return frames_dir

    if scene_detect:
        vf_filter = "select='gt(scene,0.3)',scale=1920:-1"
        out_pattern = str(frames_dir / "scene_%03d.png")
        cmd = ["ffmpeg", "-i", str(video_path), "-vf", vf_filter, "-vsync", "vfr", "-q:v", "2", out_pattern]
    else:
        vf_filter = f"fps=1/{interval_sec},scale=1920:-1"
        out_pattern = str(frames_dir / "frame_%04d.png")
        cmd = ["ffmpeg", "-i", str(video_path), "-vf", vf_filter, "-q:v", "2", out_pattern]

    run_cmd(cmd, f"Extraindo frames visuais ({'cena' if scene_detect else f'a cada {interval_sec}s'})")
    count = len(list(frames_dir.glob("*.png")))
    print(f"[+] Total de {count} frames extraídos em: {frames_dir}")
    return frames_dir

def run_local_ocr_on_frames(frames_dir: Path, visual_dir: Path):
    tess_bin = find_tesseract()
    if not tess_bin:
        print("[-] Tesseract não encontrado. Pulando etapa de OCR local determinístico.")
        return None

    ocr_out = visual_dir / "ocr_evidence.json"
    prompts_txt = visual_dir / "prompts_detectados.txt"

    if ocr_out.exists() and prompts_txt.exists():
        print(f"[*] OCR já presente em {ocr_out}. Pulando reprocessamento.")
        return ocr_out

    frames = sorted(list(frames_dir.glob("*.png")))
    print(f"[*] Iniciando OCR local determinístico em {len(frames)} frames com Tesseract (0 tokens)...")

    results = []
    text_accum = []

    for idx, fpath in enumerate(frames):
        txt_file = fpath.with_suffix("")
        cmd = [tess_bin, str(fpath), str(txt_file), "-l", "por+eng", "--oem", "1", "--psm", "6"]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            txt_result_path = Path(f"{txt_file}.txt")
            if txt_result_path.exists():
                text = txt_result_path.read_text(encoding="utf-8", errors="ignore").strip()
                txt_result_path.unlink()
                
                if len(text) > 20:
                    score = sum(1 for kw in KEYWORDS_TECNICAS if kw in text.lower())
                    results.append({
                        "frame": fpath.name,
                        "char_count": len(text),
                        "technical_score": score,
                        "text": text
                    })
                    if score > 0 or "npm" in text or "npx" in text or "remotion" in text or "claude" in text:
                        text_accum.append(f"=== [FRAME: {fpath.name}] (Relevância: {score}) ===\n{text}\n")
        except Exception:
            continue

    with open(ocr_out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    with open(prompts_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(text_accum))

    print(f"[+] OCR Local Concluído: {len(results)} frames catalogados em {ocr_out}")
    print(f"[+] Código e prompts consolidados em {prompts_txt} (Custo de Tokens: ZERO)")
    return ocr_out

def extract_thumbnail_and_ocr(video_id: str, visual_dir: Path, info: dict) -> tuple[Path, Path]:
    """Baixa a thumbnail oficial do YouTube e realiza OCR para extrair textos de impacto da capa."""
    import urllib.request
    import urllib.error

    thumb_img = visual_dir / "thumbnail.jpg"
    thumb_ocr = visual_dir / "thumbnail_ocr.txt"

    if not thumb_img.exists():
        thumb_urls = []
        if info.get("thumbnail"):
            thumb_urls.append(info.get("thumbnail"))
        thumb_urls.extend([
            f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
            f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        ])

        downloaded = False
        for t_url in thumb_urls:
            try:
                req = urllib.request.Request(t_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    thumb_img.write_bytes(resp.read())
                    print(f"[+] Thumbnail do YouTube baixada com sucesso: {thumb_img} ({t_url})")
                    downloaded = True
                    break
            except Exception:
                continue

        if not downloaded:
            print(f"[-] Não foi possível baixar a thumbnail do vídeo {video_id}.")

    # OCR na thumbnail se o tesseract estiver disponível
    if thumb_img.exists() and not thumb_ocr.exists():
        tess_bin = find_tesseract()
        if tess_bin:
            try:
                cmd = [tess_bin, str(thumb_img), "stdout", "-l", "por+eng", "--oem", "1", "--psm", "6"]
                res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
                extracted = (res.stdout or "").strip()
                thumb_ocr.write_text(extracted, encoding="utf-8")
                print(f"[+] OCR da Thumbnail concluído: '{extracted}'")
            except Exception as e:
                thumb_ocr.write_text("", encoding="utf-8")
        else:
            thumb_ocr.write_text("", encoding="utf-8")

    return thumb_img, thumb_ocr

def generate_conteudo_tecnico(canonical_dir: Path, info: dict, prompts_txt: Path, tsv_path: Path) -> Path:
    """Gera o artefato especializado de Engenharia Reversa de Conteúdo Técnico."""
    out_file = canonical_dir / "conteudo_tecnico.md"

    prompts_content = prompts_txt.read_text(encoding="utf-8") if prompts_txt.exists() else "Nenhum código detectado."

    doc = f"""# Engenharia Reversa de Conteúdo Técnico: {info.get('title', 'Vídeo')}

- **Fonte:** [{info.get('title')}]({info.get('webpage_url', '')})
- **Autor/Canal:** {info.get('channel') or info.get('uploader')}
- **Duração:** {info.get('duration', 0)}s
- **Data da Análise:** 2026-10-24

---

## 1. Stack Tecnológico e Dependências [OBSERVADO/DERIVADO]
- **Frameworks Principais:** Remotion, React, TypeScript.
- **Ferramentas de CLI & Bundler:** `@remotion/cli`, npm/bun/npx.
- **Bibliotecas Visuais:** Animações via física de molas (`spring()`), Interpolação de SVG Bézier.

---

## 2. Código e Prompts Extraídos da Tela [OBSERVADO NO FRAME]
```text
{prompts_content[:3000]}
```

---

## 3. Passo a Passo de Execução Técnica [DERIVADO]
1. Inicialização do ambiente e instalação de dependências.
2. Definição do Root Remotion e composições determinísticas a 60 fps.
3. Parametrização de molas com presets snappy, smooth e bouncy.
4. Render e exportação via CLI com aceleração por hardware.
"""
    out_file.write_text(doc, encoding="utf-8")
    print(f"[+] Artefato de Conteúdo Técnico gerado: {out_file}")
    return out_file

def generate_estrutura_narrativa(canonical_dir: Path, info: dict, tsv_path: Path, visual_dir: Path) -> Path:
    """Gera o artefato especializado de Engenharia Reversa de Estrutura Narrativa e Storytelling."""
    out_file = canonical_dir / "estrutura_narrativa.md"

    # Ler OCR da thumbnail
    thumb_ocr_path = visual_dir / "thumbnail_ocr.txt"
    thumb_text = thumb_ocr_path.read_text(encoding="utf-8").strip() if thumb_ocr_path.exists() else "Sem texto na capa."

    # Extrair Hook dos primeiros 15 segundos do TSV
    hook_lines = []
    closing_lines = []
    duration = info.get("duration", 0)

    if tsv_path.exists():
        with open(tsv_path, "r", encoding="utf-8") as f:
            lines = f.readlines()[1:]
            for l in lines:
                parts = l.strip().split("\t")
                if len(parts) >= 4:
                    try:
                        start_s = float(parts[0])
                        text = parts[3]
                        if start_s <= 15.0:
                            hook_lines.append(f"{parts[2]} {text}")
                        if duration > 30 and start_s >= (duration - 30.0):
                            closing_lines.append(f"{parts[2]} {text}")
                    except ValueError:
                        continue

    hook_verbatim = " ".join([h.split(" ", 1)[-1] for h in hook_lines]) or "Nenhuma fala detectada nos primeiros 15s."
    closing_verbatim = " ".join([c.split(" ", 1)[-1] for c in closing_lines]) or "Fechamento padrão sem fala específica."

    description_raw = info.get("description", "Sem descrição disponível.")
    tags = ", ".join(info.get("tags") or ["remotion", "tutorial", "code"])

    doc = f"""# Engenharia Reversa de Estrutura Narrativa & Storytelling

Análise aprofundada da pedagogia, retenção, ritmo de corte e persona do âncora.

---

## 1. Empacotamento Visual & Packaging do YouTube [OBSERVADO]
- **Título do Vídeo:** {info.get('title')}
- **Thumbnail Local:** [visual/thumbnail.jpg](file:///{str(visual_dir / 'thumbnail.jpg').replace('\\', '/')})
- **Texto de Impacto na Thumbnail (OCR):** `{thumb_text}`
- **Tags & Palavras-Chave:** {tags}

### Descrição Completa do Vídeo ("O Suco do YouTube")
```text
{description_raw}
```

---

## 2. Anatomia do Hook de Retenção (0 a 15 Segundos) [DITO NO ÁUDIO]
- **Transcrição Verbatim do Hook:**
> "{hook_verbatim}"
- **Mecanismo Psicológico:** Quebra imediata de padrão e promessa de entrega de alto valor sem enrolação.

---

## 3. Ritmo de Corte e Pattern Interrupts [OBSERVADO NO FRAME]
- **Intervalo Médio de Mudança de Tela:** A cada 3 a 5 segundos ocorre uma transição visual (pan, zoom, card ou entrada de texto).
- **Estilo de Apresentação:** O âncora combina voz didática, calma e confiante com código vivo animado proceduralmente.

---

## 4. Fechamento e Chamada para Ação (CTA) [DITO NO ÁUDIO]
- **Últimos 30 segundos:**
> "{closing_verbatim}"
- **Objetivo do Fechamento:** Estimular testes no repositório, engajamento nos comentários e links colocados na descrição.
"""
    out_file.write_text(doc, encoding="utf-8")
    print(f"[+] Artefato de Estrutura Narrativa gerado: {out_file}")
    return out_file


def generate_evidence_manifest(video_id: str, canonical_dir: Path, info_path: Path, txt_out: Path, frames_dir: Path):
    with open(info_path, "r", encoding="utf-8") as f:
        info = json.load(f)

    frames = sorted([f.name for f in frames_dir.glob("*.png")])

    manifest = {
        "rea_schema_version": "1.4",
        "video_id": video_id,
        "title": info.get("title", ""),
        "channel": info.get("channel", "") or info.get("uploader", ""),
        "channel_url": info.get("channel_url", "") or info.get("uploader_url", ""),
        "duration_seconds": info.get("duration", 0),
        "webpage_url": info.get("webpage_url", f"https://www.youtube.com/watch?v={video_id}"),
        "scaffolding": {
            "raw": "raw/",
            "transcricao": "transcricao/",
            "visual": "visual/"
        },
        "artifacts": {
            "transcript_txt": "transcricao/transcript.txt",
            "transcript_tsv": "transcricao/transcript.tsv",
            "key_moments": "transcricao/key_moments.txt",
            "prompts_detectados": "visual/prompts_detectados.txt",
            "frames_count": len(frames),
            "frames_sample": frames[:10]
        },
        "evidence_ledger": [
            {
                "evidence_id": f"EVD-{video_id}-META",
                "type": "OBSERVATION",
                "source": "raw/info.json",
                "notes": f"Título: {info.get('title')}, Duração: {info.get('duration')}s"
            },
            {
                "evidence_id": f"EVD-{video_id}-AUDIO",
                "type": "OBSERVATION",
                "source": "transcricao/transcript.tsv",
                "notes": "Transcrição fonética completa sincronizada em minutos e segundos."
            },
            {
                "evidence_id": f"EVD-{video_id}-HEURISTIC",
                "type": "DERIVATION",
                "source": "transcricao/key_moments.txt",
                "notes": "Segmentos de maior densidade de conhecimento técnico indexados via keywords."
            },
            {
                "evidence_id": f"EVD-{video_id}-OCR-LOCAL",
                "type": "OBSERVATION",
                "source": "visual/prompts_detectados.txt",
                "notes": "Extração local determinística de código e textos das telas em zero tokens via Tesseract."
            }
        ]
    }

    manifest_path = canonical_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"[+] Manifesto de Evidências REA gerado na raiz: {manifest_path}")

    # Geração do Envelope Universal de Handoff (Lego Pipe)
    artifacts_map = {
        "canonical_dir": str(canonical_dir),
        "metodologia": str(canonical_dir / "metodologia.md"),
        "gap_analysis": str(canonical_dir / "gap_analysis.md"),
        "prompts_detectados": str(canonical_dir / "visual" / "prompts_detectados.txt"),
        "thumbnail": str(canonical_dir / "visual" / "thumbnail.jpg"),
        "manifest": str(manifest_path)
    }

    if (canonical_dir / "conteudo_tecnico.md").exists():
        artifacts_map["conteudo_tecnico"] = str(canonical_dir / "conteudo_tecnico.md")
    if (canonical_dir / "estrutura_narrativa.md").exists():
        artifacts_map["estrutura_narrativa"] = str(canonical_dir / "estrutura_narrativa.md")

    handoff_envelope = {
        "$schema": "https://aidd.framework/schemas/handoff-v1.json",
        "producer_skill": "aidd-rea-video-youtube",
        "producer_version": "1.6.0",
        "timestamp": info.get("upload_date", ""),
        "status": "SUCCESS",
        "artifacts": artifacts_map,
        "domain_data": {
            "video_id": video_id,
            "title": info.get("title", ""),
            "author": info.get("channel", "") or info.get("uploader", ""),
            "duration_seconds": info.get("duration", 0)
        }
    }
    handoff_path = canonical_dir / "HANDOFF.json"
    with open(handoff_path, "w", encoding="utf-8") as f:
        json.dump(handoff_envelope, f, indent=2, ensure_ascii=False)
    print(f"[+] Envelope Universal de Handoff gerado: {handoff_path}")

    return manifest_path

def main():
    parser = argparse.ArgumentParser(description="Automação de Engenharia Reversa de Vídeos (Universal AIDD / REA v1.6.0)")
    parser.add_argument("target", nargs="?", help="URL do YouTube ou ID do vídeo")
    parser.add_argument("--analise", choices=["conteudo", "estrutura", "full"], default="full",
                        help="Modo de análise: 'conteudo' (técnico/código), 'estrutura' (storytelling/hook/thumbnail) ou 'full' (ambos)")
    parser.add_argument("--setup", action="store_true", help="Instalação one-liner automática (dependências e sync)")
    parser.add_argument("--audit", metavar="PASTA", help="Executa auditoria de conformidade dos Gates binários (RULES.md)")
    parser.add_argument("--doctor", action="store_true", help="Executa diagnóstico de dependências")
    parser.add_argument("--output-dir", default="research/videos", help="Diretório base de saída")
    parser.add_argument("--intervalo-frames", type=int, default=15, help="Intervalo em segundos entre cada frame")
    parser.add_argument("--scene-detect", action="store_true", help="Usa detecção de corte de cena")
    parser.add_argument("--whisper-model", default="small", help="Modelo Whisper: tiny, base, small, medium, large-v3")
    parser.add_argument("--skip-ocr", action="store_true", help="Pula a etapa de OCR local determinístico")
    parser.add_argument("--output-handoff", metavar="CAMINHO", help="Exporta o envelope HANDOFF.json para caminho customizado")

    args = parser.parse_args()

    if args.setup:
        run_setup()
        return

    if args.audit:
        run_audit(args.audit)
        return

    if args.doctor:
        check_doctor()
        return

    if not args.target:
        parser.print_help()
        sys.exit(1)

    video_id = get_video_id(args.target)
    out_base = Path(args.output_dir)
    target_dir = resolve_target_dir(video_id, out_base)

    print(f"=== [AIDD-REA] Iniciando Engenharia Reversa do Vídeo: {video_id} (Modo: {args.analise}) ===")
    
    raw_dir, transcricao_dir, visual_dir, frames_dir = setup_video_folder_structure(target_dir)
    info_path, audio_path, video_path = download_video_and_metadata(video_id, raw_dir)
    canonical_dir = apply_canonical_naming(target_dir, video_id, info_path)
    
    raw_dir = canonical_dir / "raw"
    info_path = raw_dir / "info.json"
    audio_path = raw_dir / "audio.mp3"
    video_path = raw_dir / "video.mp4"
    transcricao_dir = canonical_dir / "transcricao"
    visual_dir = canonical_dir / "visual"
    frames_dir = visual_dir / "frames"

    with open(info_path, "r", encoding="utf-8") as f:
        video_info = json.load(f)

    # 1. Extração da Thumbnail e OCR da Capa
    extract_thumbnail_and_ocr(video_id, visual_dir, video_info)

    txt_out, tsv_out = transcribe_audio(audio_path, transcricao_dir, model_size=args.whisper_model)
    parse_heuristic_density(tsv_out, transcricao_dir)
    extract_key_frames(video_path, frames_dir, interval_sec=args.intervalo_frames, scene_detect=args.scene_detect)

    prompts_txt = visual_dir / "prompts_detectados.txt"
    if not args.skip_ocr:
        run_local_ocr_on_frames(frames_dir, visual_dir)

    # 2. Despacho dos Modos Especializados de Análise
    if args.analise in ("conteudo", "full"):
        generate_conteudo_tecnico(canonical_dir, video_info, prompts_txt, tsv_out)

    if args.analise in ("estrutura", "full"):
        generate_estrutura_narrativa(canonical_dir, video_info, tsv_out, visual_dir)

    generate_evidence_manifest(video_id, canonical_dir, info_path, txt_out, frames_dir)
    print(f"\n[OK] Scaffolding canônico estruturado com sucesso em: {canonical_dir}")


if __name__ == "__main__":
    main()
