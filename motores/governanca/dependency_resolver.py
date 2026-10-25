"""
Resolvedor estático e instalador determinístico de dependências do ecossistema AIDD Ouroboros.
Governança: Zero Stubs, Validação Estrita de Versões Pinadas, Proteção Absoluta contra Vazamento de Secrets.
"""

import argparse
import importlib.metadata
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


class DependencyResolver:
    """
    Resolvedor de matriz estática de dependências baseada em manifesto dependencies.json.
    """

    def __init__(self, manifest_target: Union[str, Path]) -> None:
        self.manifest_path = self._resolve_manifest_path(Path(manifest_target))
        self.data = self._load_manifest(self.manifest_path)

    @staticmethod
    def _resolve_manifest_path(target: Path) -> Path:
        if target.is_dir():
            candidate = target / "dependencies.json"
            if candidate.is_file():
                return candidate
            raise FileNotFoundError(f"Manifesto dependencies.json não encontrado no diretório: {target}")
        if target.is_file():
            return target
        raise FileNotFoundError(f"Arquivo de manifesto não encontrado: {target}")

    @staticmethod
    def _load_manifest(path: Path) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            content = json.load(f)
            if not isinstance(content, dict):
                raise ValueError("O manifesto dependencies.json deve conter um objeto JSON na raiz.")
            return content

    def check_system_binary(self, binary_info: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        if isinstance(binary_info, dict):
            name = binary_info.get("name", "")
            required = bool(binary_info.get("required", True))
        else:
            name = str(binary_info)
            required = True

        found_path = shutil.which(name)
        status = "READY" if found_path is not None else "MISSING"
        return {
            "name": name,
            "required": required,
            "status": status,
            "resolved_path": found_path if found_path else None,
        }

    def check_python_package(self, package_spec: str) -> Dict[str, Any]:
        pkg_name = re.split(r"[><=~!]", package_spec)[0].strip()
        canonical_name = pkg_name.replace("-", "_").lower()
        
        is_installed = False
        installed_version = None

        try:
            installed_version = importlib.metadata.version(pkg_name)
            is_installed = True
        except (importlib.metadata.PackageNotFoundError, Exception):
            spec = importlib.util.find_spec(canonical_name)
            if spec is not None:
                is_installed = True

        status = "READY" if is_installed else "MISSING"
        return {
            "spec": package_spec,
            "name": pkg_name,
            "status": status,
            "installed_version": installed_version,
            "required": True,
        }

    def check_env_var(self, env_var: str) -> Dict[str, Any]:
        # Proteção estrita: NUNCA capturar ou expor o valor da variável de ambiente
        var_name = env_var.strip()
        is_present = var_name in os.environ and len(os.environ[var_name]) > 0
        return {
            "name": var_name,
            "status": "READY" if is_present else "MISSING",
            "required": True,
        }

    def check_core_skill(self, skill_name: str) -> Dict[str, Any]:
        clean_name = skill_name.strip()
        root_dir = Path.cwd()
        possible_paths = [
            root_dir / "aidd-skills" / clean_name,
            root_dir / ".agents" / "skills" / clean_name,
            root_dir.parent / "aidd-skills" / clean_name,
        ]
        exists = any(p.is_dir() for p in possible_paths)
        return {
            "name": clean_name,
            "status": "READY" if exists else "MISSING",
            "required": True,
        }

    def check(self) -> Dict[str, Any]:
        results: Dict[str, List[Dict[str, Any]]] = {
            "system_binaries": [],
            "python_packages": [],
            "env_vars": [],
            "core_skills": [],
        }

        # 1. Binários do sistema
        for b in self.data.get("system_binaries", []):
            results["system_binaries"].append(self.check_system_binary(b))

        # 2. Pacotes Python
        for p in self.data.get("python_packages", []):
            results["python_packages"].append(self.check_python_package(p))

        # 3. Variáveis de ambiente (suporte a chaves 'env_vars' ou 'environment_variables')
        env_list = self.data.get("env_vars", []) or self.data.get("environment_variables", [])
        for e in env_list:
            results["env_vars"].append(self.check_env_var(e))

        # 4. Skills dependentes (suporte a 'core_skills' ou 'skills_required')
        skills_list = self.data.get("core_skills", []) or self.data.get("skills_required", [])
        for s in skills_list:
            results["core_skills"].append(self.check_core_skill(s))

        has_missing_required = False
        for category, items in results.items():
            for item in items:
                if item.get("required", True) and item.get("status") == "MISSING":
                    has_missing_required = True

        return {
            "manifest": str(self.manifest_path),
            "ok": not has_missing_required,
            "results": results,
        }

    def validate_pinned_python_packages(self) -> Tuple[bool, List[str]]:
        packages = self.data.get("python_packages", [])
        unpinned = []
        for pkg in packages:
            if "==" not in pkg:
                unpinned.append(pkg)
        return (len(unpinned) == 0, unpinned)

    def install(self, non_interactive: bool = False) -> Tuple[bool, str]:
        if not non_interactive:
            return False, "Instalação bloqueada: a flag --yes é obrigatória para execução não-interativa."

        is_pinned, unpinned = self.validate_pinned_python_packages()
        if not is_pinned:
            return False, f"Violação de política determinística: pacotes despinados/unpinned detectados: {unpinned}. Apenas versões pinadas ('==') são permitidas."

        packages = self.data.get("python_packages", [])
        if not packages:
            return True, "Nenhum pacote Python listado para instalação."

        for pkg in packages:
            cmd = [sys.executable, "-m", "pip", "install", pkg]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                return False, f"Falha na instalação do pacote {pkg}: {res.stderr.strip()}"

        return True, "Todas as dependências pinadas foram instaladas com sucesso."


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Resolvedor e instalador determinístico de dependências do ecossistema AIDD Ouroboros."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=None,
        help="Caminho do arquivo dependencies.json ou pasta contendo o manifesto.",
    )
    parser.add_argument(
        "--manifest",
        "-m",
        dest="manifest_opt",
        default=None,
        help="Caminho explícito para dependencies.json.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Audita o status de prontidão das dependências e emite relatório JSON.",
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="Executa a instalação estrita de pacotes pinados.",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Confirmação de execução não-interativa obrigatória para instalações.",
    )

    args = parser.parse_args(argv)

    raw_path = args.manifest_opt or args.target or "dependencies.json"
    target_path = Path(raw_path)

    try:
        resolver = DependencyResolver(target_path)
    except Exception as exc:
        sys.stderr.write(f"Erro ao inicializar resolvedor: {exc}\n")
        return 1

    if args.install:
        success, message = resolver.install(non_interactive=args.yes)
        if success:
            sys.stdout.write(f"{message}\n")
            return 0
        sys.stderr.write(f"Erro: {message}\n")
        return 1

    # Por padrão ou com flag --check: executa a auditoria
    report = resolver.check()
    sys.stdout.write(json.dumps(report, indent=2) + "\n")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
