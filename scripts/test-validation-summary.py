#!/usr/bin/env python3

"""
Test Validation Summary Script
Validates the test organization and Docker setup after FastAPI code merging.
"""

import os
import sys
from pathlib import Path

def validate_test_structure():
    """Validate the test directory structure."""
    print("🧪 Production RAG System - Test Organization Validation")
    print("=" * 60)
    
    base_path = Path(__file__).parent.parent
    tests_path = base_path / "tests"
    
    print(f"📁 Base path: {base_path}")
    print(f"📁 Tests path: {tests_path}")
    print()
    
    # Check main directories
    directories = {
        "tests": tests_path,
        "tests/unit": tests_path / "unit",
        "tests/integration": tests_path / "integration", 
        "tests/component": tests_path / "component",
        "tests/scripts": tests_path / "scripts"
    }
    
    print("📂 Directory Structure:")
    for name, path in directories.items():
        if path.exists():
            if path.is_dir():
                num_files = len([f for f in path.rglob("*.py") if f.is_file()])
                print(f"   ✅ {name:<20} ({num_files} Python files)")
            else:
                print(f"   ❌ {name:<20} (not a directory)")
        else:
            print(f"   ❌ {name:<20} (missing)")
    
    print()
    
    # Check configuration files
    config_files = {
        "pytest.ini": base_path / "pytest.ini",
        "Dockerfile": base_path / "Dockerfile",
        "docker-compose.test.yml": base_path / "docker-compose.test.yml",
        "Makefile": base_path / "Makefile",
        "tests/conftest.py": tests_path / "conftest.py"
    }
    
    print("📄 Configuration Files:")
    for name, path in config_files.items():
        if path.exists():
            print(f"   ✅ {name}")
        else:
            print(f"   ❌ {name} (missing)")
    
    print()
    
    # Count test files by category
    print("📊 Test File Counts:")
    
    for category in ["unit", "integration", "component", "scripts"]:
        category_path = tests_path / category
        if category_path.exists():
            py_files = list(category_path.glob("test_*.py"))
            sh_files = list(category_path.glob("test-*.sh")) if category == "scripts" else []
            total_files = len(py_files) + len(sh_files)
            print(f"   {category.capitalize():<12}: {total_files} test files")
            
            if py_files:
                for py_file in py_files:
                    print(f"      📝 {py_file.name}")
            if sh_files:
                for sh_file in sh_files:
                    print(f"      📜 {sh_file.name}")
        else:
            print(f"   {category.capitalize():<12}: 0 test files (directory missing)")
    
    print()
    
    # Docker setup validation
    print("🐳 Docker Setup:")
    docker_files = [
        base_path / "Dockerfile",
        base_path / "docker-compose.yml", 
        base_path / "docker-compose.test.yml"
    ]
    
    for docker_file in docker_files:
        if docker_file.exists():
            print(f"   ✅ {docker_file.name}")
        else:
            print(f"   ❌ {docker_file.name} (missing)")
    
    # Test runner scripts
    print()
    print("🚀 Test Runner Scripts:")
    script_files = [
        base_path / "scripts" / "run-tests-docker.sh",
        base_path / "scripts" / "test-validation-summary.py"
    ]
    
    for script_file in script_files:
        if script_file.exists():
            print(f"   ✅ {script_file.name}")
        else:
            print(f"   ❌ {script_file.name} (missing)")
    
    print()
    print("✅ Test Organization Validation Complete!")
    print()
    print("🎯 Next Steps:")
    print("   1. Run unit tests: ./scripts/run-tests-docker.sh unit")
    print("   2. Run integration tests: ./scripts/run-tests-docker.sh integration") 
    print("   3. Run component tests: ./scripts/run-tests-docker.sh component")
    print("   4. Run all tests: ./scripts/run-tests-docker.sh all")
    print("   5. Fix any failing tests by updating import paths")
    print()
    print("📚 Documentation:")
    print("   See docs/testing-guide.md for comprehensive testing information")

if __name__ == "__main__":
    validate_test_structure()
