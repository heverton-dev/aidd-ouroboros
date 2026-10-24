#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gate_ast.py — Quality Gate Determinístico de AST e Anti-Stubs (Zero-Stubs Standard)
Garante que nenhum arquivo Python da branch ou de artefatos gerados contenha:
  1. Erros de sintaxe ou indentação (SyntaxError, IndentationError).
  2. Blocos vazios mascarados com 'pass' ou '...' em funções de negócio.
  3. 'raise NotImplementedError' em código operacional.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
import sys
from typing import List, Optional

EXCLUDED_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    "dist", "build", ".mypy_cache", ".pytest_cache", ".cache"
}


@dataclass
class GateResult:
    passed: bool
    total_checked: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class StubVisitor(ast.NodeVisitor):
    def __init__(self, filename: str):
        self.filename = filename
        self.violations: List[str] = []

    def _is_abstract_or_protocol(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id in {"abstractmethod", "overload"}:
                return True
            if isinstance(decorator, ast.Attribute) and decorator.attr in {"abstractmethod", "overload"}:
                return True
        return False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_function(node)
        self.generic_visit(node)

    def _check_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        if self._is_abstract_or_protocol(node):
            return

        body = node.body
        # Ignora docstring se for primeiro elemento
        statements = body
        if statements and isinstance(statements[0], ast.Expr) and isinstance(statements[0].value, ast.Constant) and isinstance(statements[0].value.value, str):
            statements = body[1:]

        if not statements:
            self.violations.append(
                f"{self.filename}:{node.lineno}: Função '{node.name}' possui corpo vazio sem implementação."
            )
            return

        if len(statements) == 1:
            single = statements[0]
            # Detecta 'pass' solitário
            if isinstance(single, ast.Pass):
                self.violations.append(
                    f"{self.filename}:{node.lineno}: Função '{node.name}' contém apenas 'pass' (Stub Proibido)."
                )
            # Detecta '...' solitário
            elif isinstance(single, ast.Expr) and isinstance(single.value, ast.Constant) and single.value.value is ...:
                self.violations.append(
                    f"{self.filename}:{node.lineno}: Função '{node.name}' contém apenas '...' (Elipse / Stub Proibido)."
                )
            # Detecta raise NotImplementedError
            elif isinstance(single, ast.Raise):
                exc = single.exc
                if isinstance(exc, ast.Name) and exc.id == "NotImplementedError":
                    self.violations.append(
                        f"{self.filename}:{node.lineno}: Função '{node.name}' levanta 'NotImplementedError' (Stub Proibido)."
                    )
                elif isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name) and exc.func.id == "NotImplementedError":
                    self.violations.append(
                        f"{self.filename}:{node.lineno}: Função '{node.name}' levanta 'NotImplementedError()' (Stub Proibido)."
                    )


def scan_file(file_path: Path) -> List[str]:
    violations: List[str] = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as exc:
        return [f"{file_path}: Erro ao ler arquivo ({exc})"]

    try:
        tree = ast.parse(content, filename=str(file_path))
    except SyntaxError as exc:
        return [f"{file_path}:{exc.lineno}: Erro de sintaxe: {exc.msg}"]

    visitor = StubVisitor(filename=str(file_path))
    visitor.visit(tree)
    violations.extend(visitor.violations)
    return violations


def scan_path(target_path: Path) -> GateResult:
    result = GateResult(passed=True)
    target = target_path.resolve()

    if target.is_file():
        files = [target] if target.suffix == ".py" else []
    else:
        files = []
        for p in sorted(target.rglob("*.py")):
            rel_parts = p.relative_to(target).parts
            if any(part in EXCLUDED_DIRS for part in rel_parts):
                continue
            files.append(p)

    for f in files:
        result.total_checked += 1
        errs = scan_file(f)
        if errs:
            result.passed = False
            result.errors.extend(errs)

    return result


def main(argv: Optional[List[str]] = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    target = Path(argv[0]) if argv else Path.cwd()

    print(f"=== [GATE AST] Auditoria Anti-Stubs e Sintaxe: {target} ===")
    res = scan_path(target)
    print(f"[*] Total de arquivos inspecionados: {res.total_checked}")

    if not res.passed:
        print(f"[!] FALHA: {len(res.errors)} violação(ões) detectada(s):", file=sys.stderr)
        for err in res.errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"[OK] SUCESSO: Todos os {res.total_checked} arquivos atendem à regra de Zero Stubs e sintaxe válida.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
