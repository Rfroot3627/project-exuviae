import os
import subprocess
from pathlib import Path

# --- Constants ---
REPO_ROOT = Path(r"c:\Github_RRR\project-exuviae")
NODE_VENV_PY = REPO_ROOT / "node" / ".venv" / "Scripts" / "python.exe"
TEST_FILE = REPO_ROOT / "node" / "tests" / "test_config_priority.py"
OUT_FILE = REPO_ROOT / "pytest_results.log"

def run_test():
    cmd = [str(NODE_VENV_PY), "-m", "pytest", "-v", str(TEST_FILE)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT / "node"))
        with open(OUT_FILE, "w", encoding="utf-8") as f:
            f.write(f"Return Code: {result.returncode}\n")
            f.write(f"--- STDOUT ---\n{result.stdout}\n")
            f.write(f"--- STDERR ---\n{result.stderr}\n")
        print(f"Results written to {OUT_FILE}")
    except Exception as e:
        with open(OUT_FILE, "w", encoding="utf-8") as f:
            f.write(f"Execution Error: {str(e)}\n")

if __name__ == "__main__":
    run_test()
