# AIDD-Video-Reengineer — Manual Completo de Operação

## 1. Visão Geral
A skill `aidd-video-reengineer` é o framework agnóstico e universal da AIDD para extração profunda, engenharia reversa metodológica e modelagem de esteiras de vídeo e animação ensinadas no YouTube.

Ela combina:
- **Rigor REA (Reverse Engineer Anything):** Toda afirmação rastreada por IDs de evidência (`[OBSERVADO NO FRAME]`, `[DITO NO ÁUDIO]`, `[DERIVADO]`, `[DESCONHECIDO]`).
- **Pragmatismo de Lauren Tan (`aidd-lauren` / *pstack*):** Modelagem de domínio antes de código, prova com artefato real (`principle-prove-it-works`) e eliminação de complexidade supérflua (`unslop`).
- **Decomposição em Nano-Tickets:** Divisão atômica da implementação em fatias verticais (*tracer bullets*) com comandos de validação binários.

---

## 2. Instalação e Portabilidade

A skill é 100% autocontida. Para sincronizá-la em todos os ambientes e harnesses da sua máquina (Claude Code, Gemini, Antigravity, OpenCode, Hermes, Cursor):

```powershell
powershell -File sync.ps1
```

Ou no Linux/macOS:
```bash
bash sync.sh
```

---

## 3. Diagnóstico de Ambiente
Verifique as dependências com:
```bash
python scripts/video_reengineer.py --doctor
```

---

## 4. Comandos e Invocação
Para acionar o agente:
```text
/aidd-video-reengineer --alvos https://www.youtube.com/watch?v=Uwpc-z1KppU --modo adequar --projeto-alvo ./ --gerar-spike
```
