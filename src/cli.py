"""
Command-line interface for SpyText.

Phase 1: Basic CLI structure with no processing logic.
Phase 2: IMPLEMENTED - Document loading and text extraction.
Phase 3+: Will add visibility detection and risk analysis.
"""

import sys
import yaml
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.ingest import DocumentLoader
from src.extract import PDFExtractor

console = Console()


def print_banner():
    """Display SpyText banner."""
    banner = """
    [bold cyan]SpyText[/bold cyan] v0.1.0
    Human-Aligned Document Perception System

    Detects human-invisible text before LLM processing
    """
    console.print(Panel(banner, border_style="cyan"))


def print_usage():
    """Display usage information."""
    usage = Table(show_header=False, box=None)
    usage.add_column(style="yellow")
    usage.add_column()

    usage.add_row("Usage:", "python -m src.cli <document_path>")
    usage.add_row("", "")
    usage.add_row("Example:", "python -m src.cli examples/sample.pdf")
    usage.add_row("", "")
    usage.add_row("Options:", "--help          Show this message")
    usage.add_row("", "--version       Show version")

    console.print(usage)


def load_config() -> dict:
    """Load configuration from settings.yaml."""
    config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}


def analyze_document(file_path: str) -> int:
    """
    Analyze a document for human-invisible text.

    Phase 2: IMPLEMENTED - Document loading and text extraction
    Phase 3+: Will add visibility detection and risk analysis

    Args:
        file_path: Path to document to analyze

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    console.print(f"\n[bold]Analyzing:[/bold] {file_path}")

    # Load configuration
    config = load_config()

    try:
        # Phase 2: Load document
        console.print("\n[cyan]Step 1:[/cyan] Loading document...")
        loader = DocumentLoader(config)
        doc_path = loader.load(file_path)
        console.print(f"[green]  [OK][/green] Loaded {doc_path.suffix} file")

        # Phase 2: Extract text
        console.print("\n[cyan]Step 2:[/cyan] Extracting text...")
        extractor = PDFExtractor(config)
        spans = extractor.extract(doc_path)
        console.print(f"[green]  [OK][/green] Extracted {len(spans)} text spans")

        # Display extraction results
        console.print()
        console.print("[bold cyan]Extraction Results:[/bold cyan]")
        console.print(f"  Total text spans: {len(spans)}")

        if spans:
            total_chars = sum(len(span.text) for span in spans)
            console.print(f"  Total characters: {total_chars}")

            # Show metadata coverage
            with_font_size = sum(1 for s in spans if s.font_size is not None)
            with_colors = sum(1 for s in spans if s.font_color is not None)

            console.print(f"  Font size metadata: {with_font_size}/{len(spans)} spans")
            console.print(f"  Color metadata: {with_colors}/{len(spans)} spans")

            # Show sample spans
            console.print()
            console.print("[bold cyan]Sample Text Spans:[/bold cyan]")
            for i, span in enumerate(spans[:5]):
                console.print(f"  [{i+1}] '{span.text}' (page {span.page_number})")
                if span.font_size:
                    console.print(f"      Font: {span.font_size:.1f}pt", end="")
                if span.font_color:
                    console.print(f", Color: RGB{span.font_color}", end="")
                console.print()

        # Phase 3+: Next steps
        console.print()
        console.print("[yellow]Next phases will add:[/yellow]")
        console.print("  • Visibility detection (Phase 3)")
        console.print("  • Risk aggregation (Phase 4)")
        console.print("  • Safety decisions (Phase 6)")

        return 0

    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        return 1
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        return 1
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        import traceback
        console.print(traceback.format_exc())
        return 1


def main(args: Optional[list] = None):
    """
    Main CLI entry point.

    Args:
        args: Command-line arguments (defaults to sys.argv[1:])
    """
    if args is None:
        args = sys.argv[1:]

    print_banner()

    # Handle special flags
    if not args or "--help" in args or "-h" in args:
        print_usage()
        return 0

    if "--version" in args or "-v" in args:
        console.print("SpyText version 0.1.0")
        return 0

    # Get document path
    document_path = args[0]

    # Analyze document
    exit_code = analyze_document(document_path)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
