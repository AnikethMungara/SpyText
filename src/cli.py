"""
Command-line interface for SpyText.

Phase 1: Basic CLI structure with no processing logic.
Phase 2: IMPLEMENTED - Document loading and text extraction.
Phase 3: IMPLEMENTED - Visibility detection and analysis.
Phase 4: IMPLEMENTED - Risk aggregation and security assessment.
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
from src.detect import VisibilityAnalyzer, VisibilityStatus, RiskAggregator, RiskLevel

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
    Phase 3: IMPLEMENTED - Visibility detection and analysis
    Phase 4: IMPLEMENTED - Risk aggregation and security assessment

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

        # Phase 3: Analyze visibility
        console.print("\n[cyan]Step 3:[/cyan] Analyzing visibility...")
        analyzer = VisibilityAnalyzer(config)

        for span in spans:
            span.visibility_status = analyzer.analyze(span)
            span.contrast_ratio = analyzer.get_contrast_ratio(span)

        console.print(f"[green]  [OK][/green] Analyzed visibility for all spans")

        # Phase 4: Risk aggregation
        console.print("\n[cyan]Step 4:[/cyan] Aggregating risk assessment...")
        aggregator = RiskAggregator(config)
        risk_report = aggregator.analyze(spans)
        console.print(f"[green]  [OK][/green] Risk analysis complete")

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

        # Phase 3: Visibility analysis results
        console.print()
        console.print("[bold cyan]Visibility Analysis:[/bold cyan]")

        if spans:
            # Count by visibility status
            visible_count = sum(1 for s in spans if s.visibility_status == VisibilityStatus.VISIBLE)
            suspicious_count = sum(1 for s in spans if s.visibility_status == VisibilityStatus.SUSPICIOUS)
            invisible_count = sum(1 for s in spans if s.visibility_status == VisibilityStatus.INVISIBLE)
            unknown_count = sum(1 for s in spans if s.visibility_status == VisibilityStatus.UNKNOWN)

            console.print(f"  [green]Visible:[/green] {visible_count} spans")
            console.print(f"  [yellow]Suspicious:[/yellow] {suspicious_count} spans")
            console.print(f"  [red]Invisible:[/red] {invisible_count} spans")
            if unknown_count > 0:
                console.print(f"  [dim]Unknown:[/dim] {unknown_count} spans")

            # Show suspicious and invisible spans
            if suspicious_count > 0 or invisible_count > 0:
                console.print()
                console.print("[bold yellow]Suspicious/Invisible Text Detected:[/bold yellow]")

                problem_spans = [s for s in spans if s.visibility_status in
                                [VisibilityStatus.SUSPICIOUS, VisibilityStatus.INVISIBLE]]

                for i, span in enumerate(problem_spans[:10], 1):
                    status_color = "red" if span.visibility_status == VisibilityStatus.INVISIBLE else "yellow"
                    console.print(f"  [{i}] [{status_color}]{span.visibility_status.value.upper()}[/{status_color}]: '{span.text[:50]}'")
                    console.print(f"      Page: {span.page_number}", end="")

                    if span.contrast_ratio:
                        console.print(f", Contrast: {span.contrast_ratio:.2f}:1", end="")
                    if span.font_size:
                        console.print(f", Size: {span.font_size:.1f}pt", end="")
                    if span.font_color and span.background_color:
                        console.print(f", Colors: {span.font_color} on {span.background_color}", end="")
                    console.print()

                if len(problem_spans) > 10:
                    console.print(f"  ... and {len(problem_spans) - 10} more")

        # Phase 4: Risk assessment
        console.print()
        risk_color = aggregator.get_risk_color(risk_report.risk_level)
        console.print(f"[bold {risk_color}]Risk Assessment: {risk_report.risk_level.value.upper()}[/bold {risk_color}]")

        # Show prompt injection warnings
        if risk_report.prompt_injection_detected:
            console.print()
            console.print("[bold red]WARNING: Prompt Injection Patterns Detected![/bold red]")
            console.print(f"  Found {len(risk_report.prompt_injection_patterns)} attack pattern(s):")
            for pattern in risk_report.prompt_injection_patterns[:5]:
                console.print(f"    • '{pattern}'")
            if len(risk_report.prompt_injection_patterns) > 5:
                console.print(f"    ... and {len(risk_report.prompt_injection_patterns) - 5} more")

        # Show invisible text samples
        if risk_report.invisible_text_sample:
            console.print()
            console.print("[bold yellow]Invisible Text Samples:[/bold yellow]")
            for i, text in enumerate(risk_report.invisible_text_sample, 1):
                preview = text[:60] + "..." if len(text) > 60 else text
                console.print(f"  [{i}] '{preview}'")

        # Show recommendations
        console.print()
        console.print("[bold cyan]Security Recommendations:[/bold cyan]")
        for rec in risk_report.recommendations:
            console.print(f"  • {rec}")

        # Phase 5+: Next steps
        console.print()
        console.print("[yellow]Next phases will add:[/yellow]")
        console.print("  • Text sanitization (Phase 5)")
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
