# Fundamentos de Engenharia Reversa de Apps (REA App Protocol)

Metodologia canônica para dissecação estática de executáveis e pacotes mobile.

## 1. Princípios de Desempacotamento
1. **Estrutura Zip de APKs:** Um arquivo APK é essencialmente um container ZIP contendo `classes.dex`, `resources.arsc`, `res/`, `AndroidManifest.xml` e `assets/`.
2. **Inspeção de Permissões:** O vetor de funcionalidades de um app é imediatamente revelado pelas permissões declaradas no manifesto.
3. **Mapeamento de Rotas Nativas:** Activities e Fragments representam os estados de tela equivalentes às rotas web.
