"""
Test Runner and Coverage Report Generator
Runs all tests and generates coverage reports
"""

import subprocess
import sys
from pathlib import Path


def run_tests():
    """Run all tests with coverage"""
    
    print("=" * 80)
    print("🧪 Running Trading Strategies Test Suite")
    print("=" * 80)
    
    # Run pytest with coverage
    cmd = [
        'pytest',
        'tests/',
        '-v',
        '--tb=short',
        '--cov=services',
        '--cov=models',
        '--cov=dashboard',
        '--cov-report=html',
        '--cov-report=term-missing',
    ]
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    
    print("\n" + "=" * 80)
    if result.returncode == 0:
        print("✅ All tests passed!")
        print("📊 Coverage report generated in htmlcov/index.html")
    else:
        print("❌ Some tests failed. See output above.")
    print("=" * 80)
    
    return result.returncode


def run_specific_test(test_file: str):
    """Run a specific test file"""
    
    print(f"\n🧪 Running {test_file}")
    print("=" * 80)
    
    cmd = [
        'pytest',
        f'tests/{test_file}',
        '-v',
        '--tb=short'
    ]
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    
    return result.returncode


def run_test_class(test_file: str, test_class: str):
    """Run a specific test class"""
    
    print(f"\n🧪 Running {test_class} from {test_file}")
    print("=" * 80)
    
    cmd = [
        'pytest',
        f'tests/{test_file}::{test_class}',
        '-v',
        '--tb=short'
    ]
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    
    return result.returncode


if __name__ == '__main__':
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--file' and len(sys.argv) > 2:
            sys.exit(run_specific_test(sys.argv[2]))
        elif sys.argv[1] == '--class' and len(sys.argv) > 3:
            sys.exit(run_test_class(sys.argv[2], sys.argv[3]))
    
    sys.exit(run_tests())
