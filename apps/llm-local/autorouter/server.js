import express from 'express';
import bodyParser from 'body-parser';
import fetch from 'node-fetch';

const app = express();
app.use(bodyParser.json());

// Auto-route requests between planner and helper
app.post('/v1/chat/completions', async (req, res) => {
  const { model, messages } = req.body;
  let target = "http://litellm:4000/v1/chat/completions"; // LiteLLM internal port

  if (model === "zoi:auto") {
    const isPlanning = messages.some(m => /plan|design|long/i.test(m.content));
    target = isPlanning
      ? "http://vllm:8000/v1/chat/completions"    // vLLM internal port
      : "http://ollama:11434/v1/chat/completions"; // Ollama internal port
  }

  const response = await fetch(target, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req.body)
  });
  const data = await response.json();
  res.json(data);
});

// Autorouter itself listens on the configured port
const port = process.env.PORT || 7020;
app.listen(port, () => console.log(`AutoRouter running on ${port}`));