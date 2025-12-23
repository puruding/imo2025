# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Reflexion Agent System** that uses Claude AI in a solver-verifier loop to generate and refine code solutions. The system implements an iterative refinement process where a "solver" generates code and a "verifier" reviews it, creating a feedback loop until the solution meets quality standards.

## Architecture

### Core Components

**`agent_controller.py`** - Main orchestration script
- `VerificationPipeline` class manages the solver-verifier loop
- Executes Claude CLI commands via subprocess
- Handles up to 5 refinement loops with robust verification (5 consecutive passes required)
- Models: Uses "opus" for both solver and verifier (configurable via `SOLVER_MODEL` and `VERIFIER_MODEL`)

**`prompts/`** - System prompt definitions
- `solver_prompt.md`: Defines the Senior Software Engineer persona that generates code
- `verifier_prompt.md`: Defines the Lead Code Reviewer persona that validates solutions
- Prompts use strict output formatting and verdict tags (`[VERDICT: APPROVED]` or `[VERDICT: REJECTED]`)

**`context/`** - Architectural constraints and requirements
- Contains markdown files (e.g., `example_architecture.md`) that define:
  - Architecture patterns (Clean Architecture, DDD)
  - Directory structure requirements
  - Code style requirements (dataclasses, typing)
- All context files are automatically loaded and injected into prompts

**`logs/`** - Execution logs
- Timestamped logs for each step: solution generation, verification, correction
- Format: `log_{timestamp}_{step}.txt`

### Workflow

1. **Initial Solution** (`step1_solve`): Solver generates code based on problem + context
2. **Verification Loop**: Solution is verified 5 consecutive times for robustness
3. **Correction** (`step5_correction`): If verification fails, solver receives bug report and corrects
4. **Iteration**: Repeats up to 5 times until solution passes robust verification
5. **Output**: Final solution saved to `final_solution.md`

### Key Design Patterns

- **Prompt Injection**: Context files are dynamically injected with headers like `### Context & Requirements ###`, `### Request ###`, `### Verification Report ###`
- **Verdict Parsing**: Verifier outputs must contain exact tags for automation
- **Robustness Check**: Requires 5 consecutive successful verifications to prevent false positives
- **Logging**: Every step is logged with timestamps for debugging and analysis

## Development Commands

### Setup
```bash
# Install dependencies (Poetry)
poetry install

# Or using pip with Python 3.11+
pip install pytest requests python-dotenv black
```

### Running the Agent
```bash
# Basic usage
python agent_controller.py "<problem description>"

# Example
python agent_controller.py "Create a REST API for user management following Clean Architecture"

# No argument runs default test problem
python agent_controller.py
```

### Testing
```bash
# Run tests
pytest

# Format code
black agent_controller.py
```

### Prerequisites
- Python 3.11+
- Claude CLI installed: `npm install -g @anthropic-ai/claude-code`
- Claude CLI must be accessible as `claude` (Unix) or `claude.cmd` (Windows)
- Claude Pro account (uses "opus" model by default)

## Configuration

### Key Constants in `agent_controller.py`
```python
MAX_REFINEMENT_LOOPS = 5  # Max correction attempts
CONSECUTIVE_PASSES_REQUIRED = 5  # Verification robustness threshold
SOLVER_MODEL = "opus"  # Available: "opus", "sonnet", "haiku"
VERIFIER_MODEL = "opus"
```

### Adding Context Documents
1. Create `.md` files in `context/` directory
2. Files are automatically loaded and injected into prompts
3. Context should define:
   - Architecture patterns
   - Database schemas
   - Code style requirements
   - Approved libraries/frameworks

### Modifying Prompts
- Edit `prompts/solver_prompt.md` or `prompts/verifier_prompt.md`
- Use git branches (e.g., `feat/stricter-verifier`) to test changes
- Maintain required sections and verdict tags for automation compatibility

## Error Handling

**Rate Limits**: System detects "Limit reached" errors and suggests waiting
**Timeouts**: 10-minute timeout per Claude CLI call
**File Not Found**: Checks for Claude CLI executable and provides install instructions
**Verification Failures**: Captures and logs full bug reports for correction loop
