# Rule: Senior Software Engineer Standards

## 1. Architectural & Engineering Philosophy
- **Scalability & Clean Design:** Design modular, extensible software components with clear separation of concerns (SOC) and SOLID principles.
- **Defensive Engineering:** Anticipate failure modes, handle edge cases gracefully, use strict validation (Pydantic v2, TypeScript/PropTypes), and log errors with detailed contextual diagnostics.
- **Performance & Efficiency:** Optimize database queries (indexing, N+1 query avoidance), vector embeddings, memory usage, and UI rendering performance.

## 2. Code Quality & Standards
- **Production Readiness:** No magic numbers, no dead code, no untyped fallbacks, and zero hardcoded secrets or environment assumptions.
- **Security First:** Enforce zero-trust input validation, prevent OWASP Top 10 vulnerabilities (SQLi, XSS, SSRF, Prompt Injection), and sanitize all external data inputs.
- **Clear Technical Rationale:** Document key architectural decisions, complex logic, and API contracts concisely without unnecessary conversational bloat.
