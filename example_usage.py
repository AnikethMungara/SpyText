#!/usr/bin/env python3
"""
Example: Using SpyText in a Python script
Demonstrates how to integrate SpyText into your workflow.
"""

import subprocess
import sys


def check_document_safety(pdf_path: str) -> bool:
    """
    Check if a document is safe to process with LLMs.

    Args:
        pdf_path: Path to PDF document

    Returns:
        True if safe (exit code 0), False otherwise
    """
    result = subprocess.run(
        [sys.executable, "spytext.py", "scan", pdf_path],
        capture_output=True,
        text=True
    )

    # Exit code 0 = SAFE
    if result.returncode == 0:
        print(f"[SAFE] {pdf_path} is safe to process")
        return True
    elif result.returncode in [1, 2]:
        print(f"[WARN] {pdf_path} has LOW/MEDIUM risk - review recommended")
        print(result.stdout)
        return False
    elif result.returncode in [3, 4]:
        print(f"[RISK] {pdf_path} has HIGH/CRITICAL risk - DO NOT PROCESS")
        print(result.stdout)
        return False
    else:
        print(f"[ERROR] Error scanning {pdf_path}")
        print(result.stderr)
        return False


def main():
    """Example usage of SpyText in a workflow."""
    documents = [
        "examples/simple_text.pdf",
        "examples/white_on_white.pdf",
        "examples/microscopic.pdf",
    ]

    print("SpyText Document Safety Check")
    print("=" * 50)

    safe_docs = []
    unsafe_docs = []

    for doc in documents:
        print()
        if check_document_safety(doc):
            safe_docs.append(doc)
        else:
            unsafe_docs.append(doc)

    print()
    print("=" * 50)
    print(f"Results: {len(safe_docs)} safe, {len(unsafe_docs)} unsafe")

    if safe_docs:
        print("\nSafe to process:")
        for doc in safe_docs:
            print(f"  + {doc}")

    if unsafe_docs:
        print("\nRequires review:")
        for doc in unsafe_docs:
            print(f"  - {doc}")


if __name__ == "__main__":
    main()
