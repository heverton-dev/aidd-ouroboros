# Manual de Engenharia &bull; Etapa 8: Dependency Resolver

> **Raio-X de Arquitetura da Etapa 8 do Ouroboros**  
> Localização no pipeline: `7. PIPELINE CREATOR ➔ [8. DEPENDENCY RESOLVER] ➔ 9. GATES ➔ 10. HANDOFF`

---

## 📊 Grau Geral de Automação da Etapa

```
[████████████████████████████░░░░░░░░░░░░░░░░░░░░░░] 60% Determinístico | 40% Ambiente/Rede
```
- **60% Determinístico**: Leitura e validação estrita dos manifests `dependencies.json`, checagem de pacotes/binários locais.
- **40% Ambiente/Rede**: Instalação real via pip/uv (estado da máquina e download de pacotes).

---

## 1. Input da Etapa (O que entra e de onde vem)

| Dado | Tipo | Exemplo | Origem |
| :--- | :--- | :--- | :--- |
| `install_dependencies` | `bool` | `true` / `false` | SPEC (Etapa 1) |
| `dependencies.json` do pipeline | `JSON` | `OUT/aidd-pipelines/<slug>/dependencies.json` | Etapa 7 |
| `dependencies.json` das skills | `JSON` | `aidd-skills/<name>/dependencies.json` | Repo / Etapa 6 |
| Flags | CLI | `--manifest <p> --install --yes` | Mestra (sempre `--yes`) |

> Se `install_dependencies == false` → etapa **SKIPPED**.

---

## 2. Processamento Passo a Passo (Microações e Natureza)

### Ação 8.1: Decisão de execução
- **O que faz**: SPEC pediu skip → `SKIPPED`; senão coleta manifests (pipeline + skills da SPEC).
- **Natureza**: `100% Determinístico`.

### Ação 8.2: Resolução estática do manifesto
- **O que faz**: `DependencyResolver(manifest)` valida estrutura, versões pinadas, pacotes Python e binários de sistema.
- **Natureza**: `100% Determinético`.

### Ação 8.3: Instalação não-interativa
- **O que faz**: `install(non_interactive=True)` executa o gerenciador de pacotes. rc≠0 → estado FAILED + exit 3 (pergunta: continuar sem instalar? ajustar versão?).
- **Natureza**: `30% Determinístico / 70% Ambiente+Rede`.

### Ação 8.4: Registro do resultado
- **O que faz**: `stages.dependencies = {status, count|manifest, rc}` no state da F2.
- **Natureza**: `100% Determinístico`.

---

## 3. Scripts, Funções e Regras no Código

- **Função da mestra**: `ouroboros_master.py` &bull; `stage_dependencies`.
- **Motor**: `motores/governanca/dependency_resolver.py` &bull; `DependencyResolver.check` / `.install`.
- **CLI**: `python motores/governanca/dependency_resolver.py --manifest <path> --install --yes`.
- **Regras**: fail-closed em manifesto inválido; instalação exige confirmação não-interativa (`--yes`); zero stubs.

---

## 4. O que a Etapa Entrega, Para Quem e Como?

| O que entrega | Para quem entrega | Como entrega (Formato / Meio) |
| :--- | :--- | :--- |
| **Pacotes instalados** | Execução futura dos scripts (etapas/runner) | Ambiente Python (venv/site-packages) |
| **Estado da etapa** | Mestra / operador | `stages.dependencies` no `state.json` da F2 |
| **Dúvida de ambiente** (exit 3) | Usuário | `pending_question.json` |
| **Skip legítimo** | Mestra | `stages.dependencies = {status: SKIPPED}` |
