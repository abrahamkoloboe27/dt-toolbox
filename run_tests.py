#!/usr/bin/env python
"""Test runner script for dt-toolbox.

This script runs all tests with various options.
"""
import sys
import subprocess


def run_tests(test_type="all", verbose=False):
    """Run tests based on type.
    
    Args:
        test_type: Type of tests to run (all, unit, integration, scenarios, edge)
        verbose: Enable verbose output
    """
    base_cmd = [sys.executable, "-m", "pytest"]
    
    if verbose:
        base_cmd.append("-v")
    else:
        base_cmd.append("-q")
    
    test_patterns = {
        "all": ["tests/"],
        "unit": [
            "tests/test_config.py",
            "tests/test_handlers.py",
            "tests/test_monitor.py",
            "tests/test_notifier.py",
            "tests/test_redaction.py",
            "tests/test_storage.py",
        ],
        "integration": ["tests/test_integration.py"],
        "scenarios": ["tests/test_scenarios.py"],
        "edge": ["tests/test_edge_cases.py"],
    }
    
    if test_type not in test_patterns:
        print(f"Unknown test type: {test_type}")
        print(f"Available types: {', '.join(test_patterns.keys())}")
        return 1
    
    cmd = base_cmd + test_patterns[test_type]
    
    # Create temporary pytest.ini to skip coverage
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        f.write('[pytest]\n')
        f.write('testpaths = tests\n')
        f.write('python_files = test_*.py\n')
        f.write('python_classes = Test*\n')
        f.write('python_functions = test_*\n')
        temp_ini = f.name
    
    try:
        # Add config file to command
        cmd.extend(["-c", temp_ini])
        
        print(f"Running {test_type} tests...")
        print(f"Command: {' '.join(cmd)}")
        print("-" * 80)
        
        result = subprocess.run(cmd)
        return result.returncode
    finally:
        # Cleanup
        if os.path.exists(temp_ini):
            os.unlink(temp_ini)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run dt-toolbox tests")
    parser.add_argument(
        "test_type",
        nargs="?",
        default="all",
        choices=["all", "unit", "integration", "scenarios", "edge"],
        help="Type of tests to run",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available tests",
    )
    
    args = parser.parse_args()
    
    if args.list:
        print("Available test types:")
        print("  all         - Run all tests")
        print("  unit        - Run unit tests only")
        print("  integration - Run integration tests")
        print("  scenarios   - Run scenario-based tests")
        print("  edge        - Run edge case tests")
        return 0
    
    return run_tests(args.test_type, args.verbose)


if __name__ == "__main__":
    sys.exit(main())
