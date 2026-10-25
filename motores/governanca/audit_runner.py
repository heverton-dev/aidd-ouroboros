#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_runner.py — Executor Mestre de Quality Gates da Branch
Padrão: AIDD Universal Architecture / Zero Stubs / Extreme Token Economy

Verifica:
  1. Gate AST: Sintaxe 100% válida e zero stubs (pass/TODO/NotImplementedError).
  2. Gate Micro-Frontmatter: Limite <= 25 palavras nas descrições de SKILL.md.
  3. Gate de Governança Fractal: Cada skill e pipeline deve ter seu AGENTS.md compacto (< 450 palavras).
  4. Gate de Completude Anatômica Enterprise: Circuit Breaker contra skills/pipelines ad-hoc ou anêmicas.
  5. Gate de Testes: Execução da suíte pytest com 100% de aprovação.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
import time

# Adicionar raiz da branch ao sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from motores.governanca.gate_ast import scan_path
from motores.governanca.gate_factory_completeness import executar_circuit_breaker


def auditar_micro_frontmatter(root: Path) -> tuple[bool, list[str]]:
    skills = (
        list(root.glob("aidd-skills/*/SKILL.md"))
        + list(root.glob("aidd-pipelines/*/skills/*/SKILL.md"))
    )
    skills = list(dict.fromkeys(skills))
    violations: list[str] = []

    for sk in skills:
        try:
            content = sk.read_text(encoding="utf-8")
        except Exception as exc:
            violations.append(f"{sk}: Erro ao ler ({exc})")
            continue

        desc_lines = [l for l in content.splitlines() if l.strip().startswith("description:")]
        if not desc_lines:
            violations.append(f"{sk.parent.name}: Campo 'description:' ausente no frontmatter.")
            continue

        words = len(desc_lines[0].replace("description:", "").strip().split())
        if words > 25:
            violations.append(f"{sk.parent.name}: 'description' excede 25 palavras ({words} palavras).")

    return (len(violations) == 0, violations)


def auditar_agents_governance(root: Path) -> tuple[bool, list[str]]:
    skills = [p for p in (root / "aidd-skills").glob("*") if p.is_dir() and not p.name.startswith(".")]
    pipelines = [p for p in (root / "aidd-pipelines").glob("*") if p.is_dir() and not p.name.startswith(".")]
    violations: list[str] = []

    for folder in skills + pipelines:
        agents_file = folder / "AGENTS.md"
        if not agents_file.exists():
            violations.append(f"{folder.name}: Arquivo AGENTS.md obrigatório ausente.")
            continue

        text = agents_file.read_text(encoding="utf-8")
        words = len(text.split())
        if words > 450:
            violations.append(f"{folder.name}/AGENTS.md: Excede limite de densidade de contexto ({words} palavras; máx: 450).")

    return (len(violations) == 0, violations)


def rodar_testes_pytest(root: Path) -> tuple[bool, str]:
    tests_dir = root / "tests"
    if not tests_dir.is_dir():
        return True, "Nenhum diretório tests/ encontrado."

    cmd = [
        sys.executable, "-m", "pytest", "-q", "tests",
        "--ignore=tests/negative",
        "--ignore=tests/negative-brand"
    ]
    try:
        res = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, timeout=120)
        output = (res.stdout + res.stderr).strip()
        return (res.returncode == 0, output)
    except Exception as exc:
        return False, f"Falha ao executar pytest: {exc}"


def main():
    parser = argparse.ArgumentParser(description="Auditor Geral de Quality Gates da Branch")
    parser.add_argument("--skip-pytest", action="store_true", help="Pula execução de testes pytest")
    args = parser.parse_args()

    root = Path.cwd().resolve()
    print("=" * 70)
    print(" 🛡️  AUDITORIA DE QUALITY GATES FRACTAIS — BRANCH feature-matt-penny")
    print("=" * 70)
    start_time = time.time()

    # 1. Gate AST & Zero Stubs
    print("\n[1/5] Executando Quality Gate de AST e Zero-Stubs...")
    ast_res = scan_path(root)
    if not ast_res.passed:
        print(f"[!] FALHA no Gate AST ({len(ast_res.errors)} erros):", file=sys.stderr)
        for e in ast_res.errors[:10]:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)
    print(f"  [OK] {ast_res.total_checked} arquivos Python validados com 100% de sintaxe e zero stubs.")

    # 2. Gate Micro-Frontmatter
    print("\n[2/5] Executando Quality Gate de Micro-Frontmatter (<= 25 palavras)...")
    mf_ok, mf_errs = auditar_micro_frontmatter(root)
    if not mf_ok:
        print(f"[!] FALHA no Micro-Frontmatter ({len(mf_errs)} erros):", file=sys.stderr)
        for e in mf_errs:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)
    print("  [OK] Todas as skills atendem ao limite de 25 palavras.")

    # 3. Gate Governança AGENTS.md
    print("\n[3/5] Executando Quality Gate de Governança AGENTS.md (< 450 palavras)...")
    gov_ok, gov_errs = auditar_agents_governance(root)
    if not gov_ok:
        print(f"[!] FALHA na Governança AGENTS.md ({len(gov_errs)} pendências):", file=sys.stderr)
        for e in gov_errs:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)
    print("  [OK] Todos os módulos possuem AGENTS.md compacto e em conformidade.")

    # 4. Gate de Completude Anatômica Enterprise (Circuit Breaker)
    print("\n[4/5] Executando Quality Gate de Completude Anatômica Enterprise (Circuit Breaker)...")
    comp_ok, comp_errs = executar_circuit_breaker(root)
    if not comp_ok:
        print(f"\n[💥 CIRCUIT BREAKER DESARMADO] Detectada anomia/criação ad-hoc ({len(comp_errs)} falhas estruturais):", file=sys.stderr)
        for e in comp_errs[:15]:
            print(f"  - {e}", file=sys.stderr)
        print("\n[!] ERRO FATAL: Nenhuma skill ou pipeline pode ser criada fora da meta-fábrica canônica.", file=sys.stderr)
        sys.exit(1)
    print("  [OK] Todas as skills e pipelines possuem anatomia enterprise canônica completa.")

    # 5. Suíte Pytest
    if not args.skip_pytest:
        print("\n[5/5] Executando Suíte de Testes Reais (Pytest)...")
        pt_ok, pt_out = rodar_testes_pytest(root)
        if not pt_ok:
            print("[!] FALHA na suíte Pytest:\n" + pt_out, file=sys.stderr)
            sys.exit(1)
        print("  [OK] Testes automatizados 100% verdes.")
    else:
        print("\n[5/5] Pytest ignorado via flag --skip-pytest.")

    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print(f" 🚀 AUDITORIA CONCLUÍDA COM 100% DE SUCESSO EM {elapsed:.2f}s.")
    print("=" * 70)
    sys.exit(0)


if __name__ == "__main__":
    main()
