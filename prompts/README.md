# 🧠 AI Agent Prompts

This directory contains the "System Prompts" that define the personas and behavior of the AI Agent.

## 📂 File Structure

| File | Role | Description |
|------|------|-------------|
| **`solver_prompt.md`** | 🧑‍💻 Senior Software Engineer | Generates code adhering to `context/`. Focuses on implementation details and strictly follows the "Iterative Refinement Process". |
| **`verifier_prompt.md`** | 🕵️ Lead Code Reviewer | Validates the Solver's code. Uses strict verdict tags (`[VERDICT: APPROVED/REJECTED]`) to control the loop. |

## 🤝 Interaction Protocol

The python controller (`agent_controller.py`) injects context and parses outputs based on specific signals defined in these files.

### Input Injection (Controller -> AI)
The AI expects the following headers to be appended to these prompts:
- `### Context & Requirements ###`: Architecture & DB Schemas.
- `### Request ###`: The user's goal.
- `### Verification Report ###`: Feedback from the previous loop (if any).

### Output Signals (AI -> Controller)
The `verifier_prompt.md` dictates strict tags for automation:
- `[VERDICT: APPROVED]`: The workflow succeeds.
- `[VERDICT: REJECTED]`: The workflow enters a correction loop.
- `Critical Error`: Keywords that trigger immediate rejection.

## 📦 Versioning Strategy

*   **Changes**: When modifying prompts, use git commits to track effectiveness.
*   **Experiments**: Create branches (e.g., `feat/stricter-verifier`) to test prompt changes without breaking the stable pipeline.
