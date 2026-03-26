#!/usr/bin/env python3
"""
Run all runnable tests for AI Trading Analytics.

Runs (from project root, no server required):
  - tests/test_validation.py
  - tests/test_api_basic.py
  - tests/test_db_connection.py
  - tests/test_exchange_client.py

Integration tests (require Flask app running on port 5002):
  - tests/test_api.py
  - tests/test_api_endpoints.py

Usage: python3 run_tests.py
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

STANDALONE_TESTS = [
    "tests/test_validation.py",
    "tests/test_api_basic.py",
    "tests/test_db_connection.py",
    "tests/test_exchange_client.py",
]

INTEGRATION_TESTS = [
    "tests/test_api.py",
    "tests/test_api_endpoints.py",
]


def run_script(rel_path: str) -> bool:
    """Run a test script; return True if exit code 0."""
    path = PROJECT_ROOT / rel_path
    if not path.exists():
        print(f"  ⚠️  {rel_path} not found")
        return False
    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(PROJECT_ROOT),
        capture_output=False,
    )
    return result.returncode == 0


def main():
    print("=" * 70)
    print("AI Trading Analytics - Running standalone tests")
    print("=" * 70)

    passed = 0
    failed = 0
    for rel in STANDALONE_TESTS:
        print(f"\n>>> Running {rel}")
        print("-" * 70)
        if run_script(rel):
            passed += 1
            print(f"\n✅ {rel} PASSED")
        else:
            failed += 1
            print(f"\n❌ {rel} FAILED (exit code != 0)")

    print("\n" + "=" * 70)
    print(f"Standalone tests: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed > 0:
        print("\n💡 Fix the failing tests above, then run again.")
        sys.exit(1)

    print("\n💡 To run integration tests (need Flask app on port 5002):")
    for rel in INTEGRATION_TESTS:
        print(f"   python3 {rel}")
    print("\n   Start app first: python3 app.py")
    print("=" * 70)
    sys.exit(0)


if __name__ == "__main__":
    main()
