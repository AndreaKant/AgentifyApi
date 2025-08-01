# AI Agent POC - Un Agente AI Ibrido e Autonomo

Un agente AI ibrido e autonomo basato su un'architettura a microservizi, capace di pianificare, eseguire e recuperare da errori dinamicamente, utilizzando LLM e ricerca vettoriale per interagire con diverse API (REST, gRPC, GraphQL).

---

## 🏛️ Architettura

Il sistema è composto da diversi microservizi Docker che collaborano per fornire un'intelligenza centralizzata.

```mermaid
graph TD
    subgraph "Utente"
        A[User Query]
    end

    subgraph "AI Agent (Container)"
        B[Planner] --> C{Piano Strategico};
        C --> D[Esecutore];
        D -- Cerca Strumento --> E((pgvector DB));
        D -- Chiama Tool --> F{Tool Executor};
        F -- Errore --> G[Recovery Agent];
        G -- Analizza Errore --> H[LLM Gateway];
        F -- Successo --> I[Field Extractor];
        I -- Risultato Parziale --> C;
        C -- Piano Completato --> J[Sintetizzatore];
        J -- Chiama LLM --> H;
        H -- Risposta Finale --> K[Risposta per Utente];
    end

    subgraph "Microservizi di Supporto"
        L[Indexer] -- Scrive --> E;
        M[API Servers] --> L;
        N[gRPC Parser] --> L;
        H -- Chiama --> O[API Gemini/OpenAI];
    end

    A --> B;
end
```

## ✨ Caratteristiche Principali

- **Architettura a Microservizi**: Ogni componente è isolato in un container Docker per massima scalabilità e manutenibilità.
- **Agente Ibrido**: Combina un **Planner Strategico** per la visione d'insieme e un **Operatore Esecutivo** per i singoli task.
- **Indicizzazione Semantica**: Un servizio `Indexer` analizza automaticamente i contratti delle API (OpenAPI, .proto, GraphQL) e li indicizza in un database vettoriale (`pgvector`).
- **Gestione Errori Avanzata**: Un `Recovery Agent` dedicato implementa un ciclo ReAct per analizzare e tentare di risolvere gli errori delle API in tempo reale.
- **LLM Gateway Centralizzato**: Un microservizio che gestisce tutte le chiamate ai modelli LLM, con logica di retry, fallback e logging.
- **Routing Intelligente**: Seleziona dinamicamente il modello LLM più adatto (e più economico) in base alla complessità del task.

## 🚀 Come Iniziare

### Prerequisiti
- Docker e Docker Compose
- Git
- Una API key di OpenAI e una di Google AI Studio (Gemini)

### Installazione
1. Clona il repository:
   ```bash
   git clone // TODO: URL
   cd ai-agent-poc
   ```
2. Crea il tuo file di ambiente partendo dall'esempio:
   ```bash
   cp .env.example .env
   ```
3. Apri il file `.env` e inserisci le tue chiavi API.
4. Avvia tutti i servizi con Docker Compose:
   ```bash
   docker-compose up --build -d
   ```
5. Esegui l'indicizzatore per popolare il database con gli strumenti disponibili:
   ```bash
   docker-compose exec indexer python -m indexer.main
   ```

## 🎮 Come Usarlo

Per avviare una conversazione con l'agente:
```bash
docker-compose exec agent python -m agent.main
```

A questo punto, l'agente ti saluterà e potrai iniziare a fare domande.