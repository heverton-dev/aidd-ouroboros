# Pipeline E2E Smoke Directives

> Pipeline de teste E2E determinístico conectando aidd-rea-router a aidd-rea-app-android sobre APK fixture.

## Regras Operacionais

1. **Determinismo:** O pipeline consome exclusivamente fixtures controlados (`tests/fixtures/sample_app.apk`).
2. **Handoffs Criptográficos:** Cada transição de nó deve selar payload assinado via HMAC-SHA256 e salvar em `handoffs/`.
3. **Zero Stubs:** As permissões e metadados devem ser extraídos do manifesto do APK sem emulação de valores fictícios.
4. **Isolamento de Execução:** Toda execução deve gerar artefatos em subdiretórios de workspace descartáveis.
