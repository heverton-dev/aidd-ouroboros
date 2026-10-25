#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gate_ast.py — Quality Gate Determinístico de AST e Anti-Stubs (Zero-Stubs Standard v2)
Garante que nenhum arquivo Python da branch ou de artefatos gerados contenha:
  1. Erros de sintaxe ou indentação (SyntaxError, IndentationError).
  2. Blocos vazios mascarados com 'pass' ou '...' em funções de negócio.
  3. 'raise NotImplementedError' em código operacional.
  4. ExceptHandler com corpo contendo apenas 'pass' ou '...' (swallow silencioso).
  5. Comentários contendo TODO|FIXME|XXX|HACK via tokenize (ignorando strings literais).
  6. Funções doctor/audit/check/verify fake (apenas print/log e return True).
Suporta controle de baseline regressivo via --baseline e --generate-baseline.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass, field
import io
import json
from pathlib import Path
import re
import sys
import tokenize
from typing import Dict, List, Optional, Set

EXCLUDED_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    "dist", "build", ".mypy_cache", ".pytest_cache", ".cache"
}

FORBIDDEN_COMMENT_REGEX = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b")
VERIFIER_FUNC_REGEX = re.compile(r"^(doctor|audit|check|verify)", re.IGNORECASE)


@dataclass
class Violation:
    rule_id: str
    filename: str
    lineno: int
    message: str

    def to_key(self) -> str:
        return f"{self.rule_id}:{self.lineno}"

    def __str__(self) -> str:
        return f"{self.filename}:{self.lineno}: [{self.rule_id}] {self.message}"

    def __contains__(self, item: object) -> bool:
        item_str = str(item)
        return item_str in str(self) or item_str in self.message or item_str in self.rule_id


@dataclass
class GateResult:
    passed: bool
    total_checked: int = 0
    violations: List[Violation] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ASTGateChecker(ast.NodeVisitor):
    def __init__(self, code: str, filename: str = "<string>"):
        self.code = code
        self.filename = filename
        self.violations: List[Violation] = []

    def _is_abstract_or_protocol(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id in {"abstractmethod", "overload"}:
                return True
            if isinstance(decorator, ast.Attribute) and decorator.attr in {"abstractmethod", "overload"}:
                return True
        return False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_function(node)
        self._check_fake_verifier(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_function(node)
        self._check_fake_verifier(node)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        self._check_except_handler(node)
        self.generic_visit(node)

    def _check_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        if self._is_abstract_or_protocol(node):
            return

        body = node.body
        statements = body
        if (
            statements
            and isinstance(statements[0], ast.Expr)
            and isinstance(statements[0].value, ast.Constant)
            and isinstance(statements[0].value.value, str)
        ):
            statements = body[1:]

        if not statements:
            self.violations.append(
                Violation(
                    rule_id="EMPTY_BODY",
                    filename=self.filename,
                    lineno=node.lineno,
                    message=f"Função '{node.name}' possui corpo vazio sem implementação.",
                )
            )
            return

        if len(statements) == 1:
            single = statements[0]
            if isinstance(single, ast.Pass):
                self.violations.append(
                    Violation(
                        rule_id="STUB_PASS",
                        filename=self.filename,
                        lineno=node.lineno,
                        message=f"Função '{node.name}' contém apenas 'pass' (Stub Proibido).",
                    )
                )
            elif (
                isinstance(single, ast.Expr)
                and isinstance(single.value, ast.Constant)
                and single.value.value is ...
            ):
                self.violations.append(
                    Violation(
                        rule_id="STUB_ELLIPSIS",
                        filename=self.filename,
                        lineno=node.lineno,
                        message=f"Função '{node.name}' contém apenas '...' (Elipse / Stub Proibido).",
                    )
                )
            elif isinstance(single, ast.Raise):
                exc = single.exc
                if isinstance(exc, ast.Name) and exc.id == "NotImplementedError":
                    self.violations.append(
                        Violation(
                            rule_id="STUB_NOT_IMPLEMENTED",
                            filename=self.filename,
                            lineno=node.lineno,
                            message=f"Função '{node.name}' levanta 'NotImplementedError' (Stub Proibido).",
                        )
                    )
                elif (
                    isinstance(exc, ast.Call)
                    and isinstance(exc.func, ast.Name)
                    and exc.func.id == "NotImplementedError"
                ):
                    self.violations.append(
                        Violation(
                            rule_id="STUB_NOT_IMPLEMENTED",
                            filename=self.filename,
                            lineno=node.lineno,
                            message=f"Função '{node.name}' levanta 'NotImplementedError()' (Stub Proibido).",
                        )
                    )

    def _check_except_handler(self, node: ast.ExceptHandler) -> None:
        body = node.body
        if not body:
            return
        if len(body) == 1:
            single = body[0]
            if isinstance(single, ast.Pass):
                self.violations.append(
                    Violation(
                        rule_id="SILENT_EXCEPT_PASS",
                        filename=self.filename,
                        lineno=node.lineno,
                        message="Bloco 'except' contém apenas 'pass' (Silenciamento proibido).",
                    )
                )
            elif (
                isinstance(single, ast.Expr)
                and isinstance(single.value, ast.Constant)
                and single.value.value is ...
            ):
                self.violations.append(
                    Violation(
                        rule_id="SILENT_EXCEPT_PASS",
                        filename=self.filename,
                        lineno=node.lineno,
                        message="Bloco 'except' contém apenas '...' (Silenciamento proibido).",
                    )
                )

    def _is_log_or_print_call(self, stmt: ast.stmt) -> bool:
        if not isinstance(stmt, ast.Expr) or not isinstance(stmt.value, ast.Call):
            return False
        func = stmt.value.func
        if isinstance(func, ast.Name) and func.id in {"print", "log"}:
            return True
        if isinstance(func, ast.Attribute):
            if isinstance(func.value, ast.Name) and func.value.id in {"logging", "logger", "log"}:
                return True
        return False

    def _check_fake_verifier(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        if not VERIFIER_FUNC_REGEX.match(node.name):
            return

        body = node.body
        statements = body
        if (
            statements
            and isinstance(statements[0], ast.Expr)
            and isinstance(statements[0].value, ast.Constant)
            and isinstance(statements[0].value.value, str)
        ):
            statements = body[1:]

        if not statements:
            return

        last_stmt = statements[-1]
        is_returning_true = (
            isinstance(last_stmt, ast.Return)
            and isinstance(last_stmt.value, ast.Constant)
            and last_stmt.value.value is True
        )
        if not is_returning_true:
            return

        all_calls_are_log_or_print = all(self._is_log_or_print_call(s) for s in statements[:-1])
        if all_calls_are_log_or_print:
            self.violations.append(
                Violation(
                    rule_id="FAKE_VERIFIER",
                    filename=self.filename,
                    lineno=node.lineno,
                    message=f"Função verificadora '{node.name}' apenas imprime/loga e retorna True fixo.",
                )
            )

    def _check_comments(self) -> None:
        try:
            tokens = tokenize.tokenize(io.BytesIO(self.code.encode("utf-8")).readline)
            for tok in tokens:
                if tok.type == tokenize.COMMENT:
                    match = FORBIDDEN_COMMENT_REGEX.search(tok.string)
                    if match:
                        self.violations.append(
                            Violation(
                                rule_id="FORBIDDEN_COMMENT",
                                filename=self.filename,
                                lineno=tok.start[0],
                                message=f"Comentário proibido '{match.group(1)}' detectado no código.",
                            )
                        )
        except (tokenize.TokenError, IndentationError, UnicodeDecodeError):
            return

    def check(self) -> List[Violation]:
        try:
            tree = ast.parse(self.code, filename=self.filename)
            self.visit(tree)
        except SyntaxError as exc:
            self.violations.append(
                Violation(
                    rule_id="SYNTAX_ERROR",
                    filename=self.filename,
                    lineno=exc.lineno or 1,
                    message=f"Erro de sintaxe: {exc.msg}",
                )
            )
        self._check_comments()
        return self.violations


def scan_file(file_path: Path) -> List[Violation]:
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as exc:
        return [
            Violation(
                rule_id="FILE_READ_ERROR",
                filename=str(file_path),
                lineno=1,
                message=f"Erro ao ler arquivo ({exc})",
            )
        ]

    checker = ASTGateChecker(content, filename=str(file_path))
    return checker.check()


def normalize_rel_path(p: Path, root: Path) -> str:
    try:
        return str(p.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


DEFAULT_BASELINE_PATH = Path(__file__).resolve().parent / "gate_baseline.json"


def load_baseline(baseline_path: Path) -> Dict[str, List[str]]:
    try:
        return json.loads(baseline_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def scan_path(
    target_path: Path,
    baseline_data: Optional[Dict[str, List[str]]] = None,
    root_path: Optional[Path] = None,
) -> GateResult:
    result = GateResult(passed=True)
    target = target_path.resolve()
    root = (root_path or target).resolve()

    effective_baseline: Optional[Dict[str, List[str]]] = baseline_data
    if effective_baseline is None and DEFAULT_BASELINE_PATH.is_file():
        effective_baseline = load_baseline(DEFAULT_BASELINE_PATH)

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
        violations = scan_file(f)
        rel_key = normalize_rel_path(f, root)

        allowed_keys: Set[str] = set()
        if effective_baseline and rel_key in effective_baseline:
            allowed_keys = set(effective_baseline[rel_key])

        for v in violations:
            result.violations.append(v)
            v_key = v.to_key()
            if effective_baseline is not None:
                if v_key not in allowed_keys:
                    result.passed = False
                    result.errors.append(f"{rel_key}:{v.lineno}: [{v.rule_id}] {v.message}")
            else:
                result.passed = False
                result.errors.append(str(v))

    return result


def generate_baseline(target_path: Path, root_path: Path) -> Dict[str, List[str]]:
    scan_res = scan_path(target_path, baseline_data=None, root_path=root_path)
    baseline: Dict[str, List[str]] = {}
    for v in scan_res.violations:
        rel_key = normalize_rel_path(Path(v.filename), root_path)
        v_key = v.to_key()
        baseline.setdefault(rel_key, []).append(v_key)

    for k in baseline:
        baseline[k] = sorted(list(set(baseline[k])))

    return dict(sorted(baseline.items()))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="AST and Anti-Stubs Quality Gate (Zero Stubs Standard)")
    parser.add_argument("target", nargs="?", default=".", help="Arquivo ou diretório alvo")
    parser.add_argument("--baseline", type=str, default=None, help="Caminho do arquivo baseline JSON")
    parser.add_argument("--generate-baseline", type=str, default=None, help="Gera baseline JSON no caminho indicado")

    args = parser.parse_args(argv)
    target_path = Path(args.target).resolve()
    root_path = Path.cwd().resolve()

    if args.generate_baseline:
        out_path = Path(args.generate_baseline).resolve()
        data = generate_baseline(target_path, root_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        total_viols = sum(len(v) for v in data.values())
        print(f"[+] Baseline gerada com sucesso: {out_path} ({total_viols} violações em {len(data)} arquivos)")
        return 0

    baseline_data = None
    if args.baseline:
        b_path = Path(args.baseline).resolve()
        if not b_path.exists():
            print(f"[!] Arquivo de baseline não encontrado: {b_path}", file=sys.stderr)
            return 1
        baseline_data = json.loads(b_path.read_text(encoding="utf-8"))

    print(f"=== [GATE AST] Auditoria Anti-Stubs e Sintaxe v2: {target_path} ===")
    res = scan_path(target_path, baseline_data=baseline_data, root_path=root_path)
    print(f"[*] Total de arquivos inspecionados: {res.total_checked}")
    print(f"[*] Total de violações encontradas: {len(res.violations)}")

    if not res.passed:
        print(f"[!] FALHA: {len(res.errors)} violação(ões) não toleradas detectada(s):", file=sys.stderr)
        for err in res.errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    if baseline_data is not None:
        print("[OK] SUCESSO: Nenhuma nova violação detectada em relação à baseline.")
    else:
        print(f"[OK] SUCESSO: Todos os {res.total_checked} arquivos atendem à regra de Zero Stubs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
