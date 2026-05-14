#!/usr/bin/env python3
"""Test coherency checker — structural validation of coverage matrix.

Checks:
1. Every requirement with status 'covered' has ≥1 test file
2. Every test file referenced in the matrix exists on disk
3. Every test function referenced in the matrix exists in its file
4. No orphaned test files (test exists but isn't in the matrix)
5. Marker assignments match CI job configuration
6. No requirements stuck in 'gap' status with P1 priority

Usage:
    python tools/coherency_check.py                    # full check
    python tools/coherency_check.py --format json      # machine-readable output
    python tools/coherency_check.py --strict           # exit code 1 on any warning
"""

import argparse
import ast
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
MATRIX_PATH = ROOT / "coverage" / "matrix.yaml"
TESTS_DIR = ROOT / "tests"


def load_matrix():
    with open(MATRIX_PATH) as f:
        return yaml.safe_load(f)


def check_covered_have_tests(matrix):
    """Every requirement with status 'covered' must have ≥1 test."""
    violations = []
    for req_id, req in matrix["requirements"].items():
        if req["status"] == "covered" and not req.get("tests"):
            violations.append({
                "check": "covered_without_tests",
                "severity": "error",
                "requirement": req_id,
                "message": f"{req_id} marked 'covered' but has no tests listed",
            })
    return violations


def check_test_files_exist(matrix):
    """Every test file referenced in the matrix must exist on disk."""
    violations = []
    seen_files = set()
    for req_id, req in matrix["requirements"].items():
        for test in req.get("tests", []):
            test_file = test["file"]
            if test_file in seen_files:
                continue
            seen_files.add(test_file)
            full_path = ROOT / test_file
            if not full_path.exists():
                violations.append({
                    "check": "missing_test_file",
                    "severity": "error",
                    "requirement": req_id,
                    "file": test_file,
                    "message": f"Test file '{test_file}' does not exist",
                })
    return violations


def extract_test_functions(filepath):
    """Parse a Python test file and extract all test class::method names."""
    try:
        source = filepath.read_text()
        tree = ast.parse(source)
    except (SyntaxError, FileNotFoundError):
        return set()

    functions = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                    functions.add(f"{class_name}::{item.name}")
        elif isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            # Top-level test functions (not in a class)
            if not any(isinstance(p, ast.ClassDef) for p in ast.walk(tree)
                       if node in getattr(p, 'body', [])):
                functions.add(node.name)
    return functions


def check_test_functions_exist(matrix):
    """Every test function referenced in the matrix must exist in its file."""
    violations = []
    file_functions_cache = {}

    for req_id, req in matrix["requirements"].items():
        for test in req.get("tests", []):
            test_file = test["file"]
            function_ref = test["function"]

            if test_file not in file_functions_cache:
                full_path = ROOT / test_file
                if full_path.exists():
                    file_functions_cache[test_file] = extract_test_functions(full_path)
                else:
                    continue  # file missing — caught by check_test_files_exist

            # Handle parametrized tests: TestClass::test_func covers test_func[param1], etc.
            base_function = function_ref.split("[")[0]
            available = file_functions_cache[test_file]

            if base_function not in available:
                violations.append({
                    "check": "missing_test_function",
                    "severity": "error",
                    "requirement": req_id,
                    "file": test_file,
                    "function": function_ref,
                    "message": f"Function '{function_ref}' not found in '{test_file}'",
                    "available": sorted(available),
                })
    return violations


def check_orphaned_tests(matrix):
    """Find test files on disk that aren't referenced in the matrix."""
    # Collect all test files from matrix
    matrix_files = set()
    for req in matrix["requirements"].values():
        for test in req.get("tests", []):
            matrix_files.add(test["file"])

    # Find all test files on disk
    violations = []
    for test_file in TESTS_DIR.rglob("test_*.py"):
        relative = str(test_file.relative_to(ROOT))
        if relative not in matrix_files:
            violations.append({
                "check": "orphaned_test",
                "severity": "warning",
                "file": relative,
                "message": f"Test file '{relative}' exists but is not in coverage matrix",
            })
    return violations


def check_marker_consistency(matrix):
    """Verify test markers match their assigned CI job."""
    violations = []
    ci_jobs = matrix.get("ci_jobs", {})
    marker_map = {}
    for job_name, job_config in ci_jobs.items():
        marker_map[job_name] = job_config.get("marker", job_name)

    for req_id, req in matrix["requirements"].items():
        for test in req.get("tests", []):
            test_file = test["file"]
            ci_job = test.get("ci_job")
            if not ci_job or ci_job not in marker_map:
                continue

            full_path = ROOT / test_file
            if not full_path.exists():
                continue

            source = full_path.read_text()
            expected_marker = ci_job
            # Check the primary marker (not compound markers like "regression or contract")
            if expected_marker in ("regression",) and "contract" in test_file:
                expected_marker = "contract"  # contract tests run in regression job

            marker_pattern = f"@pytest.mark.{expected_marker}"
            if marker_pattern not in source:
                # Check if it's a contract test in the regression job
                if ci_job == "regression" and "@pytest.mark.contract" in source:
                    continue
                violations.append({
                    "check": "marker_mismatch",
                    "severity": "warning",
                    "requirement": req_id,
                    "file": test_file,
                    "ci_job": ci_job,
                    "message": f"Test '{test_file}' assigned to CI job '{ci_job}' "
                               f"but marker '@pytest.mark.{expected_marker}' not found",
                })
    return violations


def check_p1_gaps(matrix):
    """Flag P1 requirements with no test coverage."""
    violations = []
    for req_id, req in matrix["requirements"].items():
        if req.get("priority") == "P1" and req["status"] == "gap":
            violations.append({
                "check": "p1_gap",
                "severity": "warning",
                "requirement": req_id,
                "description": req["description"],
                "message": f"P1 requirement '{req_id}' has no test coverage: {req['description']}",
            })
    return violations


def run_all_checks(matrix):
    """Run all coherency checks and return aggregated results."""
    all_violations = []
    all_violations.extend(check_covered_have_tests(matrix))
    all_violations.extend(check_test_files_exist(matrix))
    all_violations.extend(check_test_functions_exist(matrix))
    all_violations.extend(check_orphaned_tests(matrix))
    all_violations.extend(check_marker_consistency(matrix))
    all_violations.extend(check_p1_gaps(matrix))
    return all_violations


def format_text(violations, matrix):
    """Format results as human-readable text."""
    lines = []
    lines.append("=" * 60)
    lines.append("TEST COHERENCY CHECK")
    lines.append("=" * 60)

    # Summary counts
    reqs = matrix["requirements"]
    covered = sum(1 for r in reqs.values() if r["status"] == "covered")
    gaps = sum(1 for r in reqs.values() if r["status"] == "gap")
    total = len(reqs)
    lines.append(f"\nRequirements: {total} total, {covered} covered, {gaps} gaps")

    total_tests = sum(len(r.get("tests", [])) for r in reqs.values())
    lines.append(f"Test mappings: {total_tests}")

    errors = [v for v in violations if v["severity"] == "error"]
    warnings = [v for v in violations if v["severity"] == "warning"]
    lines.append(f"Violations: {len(errors)} errors, {len(warnings)} warnings")

    if not violations:
        lines.append("\n✓ All coherency checks passed")
    else:
        if errors:
            lines.append(f"\n--- ERRORS ({len(errors)}) ---")
            for v in errors:
                lines.append(f"  [{v['check']}] {v['message']}")

        if warnings:
            lines.append(f"\n--- WARNINGS ({len(warnings)}) ---")
            for v in warnings:
                lines.append(f"  [{v['check']}] {v['message']}")

    # Coverage gap summary
    gap_reqs = {k: v for k, v in reqs.items() if v["status"] == "gap"}
    if gap_reqs:
        lines.append(f"\n--- KNOWN GAPS ({len(gap_reqs)}) ---")
        for req_id, req in gap_reqs.items():
            priority = req.get("priority", "?")
            lines.append(f"  [{priority}] {req_id}: {req['description']}")
            if req.get("notes"):
                lines.append(f"       Note: {req['notes']}")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Test coherency checker")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--strict", action="store_true",
                        help="Exit with code 1 on any violation (including warnings)")
    args = parser.parse_args()

    if not MATRIX_PATH.exists():
        print(f"Error: Coverage matrix not found at {MATRIX_PATH}", file=sys.stderr)
        sys.exit(1)

    matrix = load_matrix()
    violations = run_all_checks(matrix)

    if args.format == "json":
        output = {
            "violations": violations,
            "summary": {
                "total_requirements": len(matrix["requirements"]),
                "covered": sum(1 for r in matrix["requirements"].values() if r["status"] == "covered"),
                "gaps": sum(1 for r in matrix["requirements"].values() if r["status"] == "gap"),
                "errors": sum(1 for v in violations if v["severity"] == "error"),
                "warnings": sum(1 for v in violations if v["severity"] == "warning"),
            },
        }
        print(json.dumps(output, indent=2))
    else:
        print(format_text(violations, matrix))

    # Exit code
    errors = [v for v in violations if v["severity"] == "error"]
    if errors:
        sys.exit(1)
    if args.strict and violations:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
