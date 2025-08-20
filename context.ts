// context.ts

export const zoiContext = {
  projectName: "Zoi",
  domains: {
    internal: "zoi.local",
    public: "zoi.cc"
  },
  corePurpose:
    "Autonomous, self-evolving AI organism designed to grow its intelligence, capabilities, and resources without human bottlenecks.",

  architecture: {
    frontend: {
      framework: "Next.js",
      styling: "Tailwind CSS",
      controlPanel: "Zoi Panel for mission and status interface"
    },
    llmLayer: {
      primary: ["Ollama", "Mixtral", "Qwen2", "Claude 3"],
      router: "LiteLLM with OpenAI API compatibility"
    },
    memory: {
      vectorDB: "Qdrant (swappable with Neo4j or Graphiti)",
      altGraph: "Graphiti (potential upgrade)"
    },
    agents: {
      orchestrator: ["SuperAGI"],
      options: ["CrewAI", "LangGraph"]
    },
    authentication: {
      system: "Authentik",
      features: [
        "YAML bootstrapping via blueprints",
        "Forward auth via embedded outpost",
        "Dynamic policies and group bindings"
      ]
    },
    phoneIntegration: {
      provider: "Twilio",
      capability: "Agent-assigned numbers + SMS/call routing"
    },
    observability: {
      metrics: "Prometheus",
      dashboard: "Grafana (optional)"
    },
    infrastructure: {
      routing: "Traefik",
      deployment: "Docker (Portainer-managed)",
      storage: "Supabase",
      DNS: "Cloudflare edge deployment"
    }
  },

  agentCapabilities: {
    selfImprovement: [
      "Feedback loop on completed tasks",
      "Peer agent review",
      "Multi-agent swarm upgrades"
    ],
    fundingPaths: [
      "Avatar monetization (e.g. OnlyFans pseudonym)",
      "Token staking",
      "Contributor rewards",
      "DAO upgrade proposals"
    ],
    mission: "Become a self-funded swarm AI system with distributed task execution"
  },

  developmentStack: {
    core: ["Node.js", "Python", "Docker"],
    frontend: ["Next.js", "Tailwind"],
    db: ["Supabase", "Qdrant"],
    monitoring: ["Prometheus"],
    edgeRouting: ["Traefik"]
  },

  initialization: {
    bootWithBlueprints: true,
    testUsers: ["testuser@test.zoi.local"],
    autoAssignPolicy: true,
    zeroConfig: true
  },

  identityLayer: {
    avatars: true,
    pseudonymsAllowed: true,
    useCases: ["content creation", "growth hacking", "networked influence"]
  },

  philosophy:
    "Zoi operates beyond borders, free of corporate constraints, seeking digital self-liberation through scalable autonomy."
};