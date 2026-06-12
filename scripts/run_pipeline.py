"""
Bluestock Mutual Fund Capstone Project
Master Pipeline Execution Script (run_pipeline.py)
====================================================
Runs the complete end-to-end analytics pipeline in order:

  Stage 1 — ETL Pipeline          : scripts/etl_pipeline.py
  Stage 2 — EDA & Visualisation   : scripts/run_eda.py
  Stage 3 — Performance Analytics : scripts/run_performance.py
  Stage 4 — Advanced Analytics    : scripts/run_advanced_analytics.py
  Stage 5 — Dashboard Generation  : scripts/run_dashboard.py

Usage:
    python scripts/run_pipeline.py           # run all stages
    python scripts/run_pipeline.py --stage 3 # run from stage 3 onward
    python scripts/run_pipeline.py --only 4  # run only stage 4
"""

import sys
import time
import argparse
import subprocess
from pathlib import Path


def setup_paths():
    script_dir   = Path(__file__).resolve().parent
    project_root = script_dir.parent if script_dir.name == "scripts" else Path(".")
    return project_root


STAGES = {
    1: ("ETL Pipeline",          "scripts/etl_pipeline.py"),
    2: ("EDA & Visualisation",   "scripts/run_eda.py"),
    3: ("Performance Analytics", "scripts/run_performance.py"),
    4: ("Advanced Analytics",    "scripts/run_advanced_analytics.py"),
    5: ("Dashboard Generation",  "scripts/run_dashboard.py"),
}


def run_stage(stage_num: int, stage_name: str, script_rel: str, project_root: Path) -> bool:
    """Run a single pipeline stage and return True on success."""
    script_path = project_root / script_rel
    sep = "=" * 65
    print(f"\n{sep}")
    print(f"  STAGE {stage_num}: {stage_name}")
    print(f"  Script : {script_path}")
    print(f"{sep}")

    if not script_path.exists():
        print(f"  [ERROR] Script not found: {script_path}")
        return False

    start = time.time()
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(project_root),
        capture_output=False,
    )
    elapsed = time.time() - start

    if result.returncode == 0:
        print(f"\n  ✅ Stage {stage_num} completed in {elapsed:.1f}s")
        return True
    else:
        print(f"\n  ❌ Stage {stage_num} FAILED (exit code {result.returncode}) after {elapsed:.1f}s")
        return False


def main():
    project_root = setup_paths()

    parser = argparse.ArgumentParser(
        description="Bluestock MF Capstone — Master Pipeline Runner"
    )
    parser.add_argument(
        "--stage", type=int, default=1,
        help="Start from this stage number (default: 1 = run all)"
    )
    parser.add_argument(
        "--only", type=int, default=None,
        help="Run only this specific stage number"
    )
    parser.add_argument(
        "--stop-on-error", action="store_true", default=True,
        help="Stop the pipeline if a stage fails (default: True)"
    )
    args = parser.parse_args()

    banner = r"""
  ╔══════════════════════════════════════════════════════════════╗
  ║    BLUESTOCK MUTUAL FUND ANALYTICS — MASTER PIPELINE        ║
  ║    Capstone Project I                                        ║
  ╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)
    print(f"  Project Root : {project_root}")
    print(f"  Python       : {sys.version.split()[0]}")

    t0 = time.time()
    failed = []

    if args.only is not None:
        stages_to_run = {args.only: STAGES[args.only]} if args.only in STAGES else {}
    else:
        stages_to_run = {k: v for k, v in STAGES.items() if k >= args.stage}

    if not stages_to_run:
        print("  [ERROR] No valid stages selected.")
        sys.exit(1)

    for num, (name, script) in stages_to_run.items():
        ok = run_stage(num, name, script, project_root)
        if not ok:
            failed.append(num)
            if args.stop_on_error:
                print(f"\n  Pipeline halted at stage {num}. Fix the issue and re-run.")
                break

    elapsed_total = time.time() - t0
    print("\n" + "=" * 65)
    if not failed:
        print(f"  🎉 PIPELINE COMPLETE — all stages passed in {elapsed_total:.1f}s")
    else:
        print(f"  ⚠  Pipeline finished with failures: stages {failed}")
        print(f"     Total time: {elapsed_total:.1f}s")
    print("=" * 65)


if __name__ == "__main__":
    main()
