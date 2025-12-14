import subprocess
import os
import sys
import time
from typing import Optional, Tuple, List
from dotenv import load_dotenv

# Load environment variables (optional, mostly for other keys if needed)
load_dotenv()

# --- Configuration ---
MAX_REFINEMENT_LOOPS = 5  # Max times to try fixing the solution
CONSECUTIVE_PASSES_REQUIRED = 5 # Number of times verifier must agree for acceptance
PROMPTS_DIR = "prompts"
SOLVER_PROMPT_FILE = os.path.join(PROMPTS_DIR, "solver_prompt.md")
VERIFIER_PROMPT_FILE = os.path.join(PROMPTS_DIR, "verifier_prompt.md")

# Using CLI aliases or model names
# User has Pro, so we use the models available to CLI.
SOLVER_MODEL = "opus" 
VERIFIER_MODEL = "opus"

def read_file(filepath):
    """Reads a file and returns its content."""
    if not os.path.exists(filepath):
        print(f"⚠️ Warning: File not found: {filepath}")
        return ""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def write_file(filepath, content):
    """Writes content to a file."""
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

def run_claude(prompt: str, model: str = "sonnet") -> Optional[str]:
    """Executes Claude CLI with the given prompt via STDIN."""
    print(f"\n🧠 Claude ({model}) Thinking...")
    executable = "claude.cmd" if os.name == 'nt' else "claude"
    
    try:
        # Use stdin (-) to pass prompt to avoid command line length limits
        cmd = [executable, "--model", model, "--print", "-"]
        
        result = subprocess.run(
            cmd, 
            input=prompt,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=600 # 10 minute timeout
        )
        
        if result.returncode != 0:
            print(f"❌ CLI Error: {result.stderr}")
            # Check for specific errors
            if "Limit reached" in result.stdout or "Limit reached" in result.stderr:
                print("⚠️ Rate Limit Reached! Please wait for your quota to reset.")
            return None
            
        return result.stdout.strip()
        
    except FileNotFoundError:
        print(f"❌ Error: '{executable}' not found. Make sure 'npm install -g @anthropic-ai/claude-code' is run.")
        return None
    except subprocess.TimeoutExpired:
        print("❌ Execution Timed Out")
        return None
    except Exception as e:
        print(f"❌ Execution Error: {e}")
        return None

def read_context_files(directory="context"):
    """Reads all markdown files from the context directory."""
    context_content = ""
    if not os.path.exists(directory):
        return ""
    
    print(f"📂 Scanning '{directory}' for constraints...")
    for filename in os.listdir(directory):
        if filename.endswith(".md"):
            filepath = os.path.join(directory, filename)
            content = read_file(filepath)
            context_content += f"\n\n[Context Document: {filename}]\n{content}"
            print(f"   - Loaded: {filename}")
            
    return context_content

class VerificationPipeline:
    def __init__(self, problem_description: str):
        self.problem = problem_description
        self.solver_prompt = read_file(SOLVER_PROMPT_FILE)
        self.verifier_prompt = read_file(VERIFIER_PROMPT_FILE)
        self.context_data = read_context_files()
        self.current_solution = ""
        self.history = []

    def log(self, step: str, content: str):
        timestamp = time.strftime("%H-%M-%S")
        filename = f"logs/log_{timestamp}_{step}.txt"
        write_file(filename, content)
        print(f"   📄 Log saved: {filename}")

    def step1_solve(self) -> str:
        """Generates the initial solution."""
        print(f"--- Step 1: Initial Solution Generation ({SOLVER_MODEL}) ---")
        full_prompt = f"{self.solver_prompt}\n\n### Context & Requirements ###\n{self.context_data}\n\n### Request ###\n{self.problem}"
        response = run_claude(full_prompt, model=SOLVER_MODEL)
        if not response:
            raise Exception("Failed to generate initial solution.")
        
        self.current_solution = response
        self.log("step1_solution", response)
        return response

    def step3_verify(self, solution: str) -> Tuple[bool, str]:
        """Verifies the solution. Returns (Passed, Bug Report)."""
        print(f"--- Step 3: Verification ({VERIFIER_MODEL}) ---")
        full_prompt = f"{self.verifier_prompt}\n\n### Problem ###\n{self.problem}\n\n### Solution ###\n{solution}"
        
        response = run_claude(full_prompt, model=VERIFIER_MODEL)
        if not response:
             return False, "Verification failed (no response)."
             
        self.log("step3_verification", response)
        
        # Parse Verdict
        is_valid = False
        if "[VERDICT: APPROVED]" in response:
            is_valid = True
        elif "[VERDICT: REJECTED]" in response:
            is_valid = False
        else:
            # Fallback for robustness if tag is missing but context implies success
            if "Final Verdict: The solution is correct" in response:
                is_valid = True
        
        # Double check for Critical Errors just in case
        if "Critical Error" in response:
            is_valid = False
            
        return is_valid, response

    def step5_correction(self, bug_report: str) -> str:
        """Asks the solver to correct the solution based on the bug report."""
        print(f"--- Step 5: Correction ({SOLVER_MODEL}) ---")
        
        full_prompt = f"""{self.solver_prompt}

### Problem ###
{self.problem}

### Previous Solution ###
{self.current_solution}

### Verification Report ###
{bug_report}

### Instruction ###
The previous solution was flagged with the issues above. 
Please provide a **Corrected Solution** that addresses these findings. 
Maintain the same output format (Summary + Detailed Solution).
"""
        response = run_claude(full_prompt, model=SOLVER_MODEL)
        if not response:
            raise Exception("Failed to generate corrected solution.")
            
        self.current_solution = response
        self.log("step5_correction", response)
        return response

    def run(self):
        print(f"🚀 Starting Verification Pipeline for Problem: {self.problem[:50]}...")
        
        # 1. Initial Solve
        try:
            self.step1_solve()
        except Exception as e:
            print(f"❌ Aborted: {e}")
            return

        # Refinement Loop
        for loop_idx in range(MAX_REFINEMENT_LOOPS):
            print(f"\n🔄 Refinement Loop {loop_idx + 1}/{MAX_REFINEMENT_LOOPS}")
            
            consecutive_passes = 0
            bug_report = ""
            
            print(f"   🕵️ Running Robustness Check (Need {CONSECUTIVE_PASSES_REQUIRED} consecutive passes)...")
            
            verified_successfully = True
            
            for v_idx in range(CONSECUTIVE_PASSES_REQUIRED):
                passed, report = self.step3_verify(self.current_solution)
                if passed:
                    consecutive_passes += 1
                    print(f"      ✅ Pass {consecutive_passes}/{CONSECUTIVE_PASSES_REQUIRED}")
                else:
                    print(f"      ❌ Failed at check {v_idx + 1}")
                    bug_report = report
                    verified_successfully = False
                    break # Stop robustness check, go to correction
            
            if verified_successfully:
                print("\n🏆 SUCCESS: Solution passed robust verification!")
                write_file("final_solution.md", self.current_solution)
                print("✅ Final solution saved to 'final_solution.md'")
                return
            else:
                print("\n⚠️ Solution failed verification. Attempting correction...")
                try:
                    self.step5_correction(bug_report)
                except Exception as e:
                    print(f"❌ Correction failed: {e}")
                    return

        print("\n🚫 FAILURE: Maximum refinement loops reached without robust success.")

def main():
    if len(sys.argv) < 2:
        print("Usage: python agent_controller.py <problem_description>")
        # Default test if no arg
        problem = "Generate a Python script to scan a directory recursively."
        print(f"No argument provided. Using default test problem: {problem}")
    else:
        problem = " ".join(sys.argv[1:])

    pipeline = VerificationPipeline(problem)
    pipeline.run()

if __name__ == "__main__":
    main()
