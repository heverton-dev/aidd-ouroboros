#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
session_sync.py — Motor Universal e Sincronizador Deterministico de Historico de Sessao (AIDD / faz-session)
Autor: Heverton Eduardo Peres (2026)
Padrao: AIDD Universal Architecture / Monolito Modular VSA

Capacidades Enterprise Cumulativas:
1. Organizacao automatica por subpastas de projeto em 'Desktop/sessoes-agentes/<projeto>/'.
2. Indices cumulativos locais por projeto ('historico_sessoes.json' e 'INDICE_PROJETO.md').
3. Indice mestre geral na raiz ('historico_geral.json' e 'INDICE_GERAL.md').
4. Suporte a sincronizacao em lote (--all / --backfill) varrendo history.jsonl e transcripts.
5. Filtro cirurgico por projeto (--project <nome>).
6. Telemetria e frontmatter estrito: id sessao, harness, tokens input, thinking, output e turnos literais.
7. Cache inteligente: pula processamento de sessoes ja sincronizadas e inalteradas.
8. Replica local transparente em 'secoes/' se o diretorio existir no workspace.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_AUTHOR = "Heverton Eduardo Peres"
DEFAULT_DESKTOP_DIR = Path.home() / "Desktop" / "sessoes-agentes"


def time_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def format_number_ptbr(n: int) -> str:
    """Formata numeros inteiros com separador de milhar no padrao brasileiro (ex: 8.314.925)."""
    if not isinstance(n, (int, float)):
        return str(n)
    return f"{int(n):,}".replace(",", ".")


def sanitize_project_name(raw: Optional[str]) -> str:
    """Sanitiza o nome de um projeto para uso seguro como pasta no sistema de arquivos."""
    if not raw or not str(raw).strip():
        return "projeto_indefinido"
    
    cleaned = str(raw).replace("\\", "/").rstrip("/")
    # Pega apenas o ultimo segmento do caminho
    base_name = cleaned.split("/")[-1].strip()
    
    # Remove caracteres invalidos para nomes de diretorio no Windows/Linux
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', base_name)
    safe_name = safe_name.strip(" .")
    return safe_name if safe_name else "projeto_indefinido"


def detect_git_info(cwd: Optional[Path] = None) -> Tuple[str, str]:
    """Detecta deterministicamente o nome do projeto e a branch ativa via git."""
    work_dir = str(cwd.resolve()) if cwd else os.getcwd()
    project_name = sanitize_project_name(Path(work_dir).name)
    branch_name = "unknown"

    try:
        res_top = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=work_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        if res_top.returncode == 0 and res_top.stdout.strip():
            project_name = sanitize_project_name(res_top.stdout.strip())

        res_branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=work_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        if res_branch.returncode == 0 and res_branch.stdout.strip():
            branch_name = res_branch.stdout.strip()
    except Exception:
        pass

    return project_name, branch_name


def date_ddmmyyyy(dt: Optional[datetime.datetime] = None) -> str:
    target_dt = dt or datetime.datetime.now()
    return target_dt.strftime("%d%m%Y")


def clean_user_prompt(raw: str) -> str:
    if not isinstance(raw, str):
        return ""
    m = re.search(r"<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>", raw, re.DOTALL)
    if m:
        return m.group(1).strip()
    raw_cleaned = re.sub(r"<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>", "", raw, flags=re.DOTALL)
    return raw_cleaned.strip()


def detect_harness(transcript_path: Path) -> str:
    """Identifica deterministicamente o harness em execucao a partir do path do transcript."""
    path_str = str(transcript_path).lower()
    if "antigravity-cli" in path_str:
        return "antigravity-cli"
    if "antigravity" in path_str or ".gemini" in path_str:
        return "gemini-antigravity"
    if ".claude" in path_str:
        return "claude-code"
    if "opencode" in path_str:
        return "opencode"
    if "cursor" in path_str:
        return "cursor"
    if "cline" in path_str:
        return "cline"
    if "hermes" in path_str:
        return "hermes"
    return "universal-aidd"


def calculate_telemetry(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calcula metricas agregadas de telemetria de tokens e raciocinio."""
    inp = 0
    out = 0
    cache = 0
    thinking_chars = 0
    thinking_tokens_explicit = 0

    for item in entries:
        inp += item.get("input_tokens", 0)
        out += item.get("output_tokens", 0)
        cache += item.get("cache_read_tokens", 0)
        
        if "thinking_tokens" in item:
            thinking_tokens_explicit += item.get("thinking_tokens", 0)
        
        th = item.get("thinking", "")
        if isinstance(th, str) and th:
            thinking_chars += len(th)

    thinking_tokens = thinking_tokens_explicit if thinking_tokens_explicit > 0 else (thinking_chars // 4)

    return {
        "tokens_input": inp,
        "tokens_thinking": thinking_tokens,
        "tokens_output": out,
        "tokens_cache_read": cache,
        "thinking_chars_total": thinking_chars
    }


def parse_antigravity_transcript(transcript_path: Path) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
    """Parse de transcript do Gemini / Antigravity CLI (transcript_full.jsonl ou transcript.jsonl)."""
    session_id = "unknown"
    parts = transcript_path.parts
    for idx, part in enumerate(parts):
        if part == "brain" and idx + 1 < len(parts):
            session_id = parts[idx + 1]
            break

    entries = []
    with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except Exception:
                pass

    telemetry = calculate_telemetry(entries)

    dialogues = []
    current_user = None
    current_responses = []

    for item in entries:
        source = item.get("source")
        item_type = item.get("type")

        if source == "USER_EXPLICIT" and item_type == "USER_INPUT":
            if current_user is not None:
                combined_response = "\n\n".join([r for r in current_responses if r.strip()]).strip()
                dialogues.append({
                    "turn": len(dialogues) + 1,
                    "timestamp": current_user.get("created_at"),
                    "user_prompt": clean_user_prompt(current_user.get("content", "")),
                    "model_response": combined_response
                })
                current_responses = []
            current_user = item
        elif source == "MODEL" and item_type == "PLANNER_RESPONSE":
            content = item.get("content")
            if content and isinstance(content, str) and content.strip():
                current_responses.append(content.strip())

    if current_user is not None:
        combined_response = "\n\n".join([r for r in current_responses if r.strip()]).strip()
        dialogues.append({
            "turn": len(dialogues) + 1,
            "timestamp": current_user.get("created_at"),
            "user_prompt": clean_user_prompt(current_user.get("content", "")),
            "model_response": combined_response
        })

    return session_id, dialogues, telemetry


def parse_claude_transcript(transcript_path: Path) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
    """Parse de transcript do Claude Code (.jsonl de projetos)."""
    session_id = transcript_path.stem
    entries = []
    with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except Exception:
                pass

    inp = 0
    out = 0
    cache = 0
    thinking_chars = 0

    for item in entries:
        u = item.get("usage", {})
        inp += u.get("input_tokens", 0)
        out += u.get("output_tokens", 0)
        cache += u.get("cache_read_input_tokens", 0)
        msg = item.get("message", {})
        if isinstance(msg, dict):
            for c in msg.get("content", []):
                if isinstance(c, dict) and c.get("type") == "thinking":
                    thinking_chars += len(c.get("thinking", ""))

    thinking_tokens = thinking_chars // 4
    telemetry = {
        "tokens_input": inp,
        "tokens_thinking": thinking_tokens,
        "tokens_output": out,
        "tokens_cache_read": cache,
        "thinking_chars_total": thinking_chars
    }

    dialogues = []
    current_user_text = ""
    current_user_ts = None
    current_responses = []

    for item in entries:
        role = item.get("role") or (item.get("message", {}).get("role") if isinstance(item.get("message"), dict) else None)
        ts = item.get("timestamp") or item.get("created_at")
        text_val = ""

        if isinstance(item.get("content"), str):
            text_val = item.get("content")
        elif isinstance(item.get("content"), list):
            for sub in item.get("content", []):
                if isinstance(sub, dict) and sub.get("type") == "text":
                    text_val += sub.get("text", "") + "\n"
                elif isinstance(sub, str):
                    text_val += sub + "\n"
        elif isinstance(item.get("message"), dict):
            m_content = item.get("message", {}).get("content", [])
            if isinstance(m_content, list):
                for sub in m_content:
                    if isinstance(sub, dict) and sub.get("type") == "text":
                        text_val += sub.get("text", "") + "\n"
                    elif isinstance(sub, str):
                        text_val += sub + "\n"
            elif isinstance(m_content, str):
                text_val = m_content

        if role == "user":
            if current_user_text:
                combined_response = "\n\n".join([r for r in current_responses if r.strip()]).strip()
                dialogues.append({
                    "turn": len(dialogues) + 1,
                    "timestamp": current_user_ts,
                    "user_prompt": clean_user_prompt(current_user_text),
                    "model_response": combined_response
                })
                current_responses = []
            current_user_text = text_val
            current_user_ts = ts
        elif role in ("assistant", "model"):
            if text_val.strip():
                current_responses.append(text_val.strip())

    if current_user_text:
        combined_response = "\n\n".join([r for r in current_responses if r.strip()]).strip()
        dialogues.append({
            "turn": len(dialogues) + 1,
            "timestamp": current_user_ts,
            "user_prompt": clean_user_prompt(current_user_text),
            "model_response": combined_response
        })

    return session_id, dialogues, telemetry


def detect_active_session_file(explicit_path: Optional[str] = None, session_id: Optional[str] = None) -> Optional[Path]:
    """Localiza deterministicamente o arquivo de transcript ativo."""
    if explicit_path:
        p = Path(explicit_path)
        if p.exists():
            return p.resolve()

    home = Path.home()

    # 1. Busca por session_id em Antigravity
    if session_id:
        for fname in ["transcript_full.jsonl", "transcript.jsonl"]:
            cand = home / ".gemini" / "antigravity-cli" / "brain" / session_id / ".system_generated" / "logs" / fname
            if cand.exists():
                return cand

    # 2. Busca a sessao mais recente em Antigravity
    brain_dir = home / ".gemini" / "antigravity-cli" / "brain"
    if brain_dir.exists():
        candidates = list(brain_dir.glob("*/.system_generated/logs/transcript_full.jsonl"))
        if not candidates:
            candidates = list(brain_dir.glob("*/.system_generated/logs/transcript.jsonl"))
        if candidates:
            candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            return candidates[0]

    # 3. Busca a sessao mais recente em Claude Code
    claude_projects = home / ".claude" / "projects"
    if claude_projects.exists():
        c_candidates = list(claude_projects.glob("*/*.jsonl"))
        if c_candidates:
            c_candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            return c_candidates[0]

    return None


def atualizar_indice_projeto(project_dir: Path, project_name: str, session_summary: Dict[str, Any]) -> None:
    """Atualiza deterministicamente o 'historico_sessoes.json' e o 'INDICE_PROJETO.md' dentro da pasta do projeto."""
    project_dir.mkdir(parents=True, exist_ok=True)
    json_path = project_dir / "historico_sessoes.json"
    md_path = project_dir / "INDICE_PROJETO.md"

    historico = {
        "projeto": project_name,
        "atualizado_em": time_iso(),
        "total_sessoes": 0,
        "total_turnos": 0,
        "total_tokens_input": 0,
        "total_tokens_thinking": 0,
        "total_tokens_output": 0,
        "sessoes": []
    }

    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                carregado = json.load(f)
                if isinstance(carregado, dict) and "sessoes" in carregado:
                    historico = carregado
        except Exception:
            pass

    # Upsert da sessao por ID
    s_id = session_summary.get("id_sessao")
    sessoes = [s for s in historico.get("sessoes", []) if s.get("id_sessao") != s_id]
    sessoes.append(session_summary)

    # Ordenar por data/timestamp decrescente
    sessoes.sort(key=lambda x: str(x.get("atualizado_em") or x.get("data") or ""), reverse=True)

    tot_turnos = sum(s.get("turnos", 0) for s in sessoes)
    tot_inp = sum(s.get("tokens_input", 0) for s in sessoes)
    tot_th = sum(s.get("tokens_thinking", 0) for s in sessoes)
    tot_out = sum(s.get("tokens_output", 0) for s in sessoes)

    historico["total_sessoes"] = len(sessoes)
    historico["total_turnos"] = tot_turnos
    historico["total_tokens_input"] = tot_inp
    historico["total_tokens_thinking"] = tot_th
    historico["total_tokens_output"] = tot_out
    historico["atualizado_em"] = time_iso()
    historico["sessoes"] = sessoes

    # Salva JSON atomico
    tmp_json = json_path.with_suffix(".tmp")
    with open(tmp_json, "w", encoding="utf-8") as f:
        json.dump(historico, f, indent=2, ensure_ascii=False)
    tmp_json.replace(json_path)

    # Gera INDICE_PROJETO.md
    md_lines = [
        f"# 📑 Histórico de Sessões — Projeto `{project_name}`",
        "",
        f"> **Total de Sessões Registradas:** {len(sessoes)}  ",
        f"> **Total de Turnos Interativos:** {format_number_ptbr(tot_turnos)}  ",
        f"> **Tokens Consumidos:** Input: {format_number_ptbr(tot_inp)} | Thinking: {format_number_ptbr(tot_th)} | Output: {format_number_ptbr(tot_out)}  ",
        f"> **Última Atualização:** {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        "",
        "| Data | ID Sessão | Turnos | Tokens (In / Th / Out) | Primeiro Prompt / Objetivo | Arquivo |",
        "| :--- | :--- | :---: | :--- | :--- | :--- |"
    ]

    for s in sessoes:
        dt = s.get("data", "N/D")
        sid = s.get("id_sessao", "N/D")
        turnos = s.get("turnos", 0)
        tok_str = f"{format_number_ptbr(s.get('tokens_input', 0))} / {format_number_ptbr(s.get('tokens_thinking', 0))} / {format_number_ptbr(s.get('tokens_output', 0))}"
        prompt = s.get("primeiro_prompt", "N/D").replace("|", "-").replace("\n", " ")[:90]
        fname = s.get("arquivo_md") or s.get("arquivo") or s.get("arquivo_json", "")
        file_link = f"[`{fname}`]({fname})" if fname else sid[:8]
        md_lines.append(f"| {dt} | `{sid[:8]}...` | {turnos} | {tok_str} | {prompt} | {file_link} |")

    md_lines.append("")
    md_path.write_text("\n".join(md_lines), encoding="utf-8")


def atualizar_indice_geral(desktop_dir: Path) -> None:
    """Consolida todas as subpastas de projetos em um 'historico_geral.json' e 'INDICE_GERAL.md' na raiz."""
    desktop_dir.mkdir(parents=True, exist_ok=True)
    json_path = desktop_dir / "historico_geral.json"
    md_path = desktop_dir / "INDICE_GERAL.md"

    projetos_resumo = []
    todas_sessoes = []

    for sub in desktop_dir.iterdir():
        if sub.is_dir() and (sub / "historico_sessoes.json").exists():
            try:
                with open(sub / "historico_sessoes.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    p_name = data.get("projeto", sub.name)
                    s_list = data.get("sessoes", [])
                    projetos_resumo.append({
                        "projeto": p_name,
                        "pasta": sub.name,
                        "total_sessoes": data.get("total_sessoes", len(s_list)),
                        "total_turnos": data.get("total_turnos", sum(s.get("turnos", 0) for s in s_list)),
                        "total_tokens_input": data.get("total_tokens_input", 0),
                        "total_tokens_thinking": data.get("total_tokens_thinking", 0),
                        "total_tokens_output": data.get("total_tokens_output", 0),
                        "ultima_atualizacao": data.get("atualizado_em", "")
                    })
                    for s in s_list:
                        s_copy = dict(s)
                        s_copy["projeto"] = p_name
                        fname = s.get("arquivo_md") or s.get("arquivo") or s.get("arquivo_json", "")
                        s_copy["rel_path"] = f"{sub.name}/{fname}" if fname else ""
                        todas_sessoes.append(s_copy)
            except Exception:
                pass

    projetos_resumo.sort(key=lambda x: x["total_sessoes"], reverse=True)
    todas_sessoes.sort(key=lambda x: str(x.get("atualizado_em") or x.get("data") or ""), reverse=True)

    geral_data = {
        "atualizado_em": time_iso(),
        "total_projetos": len(projetos_resumo),
        "total_sessoes": len(todas_sessoes),
        "total_turnos": sum(p["total_turnos"] for p in projetos_resumo),
        "total_tokens_input": sum(p["total_tokens_input"] for p in projetos_resumo),
        "total_tokens_output": sum(p["total_tokens_output"] for p in projetos_resumo),
        "projetos": projetos_resumo
    }

    tmp_json = json_path.with_suffix(".tmp")
    with open(tmp_json, "w", encoding="utf-8") as f:
        json.dump(geral_data, f, indent=2, ensure_ascii=False)
    tmp_json.replace(json_path)

    # Gera INDICE_GERAL.md
    md_lines = [
        "# 🌐 Central Cumulativa de Sessões Agênticas — AIDD",
        "",
        f"> **Total de Projetos Monitorados:** {len(projetos_resumo)}  ",
        f"> **Total de Sessões Arquivadas:** {len(todas_sessoes)}  ",
        f"> **Total de Turnos Interativos:** {format_number_ptbr(geral_data['total_turnos'])}  ",
        f"> **Tokens Globais Consumidos:** Input: {format_number_ptbr(geral_data['total_tokens_input'])} | Output: {format_number_ptbr(geral_data['total_tokens_output'])}  ",
        f"> **Última Atualização Geral:** {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        "",
        "## 📁 Resumo Consolidado por Projeto",
        "",
        "| Projeto | Sessões | Turnos | Tokens (Input / Output) | Última Atividade | Índice do Projeto |",
        "| :--- | :---: | :---: | :--- | :--- | :--- |"
    ]

    for p in projetos_resumo:
        p_name = p["projeto"]
        pasta = p["pasta"]
        sess_count = p["total_sessoes"]
        turnos = format_number_ptbr(p["total_turnos"])
        toks = f"{format_number_ptbr(p['total_tokens_input'])} / {format_number_ptbr(p['total_tokens_output'])}"
        dt_raw = p.get("ultima_atualizacao", "")[:10]
        link_md = f"[`Ver Sessões ({sess_count})`]({pasta}/INDICE_PROJETO.md)"
        md_lines.append(f"| **{p_name}** | {sess_count} | {turnos} | {toks} | {dt_raw} | {link_md} |")

    md_lines.extend([
        "",
        "---",
        "",
        "## 🕒 Últimas 25 Sessões Globais Registradas",
        "",
        "| Data | Projeto | ID Sessão | Turnos | Tokens In / Out | Objetivo / Primeiro Prompt | Arquivo |",
        "| :--- | :--- | :--- | :---: | :--- | :--- | :--- |"
    ])

    for s in todas_sessoes[:25]:
        dt = s.get("data", "N/D")
        proj = s.get("projeto", "N/D")
        sid = s.get("id_sessao", "N/D")
        turnos = s.get("turnos", 0)
        tok_str = f"{format_number_ptbr(s.get('tokens_input', 0))} / {format_number_ptbr(s.get('tokens_output', 0))}"
        prompt = s.get("primeiro_prompt", "N/D").replace("|", "-").replace("\n", " ")[:70]
        rel_link = s.get("rel_path", "")
        link_str = f"[`{sid[:8]}...`]({rel_link})" if rel_link else sid[:8]
        md_lines.append(f"| {dt} | **{proj}** | `{sid[:8]}` | {turnos} | {tok_str} | {prompt} | {link_str} |")

    md_lines.append("")
    md_path.write_text("\n".join(md_lines), encoding="utf-8")


def wrap_in_copyable_block(text: str, lang: str = "") -> str:
    """
    Envolve o conteudo em um bloco de codigo cercado com delimitadores dinamicos (CommonMark/GFM).
    Garante que renderizadores Markdown (VS Code, GitHub, Obsidian) criem o botao nativo 'Copiar',
    permitindo copiar e colar o prompt e a resposta com 1 clique sem quebrar a formatacao.
    """
    cleaned = (text or "").strip()
    if not cleaned:
        return f"```{lang}\n(vazio)\n```"

    # Encontra a maior sequencia de crases no texto para garantir fechamento seguro
    max_backticks = 2
    for match in re.finditer(r'`+', cleaned):
        if len(match.group(0)) > max_backticks:
            max_backticks = len(match.group(0))

    fence = '`' * (max_backticks + 1)
    return f"{fence}{lang}\n{cleaned}\n{fence}"


def render_markdown_session(
    dialogues: List[Dict[str, Any]],
    frontmatter: Dict[str, Any],
    project_name: str,
    branch_name: str,
    harness_name: str,
    s_id: str
) -> str:
    """
    Gera conteudo Markdown estruturado:
    - User Prompt: Envolvido em bloco de codigo copiavel para facil reutilizacao.
    - Model Response: Markdown nativo puro (tabelas, mermaid, diagramas e fluxo renderizados visualmente).
    - Cabecalho: Comandos de restauracao de sessao prontos para copiar e colar para cada harness.
    """
    inp_val = frontmatter.get("tokens_input", 0)
    th_val = frontmatter.get("tokens_thinking", 0)
    out_val = frontmatter.get("tokens_output", 0)
    cache_val = frontmatter.get("tokens_cache_read", 0)
    data_sessao = frontmatter.get("data_sessao", datetime.datetime.now().strftime("%d/%m/%Y"))
    atualizado_em = frontmatter.get("atualizado_em", time_iso())

    md_lines = [
        f"# 📋 Sessão `{s_id}` — Histórico Completo de Diálogos",
        "",
        f"> **Projeto:** `{project_name}` | **Branch:** `{branch_name}` | **Harness Ativo:** `{harness_name}`  ",
        f"> **Tokens Consumidos:** Input: `{format_number_ptbr(inp_val)}` | Thinking: `{format_number_ptbr(th_val)}` | Output: `{format_number_ptbr(out_val)}`  ",
        f"> **Total de Turnos:** `{len(dialogues)}` | **Data:** `{data_sessao}`  ",
        "",
        "### 🔄 Comandos de Restauração da Sessão",
        "```bash",
        f"# Antigravity CLI (agy)",
        f"agy --conversation {s_id} --model gemini-3.8-flash-high --dangerously-skip-permissions",
        "",
        f"# Claude Code",
        f"claude --resume {s_id} --dangerously-skip-permissions --chrome --model opus",
        "",
        f"# OpenCode",
        f"opencode --session {s_id} --pure --auto --agent -m opencode/big-pickle",
        "",
        f"# Mimo",
        f"mimo --session {s_id} --pure -m xiaomi-token-plan-sgp/mimo-v2.6-flash --trust",
        "",
        f"# OMP",
        f"omp --resume {s_id} --auto-approve --model nemotron-3-ultra-550B-A55B",
        "",
        f"# Hermes",
        f"hermes --resume {s_id} --yolo",
        "```",
        "",
        "---",
        ""
    ]

    for d in dialogues:
        turn_num = d.get("turn", 1)
        ts = d.get("timestamp", "")
        ts_str = f" — `{ts}`" if ts else ""
        md_lines.append(f"## 💬 Turno {turn_num}{ts_str}")
        md_lines.append("")
        md_lines.append("### 👤 User Prompt")
        md_lines.append(wrap_in_copyable_block(d.get("user_prompt", "")))
        md_lines.append("")
        md_lines.append("### 🤖 Model Response")
        md_lines.append(d.get("model_response", "").strip())
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    return "\n".join(md_lines).rstrip() + "\n"


def sync_session_to_disk(
    transcript_path: Optional[str] = None,
    session_id: Optional[str] = None,
    output_dir: Optional[str] = None,
    output_file: Optional[str] = None,
    export_format: str = "md",
    explicit_project: Optional[str] = None,
    clean_legacy_json: bool = True
) -> Dict[str, Any]:
    """
    Extrai turnos de uma sessao e salva deterministicamente no padrao cumulativo por projeto.
    Estrutura padrao: Desktop/sessoes-agentes/<projeto>/<data>_<id>.md (Markdown legivel e leve).
    Atualiza indices locais e o indice geral.
    """
    t_file = detect_active_session_file(transcript_path, session_id)
    if not t_file or not t_file.exists():
        raise FileNotFoundError(f"Transcript nao localizado para sessao '{session_id or transcript_path}'.")

    harness_name = detect_harness(t_file)

    if "antigravity-cli" in str(t_file) or "transcript" in t_file.name:
        s_id, dialogues, telemetry = parse_antigravity_transcript(t_file)
    else:
        s_id, dialogues, telemetry = parse_claude_transcript(t_file)

    if session_id:
        s_id = session_id

    # Determinar projeto
    if explicit_project:
        project_name = sanitize_project_name(explicit_project)
        branch_name = "unknown"
    else:
        project_name, branch_name = detect_git_info()

    # Raiz base
    base_desktop_dir = Path(output_dir) if output_dir else DEFAULT_DESKTOP_DIR
    base_desktop_dir.mkdir(parents=True, exist_ok=True)

    # Subpasta do projeto
    project_dir = base_desktop_dir / project_name
    project_dir.mkdir(parents=True, exist_ok=True)

    today_tag = date_ddmmyyyy()
    md_filename = f"{today_tag}_{s_id}.md"
    json_filename = f"{today_tag}_{s_id}.json"

    inp_val = telemetry["tokens_input"]
    th_val = telemetry["tokens_thinking"]
    out_val = telemetry["tokens_output"]
    cache_val = telemetry["tokens_cache_read"]

    primeiro_prompt = dialogues[0]["user_prompt"] if dialogues else "Sem prompts de usuario"

    frontmatter = {
        "id_sessao": s_id,
        "harness_utilizado": harness_name,
        "projeto": project_name,
        "branch": branch_name,
        "tokens_input": inp_val,
        "tokens_input_formatado": format_number_ptbr(inp_val),
        "tokens_thinking": th_val,
        "tokens_thinking_formatado": format_number_ptbr(th_val),
        "tokens_output": out_val,
        "tokens_output_formatado": format_number_ptbr(out_val),
        "tokens_cache_read": cache_val,
        "tokens_cache_read_formatado": format_number_ptbr(cache_val),
        "resumo_tokens": f"Input: {format_number_ptbr(inp_val)} | Thinking: {format_number_ptbr(th_val)} | Output: {format_number_ptbr(out_val)}",
        "total_turnos": len(dialogues),
        "data_sessao": datetime.datetime.now().strftime("%d/%m/%Y"),
        "atualizado_em": time_iso()
    }

    export_payload = {
        "frontmatter": frontmatter,
        "id_sessao": s_id,
        "harness_utilizado": harness_name,
        "projeto": project_name,
        "branch": branch_name,
        "tokens_input": inp_val,
        "tokens_input_formatado": format_number_ptbr(inp_val),
        "tokens_thinking": th_val,
        "tokens_thinking_formatado": format_number_ptbr(th_val),
        "tokens_output": out_val,
        "tokens_output_formatado": format_number_ptbr(out_val),
        "tokens_cache_read": cache_val,
        "tokens_cache_read_formatado": format_number_ptbr(cache_val),
        "total_turnos": len(dialogues),
        "total_turns": len(dialogues),
        "transcript_source": str(t_file.resolve()),
        "dialogos": dialogues
    }

    md_content = render_markdown_session(dialogues, frontmatter, project_name, branch_name, harness_name, s_id)

    saved_md_path: Optional[Path] = None
    saved_json_path: Optional[Path] = None

    # Exportar versao Markdown (.md)
    if export_format in ("md", "markdown", "all"):
        if output_file and output_file.endswith(".md"):
            target_md = Path(output_file)
            if not target_md.is_absolute():
                target_md = project_dir / target_md
        else:
            target_md = project_dir / md_filename
        target_md.write_text(md_content, encoding="utf-8")
        saved_md_path = target_md
        print(f"[OK] {len(dialogues)} turnos gravados em Markdown: {target_md.resolve()}")

    # Exportar versao JSON (.json)
    if export_format in ("json", "all"):
        if output_file and output_file.endswith(".json"):
            target_json = Path(output_file)
            if not target_json.is_absolute():
                target_json = project_dir / target_json
        else:
            target_json = project_dir / json_filename
        target_json.write_text(json.dumps(export_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        saved_json_path = target_json
        print(f"[OK] {len(dialogues)} turnos gravados em JSON: {target_json.resolve()}")

    # Se exportou apenas Markdown e foi solicitada limpeza de JSON legado individual
    if clean_legacy_json and export_format in ("md", "markdown"):
        legacy_json = project_dir / json_filename
        if legacy_json.exists():
            try:
                legacy_json.unlink()
            except Exception:
                pass

    # Replica local em 'secoes/' se o diretorio existir no workspace ativo
    local_secoes = Path("secoes")
    if not output_dir and local_secoes.is_dir():
        if export_format in ("md", "markdown", "all"):
            local_md = local_secoes / md_filename
            local_md.write_text(md_content, encoding="utf-8")
            print(f"[+] Replica local mantida em Markdown: {local_md.resolve()}")
        if export_format in ("json", "all"):
            local_json = local_secoes / json_filename
            local_json.write_text(json.dumps(export_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"[+] Replica local mantida em JSON: {local_json.resolve()}")
        if clean_legacy_json and export_format in ("md", "markdown"):
            local_legacy_json = local_secoes / json_filename
            if local_legacy_json.exists():
                try:
                    local_legacy_json.unlink()
                except Exception:
                    pass

    # Resumo para atualizar indices
    summary = {
        "id_sessao": s_id,
        "data": frontmatter["data_sessao"],
        "atualizado_em": time_iso(),
        "turnos": len(dialogues),
        "tokens_input": inp_val,
        "tokens_thinking": th_val,
        "tokens_output": out_val,
        "primeiro_prompt": primeiro_prompt,
        "arquivo_md": md_filename if saved_md_path else "",
        "arquivo_json": json_filename if saved_json_path else "",
        "arquivo": md_filename if saved_md_path else json_filename
    }

    # Atualiza indices cumulativos
    atualizar_indice_projeto(project_dir, project_name, summary)
    atualizar_indice_geral(base_desktop_dir)

    return export_payload


def sync_all_sessions(
    output_dir: Optional[str] = None,
    filter_project: Optional[str] = None,
    export_format: str = "md",
    force: bool = False
) -> None:
    """
    Modo Backfill / Sincronizacao em Lote:
    Varre o 'history.jsonl' e as pastas de 'brain/' no Antigravity CLI e Claude Code,
    agrupa todas as sessoes por projeto e popula o historico cumulativo no Desktop em Markdown (.md).
    """
    home = Path.home()
    base_desktop_dir = Path(output_dir) if output_dir else DEFAULT_DESKTOP_DIR
    base_desktop_dir.mkdir(parents=True, exist_ok=True)

    print("=============================================================================")
    print(" [AIDD-SESSION-SYNC] INICIANDO SINCRONIZACAO CUMULATIVA EM LOTE (BACKFILL)")
    print("=============================================================================")
    print(f"[*] Destino Base: {base_desktop_dir.resolve()}")
    print(f"[*] Formato Principal: {export_format.upper()}")
    if force:
        print("[*] Modo Force: ATIVADO (regeneracao total de todas as sessoes)")
    if filter_project:
        print(f"[*] Filtro de Projeto Ativo: '{filter_project}'")

    # 1. Carregar mapeamento de history.jsonl
    history_file = home / ".gemini" / "antigravity-cli" / "history.jsonl"
    session_map: Dict[str, Dict[str, Any]] = {}

    if history_file.exists():
        with open(history_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    cid = entry.get("conversationId")
                    if cid and cid not in session_map:
                        session_map[cid] = {
                            "workspace": entry.get("workspace"),
                            "display": entry.get("display", ""),
                            "timestamp": entry.get("timestamp")
                        }
                except Exception:
                    pass

    # 2. Varredura do diretorio brain/ para capturar sessoes existentes
    brain_dir = home / ".gemini" / "antigravity-cli" / "brain"
    transcripts_encontrados: Dict[str, Path] = {}

    if brain_dir.exists():
        for item in brain_dir.iterdir():
            if item.is_dir():
                s_id = item.name
                # Tenta transcript_full.jsonl ou transcript.jsonl
                t_full = item / ".system_generated" / "logs" / "transcript_full.jsonl"
                t_light = item / ".system_generated" / "logs" / "transcript.jsonl"
                if t_full.exists():
                    transcripts_encontrados[s_id] = t_full
                elif t_light.exists():
                    transcripts_encontrados[s_id] = t_light

    print(f"[*] Total de sessoes detectadas no disco: {len(transcripts_encontrados)}")
    print(f"[*] Sessoes mapeadas via history.jsonl: {len(session_map)}")

    processadas = 0
    puladas_cache = 0
    erros = 0

    for s_id, t_path in transcripts_encontrados.items():
        # Determinar projeto
        map_info = session_map.get(s_id, {})
        ws = map_info.get("workspace")
        project_name = sanitize_project_name(ws) if ws else "antigravity_geral"

        if filter_project and filter_project.lower() not in project_name.lower():
            continue

        proj_dir = base_desktop_dir / project_name
        proj_dir.mkdir(parents=True, exist_ok=True)

        today_tag = date_ddmmyyyy(datetime.datetime.fromtimestamp(t_path.stat().st_mtime))
        target_md = proj_dir / f"{today_tag}_{s_id}.md"
        target_json = proj_dir / f"{today_tag}_{s_id}.json"

        # Verificacao de cache: se o arquivo de saida ja existe e e mais novo que o transcript (se nao for force)
        primary_target = target_md if export_format in ("md", "markdown") else target_json
        if not force and primary_target.exists() and primary_target.stat().st_mtime >= t_path.stat().st_mtime:
            puladas_cache += 1
            continue

        try:
            sync_session_to_disk(
                transcript_path=str(t_path),
                session_id=s_id,
                output_dir=str(base_desktop_dir),
                export_format=export_format,
                explicit_project=project_name,
                clean_legacy_json=True
            )
            processadas += 1
        except Exception as exc:
            erros += 1

    # Atualiza o indice geral consolidado
    atualizar_indice_geral(base_desktop_dir)

    print("\n" + "=" * 75)
    print(" [AIDD-SESSION-SYNC] SINCRONIZACAO CUMULATIVA FINALIZADA")
    print("=" * 75)
    print(f"[+] Sessoes Novas / Atualizadas:  {processadas}")
    print(f"[+] Sessoes Reutilizadas (Cache): {puladas_cache}")
    if erros > 0:
        print(f"[-] Erros ou transcripts vazios:  {erros}")
    print(f"[+] Indice Geral gerado em:       {base_desktop_dir / 'INDICE_GERAL.md'}")
    print("=" * 75)


def check_doctor() -> bool:
    print("=== [AIDD-SESSION-SYNC] Diagnostico de Ambiente (Doctor) ===")
    print(f"[+] Python: {sys.version.split()[0]} (OK)")

    t_file = detect_active_session_file()
    if t_file and t_file.exists():
        harness = detect_harness(t_file)
        print(f"[+] Sessao ativa detectada: {t_file}")
        print(f"[+] Harness identificado: {harness}")
    else:
        print("[-] Nenhuma sessao ativa detectada automaticamente.")

    desktop_dir = DEFAULT_DESKTOP_DIR
    print(f"[+] Destino padrao Desktop: {desktop_dir} (Existe: {desktop_dir.exists()})")

    local_bin = Path.home() / ".local" / "bin"
    print(f"[+] Diretorio global no PATH: {local_bin} (Existe: {local_bin.exists()})")

    print("\n[OK] Diagnostico concluido com sucesso.")
    return True


def run_audit(target_dir_str: str = ".") -> bool:
    print(f"=== [AIDD-CIRCUIT-BREAKER] Auditando Sincronizador de Sessao: {target_dir_str} ===")
    target_dir = Path(target_dir_str).resolve()
    errors = []

    skill_md = target_dir / "SKILL.md"
    if not skill_md.exists():
        skill_md = target_dir.parent / "SKILL.md"

    if skill_md.exists():
        content = skill_md.read_text(encoding="utf-8")
        m = re.search(r"^description:\s*(.*?)$", content, re.MULTILINE)
        if m:
            desc = m.group(1).strip()
            words = len(re.findall(r"\b[\w-]+\b", desc))
            if words > 25:
                errors.append(f"Micro-frontmatter excede 25 palavras: {words}")
            else:
                print(f"[+] Micro-Frontmatter aprovado: {words} palavras (limite: 25)")
    else:
        errors.append("SKILL.md nao localizado para auditoria de frontmatter.")

    if errors:
        print("\n[!] Violacoes detectadas:", file=sys.stderr)
        for err in errors:
            print(f"  [-] {err}", file=sys.stderr)
        return False

    print("\n[OK] Todos os gates do Sincronizador de Sessao foram aprovados.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Sincronizador Deterministico Universal de Historico de Sessao (faz-session)")
    parser.add_argument("--transcript", help="Caminho explicito para o arquivo transcript (.jsonl)")
    parser.add_argument("--id", dest="session_id", help="UUID da sessao a exportar")
    parser.add_argument("--project", dest="project_name", help="Filtrar ou forcar nome de projeto")
    parser.add_argument("--all", "--backfill", dest="sync_all", action="store_true", help="Sincronizar cumulativamente todas as sessoes existentes no disco")
    parser.add_argument("--output-dir", help="Diretorio customizado (padrao: Desktop/sessoes-agentes)")
    parser.add_argument("--output", help="Nome ou caminho customizado do arquivo final")
    parser.add_argument("--format", choices=["md", "json", "all"], default="md", help="Formato de exportacao (padrao: md)")
    parser.add_argument("--force", action="store_true", help="Forca sincronizacao ignorando cache")
    parser.add_argument("--doctor", action="store_true", help="Diagnostico de ambiente e deteccao de sessao")
    parser.add_argument("--audit", metavar="PASTA", nargs="?", const=".", help="Auditoria de conformidade dos gates")
    parser.add_argument("--update", action="store_true", help="Atualiza incrementalmente o arquivo existente")

    args = parser.parse_args()

    if args.doctor:
        ok = check_doctor()
        sys.exit(0 if ok else 1)

    if args.audit is not None:
        ok = run_audit(args.audit)
        sys.exit(0 if ok else 1)

    if args.sync_all:
        try:
            sync_all_sessions(
                output_dir=args.output_dir,
                filter_project=args.project_name,
                export_format=args.format,
                force=args.force
            )
            sys.exit(0)
        except Exception as e:
            print(f"[ERRO] Falha na sincronizacao em lote: {e}", file=sys.stderr)
            sys.exit(1)

    try:
        sync_session_to_disk(
            transcript_path=args.transcript,
            session_id=args.session_id,
            output_dir=args.output_dir,
            output_file=args.output,
            export_format=args.format,
            explicit_project=args.project_name
        )
    except Exception as e:
        print(f"[ERRO] Falha ao sincronizar sessao: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
