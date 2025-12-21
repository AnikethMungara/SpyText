"""
Build script to create SpyText standalone executable.

Requirements:
    pip install pyinstaller

Usage:
    python build_exe.py
"""

import subprocess
import sys
from pathlib import Path


def build_executable():
    """Build standalone executable using PyInstaller."""
    print("Building SpyText executable...")
    print("=" * 60)

    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("ERROR: PyInstaller not installed")
        print("Install with: pip install pyinstaller")
        return 1

    # PyInstaller command
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--onefile",                    # Single executable file
        "--name", "spytext",            # Output name
        "--clean",                      # Clean cache
        "--noconfirm",                  # Overwrite without asking
        "--add-data", "config:config",  # Include config directory
        "spytext_exe.py"                # Main script
    ]

    print("\nRunning PyInstaller...")
    print(f"Command: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print()
        print("=" * 60)
        print("Build successful!")
        print()
        print("Executable location:")
        exe_path = Path("dist") / "spytext.exe"
        print(f"  {exe_path.absolute()}")
        print()
        print("Usage:")
        print(f"  {exe_path} --scan document.pdf")
        print()
        print("You can copy spytext.exe to any location and run it.")
        return 0
    else:
        print()
        print("=" * 60)
        print("Build failed!")
        print("Check the error messages above.")
        return 1


if __name__ == "__main__":
    sys.exit(build_executable())
