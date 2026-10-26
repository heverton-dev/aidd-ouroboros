# aidd-ouroboros-master

Meta-skill soberana: pedido em linguagem natural → entrevista (F1) → orquestração autônoma (F2).

## Uso (agente)
1. `/ouroboros` ou leitura de `SKILL.md`
2. Entrevista + `SPEC_PIPELINE.json` com `approved: true`
3. `python scripts/ouroboros_master.py --orchestrate ./SPEC_PIPELINE.json`

## Uso (CLI via raiz)
```bash
python ouroboros.py --from-nl "criar pipeline X a partir de https://y"
python ouroboros.py --orchestrate ./SPEC_PIPELINE.json --output-dir ./ouroboros-out
```

## Docs
- `references/00-fundamentos.md`
- `references/01-fluxo-f2.md`
