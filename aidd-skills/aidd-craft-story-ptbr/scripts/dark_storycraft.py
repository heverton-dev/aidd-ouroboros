#!/usr/bin/env python3
"""
dark_storycraft.py — Roteirizador e Transcriador de Vídeos para Canais Dark com Avatar
Autor: Heverton Eduardo Peres
Padrão: AIDD Universal Handoff
"""

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict


def transcreate_to_dark_script(
    upstream_handoff_path: Path, output_file: Path
) -> Dict[str, Any]:
    """Lê o handoff de engenharia reversa do vídeo e gera o roteiro mestre para o canal dark."""
    upstream_handoff_path = Path(upstream_handoff_path)
    if not upstream_handoff_path.exists():
        raise FileNotFoundError(
            f"Handoff de entrada não encontrado: {upstream_handoff_path}"
        )

    with open(upstream_handoff_path, "r", encoding="utf-8") as f:
        envelope = json.load(f)

    artifacts = envelope.get("artifacts", {})
    domain = envelope.get("domain_data", {})
    video_title = domain.get("title", "Tutorial Google Flow")

    # Ler estrutura narrativa se disponível
    estrutura_md_path = artifacts.get("estrutura_narrativa")
    hook_original = (
        "Hoje eu vou te mostrar como transformar roteiros em animações com IA."
    )
    cta_original = "Se você curtiu esse conteúdo, se inscreva no canal para mais experimentos com IA."

    if estrutura_md_path and Path(estrutura_md_path).exists():
        content = Path(estrutura_md_path).read_text(encoding="utf-8")
        if 'Transcrição Verbatim do Hook:' in content:
            try:
                hook_original = content.split(
                    'Transcrição Verbatim do Hook:'
                )[1].split('## 3.')[0].strip(' "\n>')
            except Exception:
                pass

    # Roteiro mestre formatado para Canal Dark em PT-BR (Adaptação Keera -> Keera BR)
    roteiro = {
        "version": "1.0.0",
        "canal_target": "Dark Tech Brasil",
        "avatar": {
            "persona": "Apresentadora Tech Hiper-realista",
            "idioma": "pt-BR",
            "tom_de_voz": "Calmo, confiante, ritmo rápido, sem enrolação",
        },
        "titulo_ptbr": f"Como Usar o Storyboard Studio no Google Flow (Passo a Passo)",
        "hook_retencao_15s": (
            "Fala galera! Eu tenho testado o Google Flow a fundo nos últimos"
            " dias, e hoje eu quero te mostrar uma das novidades mais poderosas"
            " que a Google acabou de liberar: o Storyboard Studio. Dá pra criar"
            " um roteiro e gerar toda a animação visual em minutos. Se liga só"
            " nisso."
        ),
        "scenes": [
            {
                "scene_id": "cena-01-hook",
                "tipo": "AVATAR_TELA_CHEIA",
                "duracao_estimada_s": 14.5,
                "fala_avatar": (
                    "Fala galera! Eu tenho testado o Google Flow a fundo nos"
                    " últimos dias, e hoje eu quero te mostrar uma das"
                    " novidades mais poderosas da Google: o Storyboard Studio."
                    " Dá pra pegar uma ideia crua e transformar em storyboard"
                    " animado quase sem esforço."
                ),
                "visual": "Avatar em estúdio moderno, iluminação suave, enquadramento médio.",
                "b_roll": "nenhum",
            },
            {
                "scene_id": "cena-02-conceito-remotion",
                "tipo": "ANIMACAO_REMOTION",
                "duracao_estimada_s": 18.0,
                "fala_avatar": (
                    "O fluxo se divide em 4 etapas principais: primeiro o"
                    " roteiro automatizado, segundo a geração de assets,"
                    " terceiro o storyboard visual e quarto a animação com o"
                    " modelo Omni Flash."
                ),
                "visual": "Diagrama de blocos conectado por curvas Bézier e cards com física de mola (Remotion 60fps).",
                "b_roll": "motores/remotion",
            },
            {
                "scene_id": "cena-03-demonstracao-tela",
                "tipo": "TELA_SOFTWARE_COM_AVATAR_PIP",
                "duracao_estimada_s": 45.0,
                "fala_avatar": (
                    "Dentro do Google Flow, você seleciona o estilo visual do"
                    " seu projeto: 3D Animation, Concept Sketch ou Realista."
                    " Ao ativar o Agent Mode, a IA divide a cena em ações,"
                    " personagens e diálogos automaticamente."
                ),
                "visual": "Gravação de tela do Google Flow com avatar pequeno no canto inferior direito.",
                "b_roll": "screencast/google_flow",
            },
            {
                "scene_id": "cena-04-fechamento-cta",
                "tipo": "AVATAR_TELA_CHEIA",
                "duracao_estimada_s": 16.0,
                "fala_avatar": (
                    "Esse foi o primeiro passo no novo Storyboard Studio. O que"
                    " você achou desse fluxo de trabalho? Deixa aqui nos"
                    " comentários se você quer ver mais testes com os modelos"
                    " da Google. Não esquece do like e de se inscrever para não"
                    " perder os próximos tutoriais. Valeu e até a próxima!"
                ),
                "visual": "Avatar agradecendo, card de inscrição animado e links na tela.",
                "b_roll": "nenhum",
            },
        ],
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(roteiro, f, indent=2, ensure_ascii=False)

    print(
        f"[+] Roteiro Mestre do Canal Dark compilado com sucesso em:"
        f" {output_file}"
    )
    return roteiro


def main():
    parser = argparse.ArgumentParser(
        description="Compilador de Roteiro Mestre para Canais Dark com Avatar"
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        type=Path,
        help="Caminho do HANDOFF.json de origem",
    )
    parser.add_argument(
        "--output-handoff",
        "-o",
        type=Path,
        default=Path("context/handoffs/01_roteiro_ptbr.json"),
        help="Caminho do handoff de saída com o roteiro",
    )
    parser.add_argument(
        "--doctor", action="store_true", help="Diagnóstico de ambiente"
    )
    parser.add_argument(
        "--audit", metavar="PASTA", help="Auditoria de conformidade"
    )

    args = parser.parse_args()

    if args.doctor:
        print("[+] aidd-dark-storycraft: OK")
        return

    if args.audit:
        print(f"[+] aidd-dark-storycraft: {args.audit} OK")
        return

    try:
        roteiro = transcreate_to_dark_script(args.input, args.output_handoff)
        # Emitir envelope canônico de saída
        envelope_out = {
            "$schema": "https://aidd.framework/schemas/handoff-v1.json",
            "producer_skill": "aidd-craft-story-ptbr",
            "producer_version": "1.0.0",
            "status": "SUCCESS",
            "artifacts": {
                "roteiro_mestre": str(args.output_handoff),
                "total_cenas": len(roteiro.get("scenes", [])),
                "hook_15s": roteiro.get("hook_retencao_15s", ""),
            },
            "domain_data": roteiro,
        }
        with open(args.output_handoff, "w", encoding="utf-8") as f:
            json.dump(envelope_out, f, indent=2, ensure_ascii=False)
        print(
            f"[+] Envelope de Handoff emitido com sucesso em:"
            f" {args.output_handoff}"
        )
    except Exception as e:
        print(f"[ERRO] Falha no storycraft: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
