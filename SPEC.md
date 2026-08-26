# SPEC.md — AniFerret Product & Feature Specification

## 1. Vision & Architectural Position
**AniFerret** is not merely another anime catalog—it is a **Temporal Knowledge Platform** that adds a 4th dimension (Time / Episode Progress) to traditional anime databases.

While existing platforms store static facts about anime, AniFerret models **when each fact becomes true in canon**, enforcing structural spoiler protection before data reaches the user or LLM context window.

```text
 ┌────────────────────────────────────────────────────────────────────────┐
 │ Existing Databases  │ Store static facts: Anime, Characters, Episodes  │
 │ AniFerret Innovation│ Stores Temporal Facts: (Fact + first_revealed_at)│
 └────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Competitive Matrix & Platform Specialization Analysis

AniFerret synthesizes the strongest data model elements of the 9 legendary anime platforms while introducing the missing temporal layer:

| Platform | Specialization & Model Strengths | Primary Limitation | How AniFerret Integrates & Wins |
|---|---|---|---|
| **AniList** | Modern GraphQL API, rich `Connection` edges (`Anime → Character → VoiceActor`) | Zero per-episode reveal tracking or progress-gated filters | Uses AniList GraphQL for base entity connections + adds temporal fact gating |
| **MyAnimeList (MAL) / Jikan** | Massive character/synopsis database & JSON scraper API | Flat text synopses with indiscriminate spoilers | Fetches base metadata via Jikan REST API v4 + parses atomic facts into Reveal Ledger |
| **AniDB** | Deep character relations & episode range associations (`appeared_in_episodes`) | Dated UI and zero automated spoiler gating | Adopts AniDB's episode-range mapping + gates reveals via vector metadata |
| **Kitsu** | JSON:API resource relationships (`anime/1/episodes`) | Simple watch lists, no LLM lore assistant | Uses structured JSON schemas for ReAct agent extraction |
| **Anime-Planet** | Rich character lists & user recommendations | Static bios reveal character deaths and plot twists | Filters character traits dynamically against user episode slider |
| **LiveChart.me** | Seasonal airing schedules & countdowns | Limited to current season discovery | Provides watch order generator (Release vs Chronological) |
| **AniChart** | Visual grid seasonal discovery | No deep lore, faction hierarchies, or Q&A | Combines visual seasonal grids with deep faction hierarchy trees |
| **Anime News Network (ANN)** | Encyclopedic staff/cast listings & prose | Unqueryable prose paragraphs | Extracts prose into schema-validated JSON exposed over MCP |
| **SIMKL** | User watch tracking & progress histories | Standard tracking without spoiler protection | Integrates progress-locked retrieval & lowest-common-checkpoint group mode |

---

## 3. The 3-Layer System Architecture

AniFerret operates across three distinct system layers:

```text
 ┌─────────────────────────────────────────────────────────────────────────┐
 │ Layer 1: Data Sources  │ Jikan REST v4, AniList GraphQL, Wiki Extracts  │
 ├─────────────────────────────────────────────────────────────────────────┤
 │ Layer 2: AniFerret     │ PostgreSQL (Temporal Fact Graph)               │
 │          Core Engine   │ + ChromaDB (Vector Index with metadata)          │
 │                        │ + ReAct Hierarchy Agent & Gemini RAG           │
 ├─────────────────────────────────────────────────────────────────────────┤
 │ Layer 3: User Interface│ React 19 Light-Mode UI (Mist Blue / Navy / Pink)│
 └─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. The Core Moat: Temporal Fact Schema & Reveal Engine

Traditional databases store character data as monolithic paragraphs (`character.description`). AniFerret decomposes data into atomic, checkpoint-labeled **Fact Objects**:

### 4.1 Temporal Fact Object Schema
```json
{
  "fact_id": 1827,
  "anime_id": "code-geass",
  "subject": "Lelouch vi Britannia",
  "predicate": "true_identity",
  "object": "Zero (Leader of the Black Knights)",
  "source_citation": "Season 1, Episode 12",
  "first_revealed_at": "S1E12",
  "first_hinted_at": "S1E3",
  "confidence": 0.96
}
```

### 4.2 Gated Retrieval Evaluation Logic

When a user executes a query at a given episode checkpoint (e.g. `User Checkpoint = S1E10`):

```text
Step 1: User Query → "Who is Zero?" (Checkpoint: S1E10)
Step 2: Vector Pre-Filter Check → first_revealed_at <= S1E10
        • Fact #1827 ("Lelouch is Zero", Revealed at S1E12) → Evaluates FALSE ❌
        • Fact #1827 is BLOCKED before reaching LLM context window.
Step 3: Output → Emits Uniform Refusal / Safe Baseline context only.

Step 4: User Progress Advances to S1E12 (Checkpoint: S1E12)
Step 5: Vector Pre-Filter Check → first_revealed_at <= S1E12
        • Fact #1827 → Evaluates TRUE ✅
        • Fact #1827 RETRIEVED & Synthesized by Gemini with exact S1E12 citation.
```

---

## 5. Core Feature Differentiators (Tier 1 Launch)

### D1. Progress-Gated Retrieval Engine
User sets progress slider ($S1E12$). All dossiers, answers, and rosters filter facts through `first_revealed_at <= user_checkpoint`. Zero prompt-level spoiler leakage.

### D2. Meta-Spoiler-Safe Uniform Refusal Engine
Prevents meta-spoilers (confirming a plot twist exists). Returns a byte-identical, uniform refusal for reveal-bearing and control questions.

### D3. Group Mode (Lowest-Common-Checkpoint Session)
Calculates $\text{effective\_checkpoint} = \min(\{C_1, C_2, \dots, C_n\})$ for co-watchers, keeping co-watching Q&A safe for everyone.

### D4. Rewatch Mode (The Foreshadowing Index)
Inverts the ledger for completed viewers. Displays setup (`first_hinted_at`) vs payoff (`first_revealed_at`) pairs with episode citations.

### D5. Machine-Queryable Hierarchy Dossiers over MCP
Parses faction command tiers, squad rosters, and class rankings into schema-validated JSON, exposed via a standalone Model Context Protocol (MCP) server.

### D6. Source-Conflict Surfacing
Transparently displays discrepancies across Jikan, AniList, and wiki sources with explicit provider tags.

---

## 6. Launch Scope & Boundaries
To ensure 100% precision and zero-leakage guarantees, the launch corpus focuses on three structurally rich series:

| Series Title | Total Episodes | Target Organizational Hierarchy |
|---|---|---|
| **Classroom of the Elite** | 37 Episodes | Class tiers, point allocation mechanics, student rankings |
| **Code Geass** | 50 Episodes | Britannian nobility, Black Knights command chain |
| **Attack on Titan (S1)** *(Stretch)* | 25 Episodes | Military branches, squad composition, survey corps ranks |
