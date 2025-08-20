# 🌀 Zoi LLM Stack (Windows / Dual GPU)

This stack is tuned for:
- RTX 5070 Ti → helper tasks (Ollama)
- RTX 3090 → planner tasks (vLLM)

## Ports
- LiteLLM → http://localhost:7010/v1
- AutoRouter → http://localhost:7020/v1 (use model: "zoi:auto")
- vLLM (Planner) → http://localhost:7030/v1
- Ollama (Helper) → http://localhost:7040
- Qdrant → http://localhost:7050

## Usage
```powershell
docker compose up -d
docker exec -it ollama bash -lc "ollama pull qwen2.5-coder:7b-instruct"
```

Then call AutoRouter with:
```json
{ "model": "zoi:auto", "messages": [{"role": "user", "content": "Write a Next.js page"}] }
```
