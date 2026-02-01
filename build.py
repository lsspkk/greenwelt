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

# Paths
PROJECT_ROOT = Path(__file__).parent
STAGING_DIR = PROJECT_ROOT / "build" / "staging"
BUILD_DIR = PROJECT_ROOT / "build" / "web"
DOCS_DIR = PROJECT_ROOT / "docs"

# Files and folders to include in the WASM build
INCLUDE_FOLDERS = [
    "assets",
    "data",
    "esper",
    "screens",
    "shared",
]

INCLUDE_FILES = [
    "main.py",
    "requirements.txt",
]


def clean():
    """Remove build artifacts"""
    print("Cleaning build artifacts...")

    if (PROJECT_ROOT / "build").exists():
        shutil.rmtree(PROJECT_ROOT / "build")
        print(f"  Removed {PROJECT_ROOT / 'build'}")

    if DOCS_DIR.exists():
        shutil.rmtree(DOCS_DIR)
        print(f"  Removed {DOCS_DIR}")

    # Clean pycache in project (not .venv)
    for pycache in PROJECT_ROOT.rglob("__pycache__"):
        if ".venv" not in str(pycache):
            shutil.rmtree(pycache)
            print(f"  Removed {pycache}")

    print("Clean complete.")


def create_staging():
    """Create staging directory with only needed files"""
    print("Creating staging directory...")

    if STAGING_DIR.exists():
        shutil.rmtree(STAGING_DIR)

    STAGING_DIR.mkdir(parents=True)

    # Copy folders
    for folder in INCLUDE_FOLDERS:
        src = PROJECT_ROOT / folder
        dst = STAGING_DIR / folder
        if src.exists():
            shutil.copytree(src, dst)
            print(f"  Copied {folder}/")

    # Copy files
    for filename in INCLUDE_FILES:
        src = PROJECT_ROOT / filename
        dst = STAGING_DIR / filename
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  Copied {filename}")

    # Count files
    file_count = sum(1 for f in STAGING_DIR.rglob("*") if f.is_file())
    total_size = sum(f.stat().st_size for f in STAGING_DIR.rglob("*") if f.is_file())
    print(f"  Staging: {file_count} files, {total_size / 1024 / 1024:.1f} MB")

    return STAGING_DIR


def build():
    """Build the WASM game using pygbag"""
    print("Building WASM game...")

    # Create staging directory
    staging = create_staging()

    print(f"  Source: {staging}")

    # Run pygbag build on staging directory
    result = subprocess.run(
        ["uv", "run", "python", "-m", "pygbag", "--build", str(staging)],
        cwd=PROJECT_ROOT,
        capture_output=False
    )

    if result.returncode != 0:
        print("ERROR: pygbag build failed!")
        sys.exit(1)

    # pygbag outputs to staging/build/web
    pygbag_output = staging / "build" / "web"
    if not pygbag_output.exists():
        print(f"ERROR: Build output not found at {pygbag_output}")
        sys.exit(1)

    print(f"  Build output: {pygbag_output}")

    # Copy to docs folder
    print(f"Copying to {DOCS_DIR}...")

    if DOCS_DIR.exists():
        shutil.rmtree(DOCS_DIR)

    shutil.copytree(pygbag_output, DOCS_DIR)

    # Show package size
    apk_files = list(DOCS_DIR.glob("*.apk"))
    if apk_files:
        apk_size = apk_files[0].stat().st_size / 1024 / 1024
        print(f"  Package size: {apk_size:.1f} MB")

    # Count files
    files = list(DOCS_DIR.rglob("*"))
    file_count = len([f for f in files if f.is_file()])

    print(f"  Copied {file_count} files to {DOCS_DIR}")

    # Post-process: Add DOCTYPE and update HTML
    index_html = DOCS_DIR / "index.html"
    if index_html.exists():
        with open(index_html, 'r', encoding='utf-8') as f:
            content = f.read()

        # Add DOCTYPE if missing (fix for Quirks Mode warning)
        if not content.startswith('<!DOCTYPE html>'):
            modified = '<!DOCTYPE html>\n' + content
        else:
            modified = content

        # Replace "Ready to start !" with "Aloita kasvipeli!"
        modified = modified.replace(
            '"Ready to start !"',
            '"Aloita kasvipeli!"'
        )

        # Write the modified content
        with open(index_html, 'w', encoding='utf-8') as f:
            f.write(modified)

        if not content.startswith('<!DOCTYPE html>'):
            print("  Added DOCTYPE declaration for Standards Mode")
        print("  Updated loading screen text to Finnish")

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

    # Create staging directory
    staging = create_staging()

    print(f"  Source: {staging}")
    print()
    print("Starting server at http://localhost:8000")
    print("Press Ctrl+C to stop")
    print()

    subprocess.run(
        ["uv", "run", "python", "-m", "pygbag", str(staging)],
        cwd=PROJECT_ROOT
    )


def main():
    args = sys.argv[1:]

    if "--clean" in args:
        clean()
    elif "--serve" in args:
        serve()
    elif "--push" in args:
        build()
        # Find the package(s) in docs/
        import subprocess
        from pathlib import Path
        docs_dir = DOCS_DIR
        # Add all files in docs/ to git
        subprocess.run(["git", "add", str(docs_dir)], check=True)
        # Commit
        subprocess.run(["git", "commit", "-m", "Updated WASM package"], check=True)
        # Push
        subprocess.run(["git", "push"], check=True)
    elif "--help" in args or "-h" in args:
        print(__doc__)
    else:
        build()


if __name__ == "__main__":
    main()
