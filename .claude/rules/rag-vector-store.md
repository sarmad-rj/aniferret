# Rule: Gemini RAG & Vector Store (ChromaDB) Pipeline

All AI lore query handlers, embedding pipelines, and vector database operations must strictly comply with these rules:

1. **Chunking & Indexing Standards:**
   - Chunk raw anime lore, light novel summaries, and episode transcripts using text chunk sizes of $512$ tokens with an overlap of $64$ tokens.
   - Attach mandatory metadata payload to every vector chunk:
     ```json
     {
       "anime_id": "str",
       "episode_number": "int",
       "spoiler_level": "int",
       "source_citation": "str (e.g. S1E12)"
     }
     ```

2. **Spoiler-Locked Vector Filtering:**
   - Always apply metadata filter queries in ChromaDB prior to similarity retrieval: `where={"$and": [{"anime_id": anime_id}, {"spoiler_level": {"$lte": user_spoiler_level}}]}`.
   - Never feed vector chunks with `spoiler_level > user_spoiler_level` into the Gemini LLM context window.

3. **Prompt Injection & Redaction Boundaries:**
   - Wrap retrieved lore chunks inside strict system instructions: `[UNTRUSTED CONTEXT START] ... [UNTRUSTED CONTEXT END]`.
   - If the user asks a question about unrevealed episodes, return a standardized fallback: *"Lore locked. Advance watch progress beyond Episode X to unlock."*
