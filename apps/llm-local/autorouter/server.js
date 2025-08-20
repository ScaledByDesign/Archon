import express from 'express';
import bodyParser from 'body-parser';
import fetch from 'node-fetch';

const app = express();
app.use(bodyParser.json());

// Auto-route requests between planner and helper
app.post('/v1/chat/completions', async (req, res) => {
  const { model, messages } = req.body;
  let target = "http://litellm:7010/v1/chat/completions"; // updated port

  if (model === "zoi:auto") {
    const isPlanning = messages.some(m => /plan|design|long/i.test(m.content));
    target = isPlanning
      ? "http://vllm:7030/v1/chat/completions"    // planner on 7030
      : "http://ollama:7040/v1/chat/completions"; // helper on 7040
  }

  const response = await fetch(target, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req.body)
  });
  const data = await response.json();
  res.json(data);
});

// Autorouter itself listens on 7020
app.listen(7020, () => console.log("AutoRouter running on 7020"));