#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
handoff_crypto.py — Protocolo Canônico de Integridade Criptográfica e Passagem por Ponteiros (Pointer Passing)
Padrão: AIDD Universal Architecture / Zero-Token-Waste Standard

Permite que skills, pipelines e swarms transacionem dados com:
  1. Integridade imutável via HMAC-SHA256 (contrato body + seal).
  2. Economia extrema de tokens: os payloads contêm apenas referências/ponteiros locais e hashes dos arquivos,
     evitando o despejo de megabytes de texto nos prompts dos agentes.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import hmac
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, Optional, Tuple, Union
import warnings


def obter_chave(chave_opcional: Optional[str] = None) -> str:
    """
    Obtém a chave secreta HMAC a partir do parâmetro explícito ou do ambiente
    (OUROBOROS_HMAC_SECRET com fallback para AIDD_HANDOFF_KEY).
    Lança RuntimeError se não estiver configurada (fail-closed).
    """
    if chave_opcional:
        return chave_opcional

    chave_env = os.environ.get("OUROBOROS_HMAC_SECRET") or os.environ.get("AIDD_HANDOFF_KEY")
    if chave_env and chave_env.strip():
        return chave_env.strip()

    raise RuntimeError(
        "Chave de assinatura HMAC não configurada. Defina a variável de ambiente AIDD_HANDOFF_KEY ou OUROBOROS_HMAC_SECRET."
    )


def calcular_sha256_arquivo(caminho: Path | str) -> str:
    path = Path(caminho)
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo alvo para hash não encontrado: {path}")
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def calcular_hmac_dict(dados: Dict[str, Any], chave: Optional[str] = None) -> str:
    chave_resolvida = obter_chave(chave)
    conteudo_canonico = json.dumps(dados, sort_keys=True, ensure_ascii=False)
    return hmac.new(
        chave_resolvida.encode("utf-8"),
        conteudo_canonico.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def selar(
    dados: Dict[str, Any],
    chave: Optional[str] = None,
    key_id: str = "ouroboros-v2"
) -> Dict[str, Any]:
    """
    Sela um dicionário de dados gerando um envelope canônico {body, seal}.
    Lança ValueError se os dados já contiverem 'body' ou 'seal'.
    """
    if not isinstance(dados, dict):
        raise TypeError("Dados para selar devem ser um dicionário.")
    if "body" in dados or "seal" in dados:
        raise ValueError("Objeto já selado: envelope já contém 'body' ou 'seal'.")

    chave_resolvida = obter_chave(chave)
    conteudo_canonico = json.dumps(dados, sort_keys=True, ensure_ascii=False)
    assinatura = hmac.new(
        chave_resolvida.encode("utf-8"),
        conteudo_canonico.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    sealed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return {
        "body": dados,
        "seal": {
            "algorithm": "HMAC-SHA256",
            "key_id": key_id,
            "hmac_sha256": assinatura,
            "sealed_at": sealed_at,
        }
    }


def abrir(
    envelope_ou_path: Dict[str, Any] | Path | str,
    chave: Optional[str] = None,
    verificar_disco: bool = True,
    **kwargs: Any
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Abre e valida a autenticidade de um envelope {body, seal} ou legado {payload, hmac_sha256}.
    Retorna (valido, motivo, corpo). Em caso de sucesso, motivo == 'OK'.
    """
    try:
        chave_resolvida = obter_chave(chave)
    except RuntimeError as exc:
        return False, str(exc), {}

    if isinstance(envelope_ou_path, (str, Path)):
        p = Path(envelope_ou_path)
        if not p.is_file():
            return False, f"Envelope não encontrado no caminho: {p}", {}
        try:
            with open(p, "r", encoding="utf-8") as f:
                envelope = json.load(f)
        except Exception as exc:
            return False, f"Erro ao desserializar JSON do envelope: {exc}", {}
    else:
        envelope = envelope_ou_path

    if not isinstance(envelope, dict):
        return False, "Envelope não é um dicionário JSON válido.", {}

    # Mapear parâmetros de verificação de disco
    checagem_disco = verificar_disco
    if "verificar_existencia_disco" in kwargs:
        checagem_disco = bool(kwargs["verificar_existencia_disco"])
    elif "verificar_integridade_disco" in kwargs:
        checagem_disco = bool(kwargs["verificar_integridade_disco"])

    # Formato novo: body + seal
    if "body" in envelope and "seal" in envelope:
        body = envelope["body"]
        seal = envelope["seal"]
        if not isinstance(seal, dict) or "hmac_sha256" not in seal:
            return False, "Selo incompleto: 'seal' inválido ou 'hmac_sha256' ausente.", {}

        assinatura_esperada = seal["hmac_sha256"]
        assinatura_calculada = calcular_hmac_dict(body, chave_resolvida)
        if not hmac.compare_digest(assinatura_calculada, assinatura_esperada):
            return False, "Violação de Integridade: assinatura HMAC-SHA256 não confere (body foi adulterado).", {}

        # Se contiver espelhamento legado de payload/hmac_sha256, validar integridade do espelho também
        if "payload" in envelope and envelope["payload"] != body:
            return False, "Violação de Integridade: divergência entre payload e body espelhados.", {}
        if "hmac_sha256" in envelope and not hmac.compare_digest(str(envelope["hmac_sha256"]), assinatura_esperada):
            return False, "Violação de Integridade: hmac_sha256 divergente do selo.", {}

        corpo = body

    # Formato legado: payload + hmac_sha256
    elif "payload" in envelope and "hmac_sha256" in envelope:
        warnings.warn(
            "Envelope em formato legado. Migre para 'body' + 'seal'.",
            DeprecationWarning,
            stacklevel=2
        )
        payload = envelope["payload"]
        assinatura_esperada = envelope["hmac_sha256"]
        assinatura_calculada = calcular_hmac_dict(payload, chave_resolvida)
        if not hmac.compare_digest(assinatura_calculada, assinatura_esperada):
            return False, "Violação de Integridade: assinatura HMAC-SHA256 não confere (payload foi adulterado).", {}
        corpo = payload
    else:
        return False, "Envelope incompleto: formato desconhecido ou campos obrigatórios ausentes.", {}

    if checagem_disco:
        pointers = corpo.get("artifacts_pointers", {})
        if isinstance(pointers, dict):
            for nome, info in pointers.items():
                if isinstance(info, dict) and info.get("sha256"):
                    caminho_arquivo = Path(info["path"])
                    if not caminho_arquivo.is_file():
                        return False, f"Artefato apontado '{nome}' não existe no disco: {caminho_arquivo}", {}
                    sha_atual = calcular_sha256_arquivo(caminho_arquivo)
                    if sha_atual != info["sha256"]:
                        return False, f"Adulteração no disco: o hash de '{nome}' ({sha_atual}) difere do manifesto ({info['sha256']}).", {}
        elif isinstance(pointers, list):
            for item in pointers:
                if isinstance(item, dict) and item.get("sha256"):
                    caminho_arquivo = Path(item.get("path", ""))
                    if not caminho_arquivo.is_file():
                        return False, f"Artefato apontado '{item.get('name', 'item')}' não existe no disco: {caminho_arquivo}", {}
                    sha_atual = calcular_sha256_arquivo(caminho_arquivo)
                    if sha_atual != item["sha256"]:
                        return False, "Adulteração no disco: o hash difere do manifesto.", {}

    return True, "OK", corpo


def criar_envelope_handoff(
    origem_skill: str,
    status_ou_artefatos: Any = "SUCCESS",
    artefatos_ou_metadados: Any = None,
    metadados: Optional[Dict[str, Any]] = None,
    caminho_saida: Optional[Path | str] = None,
    chave: Optional[str] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Gera um envelope canônico com hashes SHA-256 de todos os artefatos apontados
    e assina todo o payload via HMAC-SHA256, produzindo estrutura {body, seal}
    e mantendo espelhamento {payload, hmac_sha256} para máxima retrocompatibilidade.
    """
    chave_resolvida = obter_chave(chave)

    # Suporte polimórfico a chamadas posicionais:
    # 1. criar_envelope_handoff(origem, artefatos, metadados)
    # 2. criar_envelope_handoff(origem, status, artefatos, metadados)
    if isinstance(status_ou_artefatos, (list, dict)):
        artefatos = status_ou_artefatos
        meta = artefatos_ou_metadados if isinstance(artefatos_ou_metadados, dict) else (metadados or {})
        status = kwargs.get("status", "SUCCESS")
    else:
        status = str(status_ou_artefatos or "SUCCESS")
        artefatos = kwargs.get("artefatos", artefatos_ou_metadados)
        meta = kwargs.get("metadados", metadados) or {}

    artefatos_processados: Union[Dict[str, Any], list[Any]] = {}
    if isinstance(artefatos, dict):
        proc_dict: Dict[str, Any] = {}
        for nome_chave, caminho in artefatos.items():
            p = Path(caminho)
            if p.exists() and p.is_file():
                proc_dict[nome_chave] = {
                    "path": str(p.resolve()),
                    "sha256": calcular_sha256_arquivo(p),
                    "tamanho_bytes": p.stat().st_size
                }
            else:
                proc_dict[nome_chave] = {
                    "path": str(p),
                    "sha256": None,
                    "tamanho_bytes": 0,
                    "alerta": "Arquivo ainda não materializado no disco"
                }
        artefatos_processados = proc_dict
    elif isinstance(artefatos, list):
        proc_list: list[Any] = []
        for item in artefatos:
            if isinstance(item, (str, Path)):
                p = Path(item)
                if p.exists() and p.is_file():
                    proc_list.append({
                        "name": p.name,
                        "path": str(p.resolve()),
                        "sha256": calcular_sha256_arquivo(p),
                        "tamanho_bytes": p.stat().st_size
                    })
                else:
                    proc_list.append({
                        "name": str(item),
                        "path": str(item),
                        "sha256": None,
                        "tamanho_bytes": 0,
                    })
            elif isinstance(item, dict):
                proc_list.append(item)
        artefatos_processados = proc_list

    payload = {
        "schema_version": "2.0-crypto",
        "producer_skill": origem_skill,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": status,
        "artifacts_pointers": artefatos_processados,
        "domain_metadata": meta
    }

    envelope_selado = selar(payload, chave=chave_resolvida)

    envelope = {
        "envelope_format": "AIDD-CANONICAL-HANDOFF",
        "signature_algorithm": "HMAC-SHA256",
        "hmac_sha256": envelope_selado["seal"]["hmac_sha256"],
        "payload": payload,
        "body": envelope_selado["body"],
        "seal": envelope_selado["seal"],
    }

    if caminho_saida:
        out_p = Path(caminho_saida)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(envelope, f, indent=2, ensure_ascii=False)

    return envelope


def verificar_envelope_handoff(
    envelope_ou_path: Dict[str, Any] | Path | str,
    chave: Optional[str] = None,
    verificar_integridade_disco: bool = True,
    **kwargs: Any
) -> Tuple[bool, str]:
    """
    Verifica se a assinatura HMAC bate com o payload e se os arquivos referenciados
    não foram adulterados no disco.
    """
    valido, motivo, _ = abrir(
        envelope_ou_path,
        chave=chave,
        verificar_disco=verificar_integridade_disco,
        **kwargs
    )
    if valido:
        return True, "Envelope 100% íntegro e autêntico."
    return False, motivo


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
        parser.print_help(sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

