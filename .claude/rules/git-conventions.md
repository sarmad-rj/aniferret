# Rule: Conventional Commits & Git Hygiene

All commit messages and version control operations in AniFerret must follow standard Conventional Commit patterns:

1. **Repository & Remote Configuration:**
   - Official Remote URL: `https://github.com/sarmad-rj/aniferret.git`
   - Default Branch: `main`

2. **Commit Message Format:**
   `<type>(<scope>): <short summary>`

3. **Allowed Commit Types:**
   - `feat`: A new user-facing feature or API endpoint.
   - `fix`: A bug fix or error remediation.
   - `docs`: Documentation updates (`SPEC.md`, `CLAUDE.md`, `PROMPTS.md`).
   - `style`: Formatting, missing semi-colons, Prettier/Ruff cleanups.
   - `refactor`: Code change that neither fixes a bug nor adds a feature.
   - `test`: Adding or correcting tests (`pytest`, Playwright).
   - `chore`: Maintenance, dependencies, build configs.

4. **Example Messages:**
   - `feat(dossiers): add progress-locked character trait matrix endpoint`
   - `fix(rag): filter ChromaDB queries by user episode spoiler level`
   - `test(frontend): add mobile viewport navigation drawer unit test`
