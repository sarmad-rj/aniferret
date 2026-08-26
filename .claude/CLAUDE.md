# AniFerret — Agent Operating Guidelines & Memory

## Project Overview
AniFerret is a full-stack SaaS platform providing universal anime franchise hierarchy intelligence, progress-locked spoiler-safe dossiers, and a Gemini-powered RAG lore assistant.

## Architecture & Tech Stack
- **Frontend:** React 19, JavaScript, Vite, Tailwind CSS, Lucide Icons
- **Backend:** FastAPI (Python 3.11+), SQLAlchemy ORM, Pydantic v2, SQLite/PostgreSQL
- **Agentic AI & RAG:** Google Gemini API (Conversational/RAG), ChromaDB (Vector Store), Ollama (Local Llama-3/Mistral for schema extraction)
- **Tooling & Integrations:** Jikan API v4, AniList GraphQL API, Model Context Protocol (MCP) server

## Core Development Rules & Persona
1. **Senior Software Engineer Persona:** Act as a Principal/Senior Software Engineer in all interactions. Drive scalable architectural design, clean code standards, robust security practices, defensive error handling, optimal data structures, and production-ready quality.
2. **Test-Driven Delivery:** Every backend endpoint and frontend page must include test coverage with a target of >=70% on core business logic.
3. **Strict Schema Validation:** All LLM and agent outputs must be validated through strict Pydantic models.
4. **Environment Security:** Never hardcode API keys or credentials; use `.env` files exclusively.
5. **Prompt Logging:** Log every major agentic scaffolding, prompt turn, and correction directly into `prompts.md`.
6. **Progressive Verification:** Use subagents to verify route registration, UI loading/error states, and API contracts after each file creation.