# AgentifyApi: A Hybrid and Agnostic AI Agent

A state-of-the-art hybrid AI agent built on a decoupled microservices architecture. It leverages a two-tier thinking process: a **Strategic Planner** for high-level goal setting and a **Task Operator** for execution. The agent dynamically discovers and interacts with tools (REST, gRPC, GraphQL) through semantic search on a vector database, and features a **Recovery Agent** to autonomously handle and learn from API errors. The entire system is orchestrated via Docker Compose, creating a scalable and resilient framework for building autonomous solutions.

---

## 🏛️ Architecture

The system is composed of several Docker microservices that work in concert to provide a centralized intelligence. The flow is designed for resilience, adaptability, and observability.

```mermaid
graph TD
    subgraph "User"
        A[User Query]
    end

    subgraph "AI Agent (Container)"
        B[Planner] --> C{Strategic Plan};
        C --> D[Executor];
        D -- Find Tool --> E((pgvector DB));
        D -- Call Tool --> F{Tool Executor};
        F -- on Error --> G[Recovery Agent];
        G -- Analyze Error --> H[LLM Gateway];
        F -- on Success --> I[Field Extractor];
        I -- Partial Result --> C;
        C -- Plan Completed --> J[Synthesizer];
        J -- Call LLM --> H;
        H -- Final Response --> K[User Response];
    end

    subgraph "Support Microservices"
        L[Indexer] -- Writes To --> E;
        M[API Servers] -- Scanned by --> L;
        N[gRPC Parser] -- Scanned by --> L;
        H -- Calls --> O[External Gemini/OpenAI API];
    end

    A --> B;
end
```
## ✨ Key Features

-   **🧠 Hybrid Agent Architecture:** Utilizes a high-level **Planner** (using powerful models like Gemini Pro) to create strategic plans, and a low-level **Operator** (using faster, cheaper models like Gemini Flash) to execute each step, optimizing for both cost and performance.
-   **🔌 Agnostic Tool Integration:** The agent is not hardcoded to specific tools. An `Indexer` service automatically parses API contracts (OpenAPI for REST, `.proto` for gRPC, and GraphQL schemas) and indexes them in a `pgvector` database, allowing for dynamic, semantic discovery of the best tool for any given task.
-   **❤️‍🩹 Self-Healing & Resilience:** A dedicated `Recovery Agent` intercepts failed API calls. It uses an LLM to analyze the error, reason about the cause (e.g., invalid payload, temporary server issue), and autonomously decide on a recovery strategy, such as retrying with a corrected payload or waiting.
-   **🏛️ Decoupled Microservices:** Built with Docker Compose, the system isolates every component—from the agent's core logic to the LLM gateway and API parsers—into its own container. This ensures scalability, maintainability, and easy development.
-   ** GATEWAY Centralized LLM Gateway:** A dedicated Node.js microservice proxies all calls to external LLMs. This central point manages API keys, implements robust retry/fallback logic, and provides centralized logging, abstracting away complexity from the main agent.

## 🚀 Getting Started

### Prerequisites
- Docker and Docker Compose
- Git
- An OpenAI API key and a Google AI Studio (Gemini) API key.

### Installation
1.  Clone the repository:
    ```bash
    git clone https://github.com/AndreaKant/AgentifyApi
    ```
2.  Navigate into the project directory:
    ```bash
    cd AgentifyApi
    ```
3.  Create your environment file from the example:
    ```bash
    cp .env.example .env
    ```
4.  Open the `.env` file and insert your API keys.

5.  Build and run all services in the background:
    ```bash
    docker-compose up --build -d
    ```
6.  Run the indexer to populate the database with the available tools:
    ```bash
    docker-compose exec indexer python -m indexer.main
    ```

## 🎮 How to Use

To start a conversation with the agent, run the following command:
```bash
docker-compose exec agent python -m agent.main
```

At this point, the agent will greet you, and you can start asking questions. For example: 
```What is the heaviest Pokémon between Pikachu, Charizard, and Snorlax?```