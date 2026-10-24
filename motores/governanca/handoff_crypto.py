#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
handoff_crypto.py — Protocolo Canônico de Integridade Criptográfica e Passagem por Ponteiros (Pointer Passing)
Padrão: AIDD Universal Architecture / Zero-Token-Waste Standard

Permite que skills, pipelines e swarms transacionem dados com:
  1. Integridade imutável via HMAC-SHA256.
  2. Economia extrema de tokens: os payloads contêm apenas referências/ponteiros locais e hashes dos arquivos,
     evitando o despejo de megabytes de texto nos prompts dos agentes.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import hmac
import json
from pathlib import Path
import sys
from typing import Any, Dict, Optional, Tuple

DEFAULT_SECRET = "aidd-secret-penny-harness-2026"


def calcular_sha256_arquivo(caminho: Path | str) -> str:
    path = Path(caminho)
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo alvo para hash não encontrado: {path}")
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def calcular_hmac_dict(dados: Dict[str, Any], chave: str = DEFAULT_SECRET) -> str:
    conteudo_canonico = json.dumps(dados, sort_keys=True, ensure_ascii=False)
    return hmac.new(
        chave.encode("utf-8"),
        conteudo_canonico.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def criar_envelope_handoff(
    origem_skill: str,
    status: str = "SUCCESS",
    artefatos: Optional[Dict[str, str | Path]] = None,
    metadados: Optional[Dict[str, Any]] = None,
    caminho_saida: Optional[Path | str] = None,
    chave: str = DEFAULT_SECRET
) -> Dict[str, Any]:
    """
    Gera um envelope canônico com hashes SHA-256 de todos os artefatos apontados
    e assina todo o payload via HMAC-SHA256.
    """
    artefatos_processados: Dict[str, Dict[str, Any]] = {}
    if artefatos:
        for nome_chave, caminho in artefatos.items():
            p = Path(caminho)
            if p.exists() and p.is_file():
                artefatos_processados[nome_chave] = {
                    "path": str(p.resolve()),
                    "sha256": calcular_sha256_arquivo(p),
                    "tamanho_bytes": p.stat().st_size
                }
            else:
                artefatos_processados[nome_chave] = {
                    "path": str(p),
                    "sha256": None,
                    "tamanho_bytes": 0,
                    "alerta": "Arquivo ainda não materializado no disco"
                }

    payload = {
        "schema_version": "2.0-crypto",
        "producer_skill": origem_skill,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": status,
        "artifacts_pointers": artefatos_processados,
        "domain_metadata": metadados or {}
    }

    assinatura = calcular_hmac_dict(payload, chave)
    envelope = {
        "envelope_format": "AIDD-CANONICAL-HANDOFF",
        "signature_algorithm": "HMAC-SHA256",
        "hmac_sha256": assinatura,
        "payload": payload
    }

    if caminho_saida:
        out_p = Path(caminho_saida)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(envelope, f, indent=2, ensure_ascii=False)

    return envelope


def verificar_envelope_handoff(
    envelope_ou_path: Dict[str, Any] | Path | str,
    chave: str = DEFAULT_SECRET,
    verificar_integridade_disco: bool = True
) -> Tuple[bool, str]:
    """
    Verifica se a assinatura HMAC bate com o payload e se os arquivos referenciados
    não foram adulterados no disco.
    """
    if isinstance(envelope_ou_path, (str, Path)):
        p = Path(envelope_ou_path)
        if not p.is_file():
            return False, f"Envelope não encontrado no caminho: {p}"
        try:
            with open(p, "r", encoding="utf-8") as f:
                envelope = json.load(f)
        except Exception as exc:
            return False, f"Erro ao desserializar JSON do envelope: {exc}"
    else:
        envelope = envelope_ou_path

    if not isinstance(envelope, dict):
        return False, "Envelope não é um dicionário JSON válido."

    if "payload" not in envelope or "hmac_sha256" not in envelope:
        return False, "Envelope incompleto: campos 'payload' e/ou 'hmac_sha256' ausentes."

    payload = envelope["payload"]
    assinatura_esperada = envelope["hmac_sha256"]
    assinatura_calculada = calcular_hmac_dict(payload, chave)

    if assinatura_calculada != assinatura_esperada:
        return False, "Violação de Integridade: assinatura HMAC-SHA256 não confere (payload foi adulterado)."

    if verificar_integridade_disco:
        pointers = payload.get("artifacts_pointers", {})
        for nome, info in pointers.items():
            if isinstance(info, dict) and info.get("sha256"):
                caminho_arquivo = Path(info["path"])
                if not caminho_arquivo.is_file():
                    return False, f"Artefato apontado '{nome}' não existe no disco: {caminho_arquivo}"
                sha_atual = calcular_sha256_arquivo(caminho_arquivo)
                if sha_atual != info["sha256"]:
                    return False, f"Adulteração no disco: o hash de '{nome}' ({sha_atual}) difere do manifesto ({info['sha256']})."

    return True, "Envelope 100% íntegro e autêntico."


def main():
    parser = argparse.ArgumentParser(description="Utilitário CLI de Integridade HMAC-SHA256 e Pointer Passing")
    subparsers = parser.add_subparsers(dest="command")

    verify_p = subparsers.add_parser("verify", help="Verifica a autenticidade e integridade de um arquivo de handoff")
    verify_p.add_argument("path", help="Caminho do arquivo JSON de handoff")
    verify_p.add_argument("--skip-disk", action="store_true", help="Pula verificação dos arquivos no disco")

    args = parser.parse_args()
    if args.command == "verify":
        ok, msg = verificar_envelope_handoff(args.path, verificar_integridade_disco=not args.skip_disk)
        if ok:
            print(f"[OK] {msg}")
            sys.exit(0)
        else:
            print(f"[!] ERRO: {msg}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
