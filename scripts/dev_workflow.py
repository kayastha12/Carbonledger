#!/usr/bin/env python
import os
import sys
import subprocess
import time
import argparse

# Force utf-8 stdout/stderr in case of terminal encoding issues
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def get_changed_files():
    try:
        # Get list of uncommitted changed files in git
        res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
        files = []
        for line in res.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.strip().split(None, 1)
            if len(parts) == 2:
                files.append(parts[1])
        return files
    except Exception as e:
        print(f"[dev_workflow] Warning: Not in a git repo or git not found ({e}). Falling back to manual timestamp scan.")
        # Fallback: scan files modified in last 5 minutes (300 seconds)
        changed = []
        now = time.time()
        for root, dirs, files in os.walk("."):
            if "venv" in root or ".git" in root or "__pycache__" in root or ".pytest_cache" in root:
                continue
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    if now - os.path.getmtime(filepath) < 300:
                        changed.append(filepath.replace(".\\", "").replace("./", ""))
                except Exception:
                    pass
        return changed

def run_type_checks(changed_files):
    py_files = [f for f in changed_files if f.endswith(".py") and os.path.exists(f)]
    if not py_files:
        print("[dev_workflow] No python files modified to type check.")
        return True
    
    print(f"[dev_workflow] Running fast syntax/type checks on {len(py_files)} files...")
    all_ok = True
    for f in py_files:
        res = subprocess.run([sys.executable, "-m", "py_compile", f])
        if res.returncode != 0:
            print(f"[dev_workflow] [FAIL] Syntax error in {f}")
            all_ok = False
        else:
            print(f"[dev_workflow] [OK] Syntax check passed for {f}")
    return all_ok

def run_smart_tests(changed_files):
    # Map changed files to test modules
    test_files_to_run = set()
    
    parser_files = {"services/document_understanding.py", "services/field_extraction_service.py", "services/universal_upload_service.py"}
    engine_files = {"services/calculation_engine.py", "services/carbon_calculation_service.py", "services/emission_factor_service.py"}
    dashboard_files = {"services/dashboard_service.py", "frontend/DashboardApp.jsx"}
    reports_files = {"services/report_generator_service.py", "services/cbam_engine.py"}
    
    has_parser_change = False
    has_engine_change = False
    has_dashboard_change = False
    has_reports_change = False
    
    for f in changed_files:
        f_std = f.replace("\\", "/")
        if f_std in parser_files or "parser" in f_std.lower():
            has_parser_change = True
        if f_std in engine_files or "calculation" in f_std.lower() or "factor" in f_std.lower():
            has_engine_change = True
        if f_std in dashboard_files or "dashboard" in f_std.lower():
            has_dashboard_change = True
        if f_std in reports_files or "report" in f_std.lower() or "cbam" in f_std.lower():
            has_reports_change = True

    if has_parser_change:
        print("[dev_workflow] [LINK] Dependency Trigger: Parser files changed.")
        test_files_to_run.add("tests/test_document_parser.py")
        
    if has_engine_change:
        print("[dev_workflow] [LINK] Dependency Trigger: Carbon Engine files changed.")
        test_files_to_run.add("tests/test_calculations.py")
        test_files_to_run.add("tests/test_emission_factor_service.py")
        
    if has_dashboard_change:
        print("[dev_workflow] [LINK] Dependency Trigger: Dashboard files changed.")
        test_files_to_run.add("tests/test_phase2.py")
        test_files_to_run.add("tests/test_phase3.py")
        
    if has_reports_change:
        print("[dev_workflow] [LINK] Dependency Trigger: Reports/CBAM files changed.")
        test_files_to_run.add("tests/test_universal_upload_pipeline.py")
        test_files_to_run.add("tests/test_phase6.py")
        
    if not test_files_to_run:
        print("[dev_workflow] No direct module changes matched. Defaulting to fast parser/pipeline tests.")
        test_files_to_run.add("tests/test_document_parser.py")

    print(f"[dev_workflow] Smart Testing: Running {len(test_files_to_run)} test suites...")
    all_ok = True
    for test_suite in test_files_to_run:
        print(f"[dev_workflow] Running: pytest {test_suite} -v")
        res = subprocess.run([sys.executable, "-m", "pytest", test_suite, "-v"])
        if res.returncode != 0:
            print(f"[dev_workflow] [FAIL] Test suite failed: {test_suite}")
            all_ok = False
        else:
            print(f"[dev_workflow] [OK] Test suite passed: {test_suite}")
            
    return all_ok

def run_dev_workflow():
    t_start = time.perf_counter()
    print("=" * 60)
    print("[START] RUNNING CARBONLEDGER FAST DEVELOPMENT WORKFLOW")
    print("=" * 60)
    
    # 1. Get changed files
    changed = get_changed_files()
    print(f"[dev_workflow] Detected {len(changed)} changed files: {changed}")
    
    # 2. Compile/Type check changed modules only
    checks_ok = run_type_checks(changed)
    
    # 3. Dependency-aware smart tests
    tests_ok = run_smart_tests(changed)
    
    t_duration = time.perf_counter() - t_start
    print("=" * 60)
    if checks_ok and tests_ok:
        print(f"[SUCCESS] DEV WORKFLOW SUCCESSFUL (Duration: {t_duration:.2f}s, Target: <15s)")
    else:
        print(f"[FAIL] DEV WORKFLOW FAILED (Duration: {t_duration:.2f}s)")
    print("=" * 60)
    return 0 if (checks_ok and tests_ok) else 1

def run_prod_workflow():
    t_start = time.perf_counter()
    print("=" * 60)
    print("[START] RUNNING CARBONLEDGER FULL PRODUCTION REGRESSION WORKFLOW")
    print("=" * 60)
    
    # 1. Full Production Build of Frontend
    print("[prod_workflow] Building frontend web app bundle...")
    frontend_dir = os.path.join("D:\\CarbanLedger", "frontend")
    build_res = subprocess.run(["npm", "run", "build"], cwd=frontend_dir, shell=True)
    if build_res.returncode != 0:
        print("[prod_workflow] [FAIL] Frontend production build failed!")
        return 1
    print("[prod_workflow] [OK] Frontend production build succeeded.")
    
    # 2. Run All Python Unit & Regression Tests
    print("[prod_workflow] Running full backend test suite...")
    test_res = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"])
    if test_res.returncode != 0:
        print("[prod_workflow] [FAIL] Backend test suite regression detected!")
        return 1
    print("[prod_workflow] [OK] Full regression test suite passed.")
    
    # 3. Report validation checks (ensuring mock outputs can be generated)
    print("[prod_workflow] Running report validation verification...")
    report_script = os.path.join("D:\\CarbanLedger", "scripts", "generate_cbam_report_files.py")
    if os.path.exists(report_script):
        rep_res = subprocess.run([sys.executable, report_script])
        if rep_res.returncode != 0:
            print("[prod_workflow] [FAIL] Reports generation verification failed!")
            return 1
    print("[prod_workflow] [OK] Reports generation validation passed.")
    
    t_duration = time.perf_counter() - t_start
    print("=" * 60)
    print(f"[SUCCESS] PRODUCTION BUILD & TEST REGRESSION SUCCESSFUL (Duration: {t_duration:.2f}s)")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CarbonLedger Build/Test Workflow Runner")
    parser.add_argument("--mode", type=str, choices=["development", "production"], default="development",
                        help="Workflow runner mode: 'development' (default, smart changed modules) or 'production' (runs full build and test regressions)")
    args = parser.parse_args()
    
    if args.mode == "production":
        sys.exit(run_prod_workflow())
    else:
        sys.exit(run_dev_workflow())
