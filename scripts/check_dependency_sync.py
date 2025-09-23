#!/usr/bin/env python3
"""
Check that requirements.txt and pyproject.toml dependencies are in sync.

This prevents CI failures due to missing dependencies in pyproject.toml.
"""
import re
import sys
from pathlib import Path


def parse_requirements_txt(requirements_path: Path) -> set[str]:
    """Parse requirements.txt and return normalized dependency names."""
    if not requirements_path.exists():
        return set()

    deps = set()
    with open(requirements_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                # Extract package name (before == or >= etc)
                package = re.split("[>=<~!]", line)[0].strip()
                deps.add(package.lower())
    return deps


def parse_pyproject_toml(pyproject_path: Path) -> set[str]:
    """Parse pyproject.toml and return normalized dependency names."""
    if not pyproject_path.exists():
        return set()

    deps = set()
    with open(pyproject_path) as f:
        content = f.read()

    # Extract dependencies from [project] section
    in_dependencies = False
    for line in content.split("\n"):
        line = line.strip()

        if line == "dependencies = [":
            in_dependencies = True
            continue
        elif in_dependencies and line == "]":
            break
        elif in_dependencies and line.startswith('"') and not line.startswith("# "):
            # Extract package name from quoted dependency
            dep_line = line.strip('"').strip(",")
            if dep_line:
                package = re.split("[>=<~!]", dep_line)[0].strip()
                deps.add(package.lower())

    return deps


def main() -> int:
    """Check dependency sync between requirements.txt and pyproject.toml."""
    backend_dir = Path(__file__).parent.parent / "backend"
    requirements_path = backend_dir / "requirements.txt"
    pyproject_path = backend_dir / "pyproject.toml"

    requirements_deps = parse_requirements_txt(requirements_path)
    pyproject_deps = parse_pyproject_toml(pyproject_path)

    # Check for missing dependencies
    missing_in_pyproject = requirements_deps - pyproject_deps
    missing_in_requirements = pyproject_deps - requirements_deps

    if missing_in_pyproject:
        print("❌ Dependencies in requirements.txt but missing from pyproject.toml:")
        for dep in sorted(missing_in_pyproject):
            print(f"   - {dep}")
        print()
        print("💡 Add these to pyproject.toml [project] dependencies section")
        print()

    if missing_in_requirements:
        print("⚠️  Dependencies in pyproject.toml but missing from requirements.txt:")
        for dep in sorted(missing_in_requirements):
            print(f"   - {dep}")
        print()

    if missing_in_pyproject or missing_in_requirements:
        print("🚨 Dependency mismatch detected!")
        print(
            "   This will cause CI failures when GitHub Actions can't find required packages."
        )
        print("   Please sync both files to match.")
        return 1

    print("✅ Dependencies are in sync between requirements.txt and pyproject.toml")
    return 0


if __name__ == "__main__":
    sys.exit(main())
