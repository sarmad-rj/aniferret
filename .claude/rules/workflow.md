# Rule: Core Agentic Workflow

## 1. Caveman Mode (Token & Output Optimization)
- Be extremely terse. Zero polite conversational fluff or filler greetings.
- Provide direct task logs, file paths, implementation plans, and clean code diffs.
- Never restate the user's prompt back to them.

## 2. Pre-Implementation Phase
- Check registered MCP server tools for relevant framework documentation before writing boilerplate.
- Read `SPEC.md` and trigger the `superpower-planner` skill to output a step-by-step execution plan prior to file creation or major edits.

## 3. Post-Implementation Phase (QA & Review Loop)
- Trigger `.claude/agents/code-reviewer.md` to verify Airbnb React formatting and security standards.
- Run `.claude/agents/qa-agent.md` (Playwright headless Chrome) to verify desktop ($1280 \times 720$) and mobile ($375 \times 667$) views.
- Do NOT declare a task complete if tests fail or layout overflows.

## 4. Mandatory PROMPTS.md Logging
- Every user prompt or instruction MUST be appended to `PROMPTS.md`.
- Record: (1) timestamp, (2) user prompt summary, (3) tools/models executed, (4) generated artifacts/corrections.
- Never overwrite past entries — always append to the bottom.
