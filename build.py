#!/usr/bin/env python3
"""
Build script for Plant Courier WASM game.
Builds the game and copies output to docs/ for GitHub Pages deployment.

Usage:
    uv run build.py          # Build only
    uv run build.py --serve  # Build and start local server
    uv run build.py --clean  # Clean build artifacts
"""

import subprocess
import shutil
import sys
from pathlib import Path

# Paths - source files are directly in the project root
PROJECT_ROOT = Path(__file__).parent
BUILD_DIR = PROJECT_ROOT / "build" / "web"
DOCS_DIR = PROJECT_ROOT / "docs"


def clean():
    """Remove build artifacts"""
    print("Cleaning build artifacts...")

    if BUILD_DIR.parent.exists():
        shutil.rmtree(BUILD_DIR.parent)
        print(f"  Removed {BUILD_DIR.parent}")

    if DOCS_DIR.exists():
        shutil.rmtree(DOCS_DIR)
        print(f"  Removed {DOCS_DIR}")

    # Clean pycache
    for pycache in PROJECT_ROOT.rglob("__pycache__"):
        shutil.rmtree(pycache)
        print(f"  Removed {pycache}")

    print("Clean complete.")


def build():
    """Build the WASM game using pygbag"""
    print("Building WASM game...")
    print(f"  Source: {PROJECT_ROOT}")

    # Run pygbag build using uv
    result = subprocess.run(
        ["uv", "run", "python", "-m", "pygbag", "--build", "."],
        cwd=PROJECT_ROOT,
        capture_output=False
    )

    if result.returncode != 0:
        print("ERROR: pygbag build failed!")
        sys.exit(1)

    if not BUILD_DIR.exists():
        print(f"ERROR: Build output not found at {BUILD_DIR}")
        sys.exit(1)

    print(f"  Build output: {BUILD_DIR}")

    # Copy to docs folder
    print(f"Copying to {DOCS_DIR}...")

    if DOCS_DIR.exists():
        shutil.rmtree(DOCS_DIR)

    shutil.copytree(BUILD_DIR, DOCS_DIR)

    # Count files
    files = list(DOCS_DIR.rglob("*"))
    file_count = len([f for f in files if f.is_file()])

    print(f"  Copied {file_count} files to {DOCS_DIR}")
    print()
    print("Build complete!")
    print()
    print("To deploy to GitHub Pages:")
    print("  1. Push the docs/ folder to your repository")
    print("  2. Go to Settings > Pages")
    print("  3. Set Source to 'Deploy from a branch'")
    print("  4. Select branch 'main' and folder '/docs'")
    print()


def serve():
    """Build and start local server"""
    print("Building and starting server...")
    print(f"  Source: {PROJECT_ROOT}")

    # Run pygbag with server (no --build flag)
    print()
    print("Starting server at http://localhost:8000")
    print("Press Ctrl+C to stop")
    print()

    subprocess.run(
        ["uv", "run", "python", "-m", "pygbag", "."],
        cwd=PROJECT_ROOT
    )


def main():
    args = sys.argv[1:]

    if "--clean" in args:
        clean()
    elif "--serve" in args:
        serve()
    elif "--help" in args or "-h" in args:
        print(__doc__)
    else:
        build()


if __name__ == "__main__":
    main()
