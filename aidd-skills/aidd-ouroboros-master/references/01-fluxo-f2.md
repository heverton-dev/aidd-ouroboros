# 01 — Fluxo F2 (autônomo) passo a passo

Ordem imutável dentro de `--orchestrate`:

1. **Schema** — `jsonschema` contra `SPEC_PIPELINE.schema.json`
2. **REA** — se `target.kind != none`: `rea_router.py --target <uri> --output-handoff ...`
3. **Skills** — para cada `skills_required`:
   - se existe em `aidd-skills/` → reuse
   - senão `mode=github-scout` → `skill_creator.py --github-scout`
   - senão → `skill_creator.py --nome`
4. **Pipeline** — `pipeline_creator.py --scaffold-pipeline <nome> --steps <json>`
5. **Deps** — `dependency_resolver.py --manifest ... --install --yes`
6. **Audit** — `audit_runner.py --skip-pytest`

## Handoff final
`ouroboros-out/handoffs/master_final_handoff.json` assinado via `handoff_crypto.criar_envelope_handoff`.

## Retomada
Após exit 3, corrija só o campo apontado em `pending_question.json`, rode de novo com `--resume`.
