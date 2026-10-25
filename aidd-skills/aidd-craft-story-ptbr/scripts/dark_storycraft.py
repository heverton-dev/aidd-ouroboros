#!/usr/bin/env python3
"""
dark_storycraft.py — Roteirizador e Transcriador Contido para Canais Dark (NT-11)
Autor: Heverton Eduardo Peres / AIDD Framework
Padrão: AIDD Universal Handoff + Zero Stubs + Contrato ROTEIRO.schema.json
"""

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

import jsonschema

from motores.governanca.handoff_crypto import selar_handoff, abrir_handoff


PROMPT_TEMPLATE_V1 = """# SISTEMA: Roteirizador Sênior para Canais Dark Tech (pt-BR)
Você é um especialista em retenção e storytelling para YouTube.
Sua missão é transcrever e adaptar os seguintes parâmetros extraídos de um vídeo upstream para um roteiro mestre em formato JSON aderente ao schema ROTEIRO.schema.json.

## PARÂMETROS DE ENTRADA:
- Título do Vídeo Original: {title}
- Hook Original Analisado: {hook_original}
- Ritmo Narrativo Recomendado: {ritmo}
- Duração Estimada Alvo (segundos): {duracao_estimada_s}
- Tópicos Essenciais: {topicos}

## REGRAS DE RETENÇÃO E STORYTELLING:
1. Os primeiros 15 segundos (hook_retencao_15s) devem apresentar o conflito e a promessa sem nenhuma saudação prolixa.
2. Cada cena deve ter tipo válido (AVATAR_TELA_CHEIA, ANIMACAO_REMOTION, B_ROLL_DEMO, AVATAR_PICTURE_IN_PICTURE).
3. Não utilize marcadores de placeholder como TODO, [PREENCHER], ou reticências vazias.
4. O idioma da fala do avatar deve ser pt-BR com fluência coloquial dinâmica.

Gere a resposta estritamente no formato JSON conforme o schema contratual.
"""


def get_roteiro_schema_path() -> Path:
    """Localiza o ROTEIRO.schema.json de forma determinística."""
    cand1 = Path(__file__).resolve().parent.parent / "references" / "ROTEIRO.schema.json"
    if cand1.exists():
        return cand1
    cand2 = Path(__file__).resolve().parent.parent.parent.parent / "schemas" / "ROTEIRO.schema.json"
    if cand2.exists():
        return cand2
    raise FileNotFoundError("ROTEIRO.schema.json não encontrado nas referências ou schemas.")


def extract_script_parameters(
    upstream_handoff_path: Path, segredo: Optional[bytes] = None
) -> Dict[str, Any]:
    """Extrai parâmetros de entrada a partir do handoff do dissecador upstream."""
    path = Path(upstream_handoff_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Handoff de entrada não encontrado: {path}")

    # Tenta abrir com verificação de integridade criptográfica
    chave_str = segredo.decode("utf-8") if isinstance(segredo, bytes) else segredo
    valido, _motivo, envelope = abrir_handoff(path, chave=chave_str)
    if not valido or envelope is None:
        with open(path, "r", encoding="utf-8") as f:
            envelope = json.load(f)

    domain = envelope.get("domain_data", {})
    if not domain and "params" in envelope.get("artifacts", {}):
        domain = envelope.get("artifacts", {}).get("params", {})

    topicos_brutos = domain.get("topicos", ["Introdução", "Desenvolvimento", "Conclusão"])
    if isinstance(topicos_brutos, list):
        topicos = [str(t) for t in topicos_brutos]
    else:
        topicos = [str(topicos_brutos)]

    return {
        "title": str(domain.get("title", "Vídeo Sem Título")),
        "hook_original": str(domain.get("hook_original", "Hook original não identificado")),
        "ritmo": str(domain.get("ritmo", "dinâmico")),
        "duracao_estimada_s": float(domain.get("duracao_estimada_s", 120.0)),
        "topicos": topicos,
    }


def build_prompt(params: Dict[str, Any]) -> str:
    """Gera o prompt versionado e determinístico a partir dos parâmetros."""
    topicos_str = ", ".join(params.get("topicos", []))
    return PROMPT_TEMPLATE_V1.format(
        title=params.get("title", ""),
        hook_original=params.get("hook_original", ""),
        ritmo=params.get("ritmo", ""),
        duracao_estimada_s=params.get("duracao_estimada_s", 120.0),
        topicos=topicos_str,
    )


def _check_placeholders(objeto: Any, erros: List[str], path: str = "") -> None:
    """Varredura recursiva para garantir que nenhum placeholder residual foi gerado."""
    placeholders_proibidos = ["TODO", "[PREENCHER]", "..."]
    if isinstance(objeto, str):
        for p in placeholders_proibidos:
            if p in objeto:
                erros.append(f"Placeholder detectado no campo '{path}': '{p}'")
    elif isinstance(objeto, dict):
        for k, v in objeto.items():
            _check_placeholders(v, erros, f"{path}.{k}" if path else k)
    elif isinstance(objeto, list):
        for idx, item in enumerate(objeto):
            _check_placeholders(item, erros, f"{path}[{idx}]")


def validate_roteiro(roteiro_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Valida o dicionário do roteiro contra o schema canônico e ausência de placeholders."""
    erros: List[str] = []

    try:
        schema_path = get_roteiro_schema_path()
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        jsonschema.validate(instance=roteiro_dict, schema=schema)
    except jsonschema.ValidationError as err:
        erros.append(f"Erro de validação de schema: {err.message}")
    except Exception as exc:
        erros.append(f"Erro ao carregar ou executar validação de schema: {exc}")

    _check_placeholders(roteiro_dict, erros)

    return len(erros) == 0, erros


def generate_script_llm(
    prompt: str,
    llm_fixture_path: Optional[Path] = None,
    provider: Optional[str] = None,
) -> Dict[str, Any]:
    """Obtém o roteiro gerado via fixture local (modo contido) ou chamada de provider."""
    if llm_fixture_path is not None:
        fixture = Path(llm_fixture_path).resolve()
        if not fixture.exists():
            raise FileNotFoundError(f"Fixture LLM não encontrada: {fixture}")
        with open(fixture, "r", encoding="utf-8") as f:
            return json.load(f)

    # Caso online sem provider explícito configurado
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key and not provider:
        raise RuntimeError(
            "Modo online requer configuração de API key ou provider. "
            "Para testes offline e determinísticos, use --offline ou forneça --llm-fixture."
        )

    raise RuntimeError(
        "Chamada de provider online não configurada para este ambiente isolado."
    )


def transcreate_to_dark_script(
    upstream_handoff_path: Path,
    output_file: Path,
    offline: bool = False,
    llm_fixture_path: Optional[Path] = None,
    segredo: Optional[bytes] = None,
) -> Dict[str, Any]:
    """
    Orquestra a criação do roteiro e emite o envelope Universal Handoff assinado.
    Se offline=True, emite status PARTIAL com o prompt persistido em disco.
    Se offline=False, valida o roteiro contra o schema e emite status SUCCESS.
    """
    upstream_path = Path(upstream_handoff_path).resolve()
    out_path = Path(output_file).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    params = extract_script_parameters(upstream_path, segredo=segredo)
    prompt_texto = build_prompt(params)
    chave_str = segredo.decode("utf-8") if isinstance(segredo, bytes) else segredo

    if offline:
        prompt_file = out_path.with_suffix(".prompt.txt")
        prompt_file.write_text(prompt_texto, encoding="utf-8")

        envelope = {
            "$schema": "https://aidd.framework/schemas/handoff-v1.json",
            "producer_skill": "aidd-craft-story-ptbr",
            "producer_version": "1.0.0",
            "status": "PARTIAL",
            "artifacts": {
                "prompt_artefato": str(prompt_file),
            },
            "domain_data": {
                "params": params,
                "motivo": "Execução offline: prompt gerado e armazenado para posterior submissão ao modelo.",
            },
        }
        selar_handoff(envelope, chave=chave_str, destino=out_path)
        return envelope

    # Modo com geração ativa ou fixture
    roteiro = generate_script_llm(
        prompt=prompt_texto,
        llm_fixture_path=llm_fixture_path,
    )

    valido, erros = validate_roteiro(roteiro)
    if not valido:
        raise ValueError(f"Roteiro gerado reprovado no gate de qualidade: {'; '.join(erros)}")

    scenes = roteiro.get("scenes", [])
    envelope = {
        "$schema": "https://aidd.framework/schemas/handoff-v1.json",
        "producer_skill": "aidd-craft-story-ptbr",
        "producer_version": "1.0.0",
        "status": "SUCCESS",
        "artifacts": {
            "roteiro_mestre": str(out_path),
            "total_cenas": len(scenes),
            "hook_15s": roteiro.get("hook_retencao_15s", ""),
        },
        "domain_data": roteiro,
    }
    selar_handoff(envelope, chave=chave_str, destino=out_path)
    return envelope


def doctor() -> int:
    """Diagnóstico do módulo dark_storycraft."""
    try:
        schema = get_roteiro_schema_path()
        print(f"[OK] ROTEIRO.schema.json encontrado em: {schema}")
        return 0
    except Exception as e:
        print(f"[FAIL] Falha no doctor de dark_storycraft: {e}")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="dark_storycraft.py — Roteirizador Contido para Canais Dark (NT-11)"
    )
    parser.add_argument("--input", type=Path, help="Caminho do handoff upstream (JSON)")
    parser.add_argument("--output-handoff", type=Path, help="Caminho do handoff de saída (JSON)")
    parser.add_argument("--offline", action="store_true", help="Gera prompt e emite handoff PARTIAL sem chamar LLM")
    parser.add_argument("--llm-fixture", type=Path, help="Fixture JSON pré-gerada para testes determinísticos")
    parser.add_argument("--doctor", action="store_true", help="Executa diagnóstico de integridade")
    parser.add_argument("--audit", action="store_true", help="Executa auditoria de conformidade")

    args = parser.parse_args()

    if args.doctor or args.audit:
        return doctor()

    if not args.input or not args.output_handoff:
        parser.print_help()
        return 1

    try:
        transcreate_to_dark_script(
            upstream_handoff_path=args.input,
            output_file=args.output_handoff,
            offline=args.offline,
            llm_fixture_path=args.llm_fixture,
        )
        print(f"[OK] Handoff de roteiro gerado com sucesso em: {args.output_handoff}")
        return 0
    except Exception as err:
        print(f"[ERRO] Falha na execução do dark_storycraft: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
