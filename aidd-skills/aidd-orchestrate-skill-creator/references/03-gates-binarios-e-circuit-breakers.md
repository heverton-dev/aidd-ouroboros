# 03 — Gates Binários e Circuit Breakers

## A Filosofia de Governança
Nenhuma regra de engenharia sobrevive se depender da "boa vontade" do agente. Ela precisa ser checada por um script estático que retorna código de saída `0` (sucesso) ou `1` (falha).

## Os 4 Gates Automatizados da Skill Gerada
1. `G-MICRO-FRONTMATTER`: Garante que a descrição tenha $\le 25$ palavras.
2. `G-DUAL-SPEC`: Garante que `SKILL.md` e `AGENTS.md` existam e estejam em sincronia.
3. `G-GOVERNANCA`: Garante que `RULES.md`, `LICENSE`, `pyproject.toml` e `requirements.txt` existam.
4. `G-CIRCUIT-BREAKER`: Garante que a ferramenta CLI implemente `--doctor` e `--audit`.
