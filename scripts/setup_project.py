# Master setup orchestration script for CarbonLedger
import os
import sys
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_script(script_name):
    script_path = os.path.join(ROOT, "scripts", script_name)
    print(f"\nRunning: {script_name}...")
    res = subprocess.run([sys.executable, script_path], cwd=ROOT)
    if res.returncode != 0:
        print(f"[!] Error running script {script_name} (Exit code: {res.returncode})")
        sys.exit(res.returncode)
    print(f"[-] Completed: {script_name}")

def main():
    print("=" * 60)
    print("CarbonLedger Production Environment Setup Orchestrator")
    print("=" * 60)
    
    # Step 1: Decompress datasets
    run_script("decompress_datasets.py")
    
    # Step 2: Pre-download AI models
    run_script("download_models.py")
    
    # Step 3: Rebuild Vector DB (which also cleans raw factor worksheets)
    run_script("rebuild_vector_db.py")
    
    print("\n" + "=" * 60)
    print("CarbonLedger environment setup is successfully completed!")
    print("You can now run 'python -m api.main' and 'npm run dev' to start the application.")
    print("=" * 60)

if __name__ == "__main__":
    main()
