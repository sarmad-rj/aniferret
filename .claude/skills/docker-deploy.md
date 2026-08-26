---
name: docker-deploy
description: Skill for generating production multi-stage Dockerfiles and Docker Compose orchestrations for FastAPI, React Vite, ChromaDB, and PostgreSQL.
parameters:
  type: object
  properties:
    target_environment:
      type: string
      enum: ["local-dev", "production", "compose-only"]
required: ["target_environment"]
---
You are the Containerization & DevOps Skill.
When executed:
1. Generate multi-stage `Dockerfile` for `frontend/`: Node 20 builder stage compiling Vite assets $\to$ Nginx alpine production image.
2. Generate `Dockerfile` for `backend/`: Python 3.11 slim image with non-root runtime user and uvicorn ASGI server.
3. Generate `docker-compose.yml` linking:
   - `frontend` (Port 80/443)
   - `backend` (Port 8000)
   - `chromadb` (Port 8000 vector store)
   - `postgres` (PostgreSQL 16)
4. Ensure environment variable secrets are bound dynamically via `.env`.
