#!/usr/bin/env python3
"""
SpyText - Human-Aligned Document Perception System
Simple terminal interface for detecting invisible text in documents.
"""

import sys
import yaml
from pathlib import Path

from src.ingest import DocumentLoader
from src.extract import PDFExtractor
from src.extract.docx_extractor import DOCXExtractor
from src.detect import VisibilityAnalyzer, VisibilityStatus, RiskAggregator, RiskLevel
from src.sanitize import TextSanitizer, SanitizationStrategy


def load_config() -> dict:
    """Load configuration from settings.yaml."""
    config_path = Path(__file__).parent / "config" / "settings.yaml"
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}


def scan(file_path: str, verbose: bool = False) -> int:
    """
    Scan a document for invisible text and security risks.

    Args:
        file_path: Path to document to scan
        verbose: Show detailed output

    Returns:
        Exit code (0=safe, 1=low, 2=medium, 3=high, 4=critical)
    """
    config = load_config()

    try:
        # Load and extract
        print(f"Scanning: {file_path}")

        loader = DocumentLoader(config)
        doc_path = loader.load(file_path)

        # Select appropriate extractor based on file format
        file_format = loader.detect_format(doc_path)
        if file_format == 'pdf':
            extractor = PDFExtractor(config)
        elif file_format == 'docx':
            extractor = DOCXExtractor(config)
        else:
            raise ValueError(f"Unsupported format for extraction: {file_format}")

        spans = extractor.extract(doc_path)

        if verbose:
            print(f"  Extracted {len(spans)} text spans")

        # Analyze visibility
        analyzer = VisibilityAnalyzer(config)
        for span in spans:
            span.visibility_status = analyzer.analyze(span)
            span.contrast_ratio = analyzer.get_contrast_ratio(span)

        # Aggregate risk
        aggregator = RiskAggregator(config)
        risk_report = aggregator.analyze(spans)

        # Count visibility statuses
        visible_count = sum(1 for s in spans if s.visibility_status == VisibilityStatus.VISIBLE)
        suspicious_count = sum(1 for s in spans if s.visibility_status == VisibilityStatus.SUSPICIOUS)
        invisible_count = sum(1 for s in spans if s.visibility_status == VisibilityStatus.INVISIBLE)

        # Display results
        print(f"  Status: {visible_count} visible, {suspicious_count} suspicious, {invisible_count} invisible")
        print(f"  Risk: {risk_report.risk_level.value.upper()}")

        # Show warnings
        if risk_report.prompt_injection_detected:
            print(f"  WARNING: Prompt injection detected ({len(risk_report.prompt_injection_patterns)} patterns)")

        # Detailed output
        if verbose:
            print()
            for rec in risk_report.recommendations:
                print(f"  - {rec}")

            if risk_report.invisible_text_sample:
                print()
                print("  Invisible text samples:")
                for i, text in enumerate(risk_report.invisible_text_sample[:3], 1):
                    preview = text[:40] + "..." if len(text) > 40 else text
                    print(f"    [{i}] '{preview}'")

        # Return exit code based on risk level
        exit_codes = {
            RiskLevel.SAFE: 0,
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 4
        }

        return exit_codes.get(risk_report.risk_level, 0)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 5
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 5
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if verbose:
            import traceback
            traceback.print_exc()
        return 5


def clean(file_path: str, output_path: str = None, strategy: str = "strip", verbose: bool = False) -> int:
    """
    Clean a document by removing invisible text.

    Args:
        file_path: Path to document to clean
        output_path: Path to save cleaned text (default: stdout)
        strategy: Sanitization strategy (strip/flag/preserve)
        verbose: Show detailed output

    Returns:
        Exit code (0=success, 5=error)
    """
    config = load_config()

    try:
        print(f"Cleaning: {file_path}")

        # Load and extract
        loader = DocumentLoader(config)
        doc_path = loader.load(file_path)

        # Select appropriate extractor based on file format
        file_format = loader.detect_format(doc_path)
        if file_format == 'pdf':
            extractor = PDFExtractor(config)
        elif file_format == 'docx':
            extractor = DOCXExtractor(config)
        else:
            raise ValueError(f"Unsupported format for extraction: {file_format}")

        spans = extractor.extract(doc_path)

        if verbose:
            print(f"  Extracted {len(spans)} text spans")

        # Analyze visibility
        analyzer = VisibilityAnalyzer(config)
        for span in spans:
            span.visibility_status = analyzer.analyze(span)
            span.contrast_ratio = analyzer.get_contrast_ratio(span)

        # Aggregate risk
        aggregator = RiskAggregator(config)
        risk_report = aggregator.analyze(spans)

        # Sanitize
        sanitizer = TextSanitizer(config)
        sanitization_strategy = SanitizationStrategy(strategy)
        sanitize_report = sanitizer.sanitize(spans, sanitization_strategy, risk_report.risk_level)

        # Display results
        print(f"  Strategy: {sanitize_report.strategy_used.value}")
        print(f"  Original: {sanitize_report.original_span_count} spans")
        print(f"  Removed: {sanitize_report.removed_count} spans")
        if sanitize_report.flagged_count > 0:
            print(f"  Flagged: {sanitize_report.flagged_count} spans")

        # Show removed text samples
        if verbose and sanitize_report.removed_text_sample:
            print()
            print("  Removed text samples:")
            for i, text in enumerate(sanitize_report.removed_text_sample[:3], 1):
                preview = text[:40] + "..." if len(text) > 40 else text
                print(f"    [{i}] '{preview}'")

        # Output cleaned text
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(sanitize_report.safe_text)
            print(f"  Output: {output_path}")
        else:
            print()
            print("--- Cleaned Text ---")
            print(sanitize_report.safe_text)
            print("--- End ---")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 5
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 5
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if verbose:
            import traceback
            traceback.print_exc()
        return 5


def print_usage():
    """Display usage information."""
    print("""
SpyText v0.1.0 - Detect invisible text in documents

Supported formats: PDF, DOCX (Microsoft Word)

Usage:
  python spytext.py scan <document> [--verbose]
  python spytext.py clean <document> [--output FILE] [--strategy STRATEGY] [--verbose]
  python spytext.py --help
  python spytext.py --version

Commands:
  scan <document>     Scan document for invisible text and risks
  clean <document>    Remove invisible text and output cleaned version

Options:
  --verbose, -v       Show detailed output
  --output, -o FILE   Save cleaned text to file (clean command only)
  --strategy STRATEGY Sanitization strategy: strip/flag/preserve (default: strip)
  --help, -h          Show this help message
  --version           Show version

Examples:
  python spytext.py scan document.pdf
  python spytext.py scan document.docx --verbose
  python spytext.py clean document.pdf
  python spytext.py clean document.docx --output cleaned.txt
  python spytext.py clean document.pdf --strategy flag --verbose

Exit Codes (scan):
  0 = SAFE
  1 = LOW risk
  2 = MEDIUM risk
  3 = HIGH risk
  4 = CRITICAL risk
  5 = Error

Exit Codes (clean):
  0 = Success
  5 = Error
""")


def main():
    """Main CLI entry point."""
    args = sys.argv[1:]

    # Handle help and version
    if not args or "--help" in args or "-h" in args:
        print_usage()
        return 0

    if "--version" in args:
        print("SpyText v0.1.0")
        return 0

    # Parse command
    if args[0] == "scan":
        if len(args) < 2:
            print("Error: scan command requires a document path", file=sys.stderr)
            print("Usage: python spytext.py scan <document>", file=sys.stderr)
            return 5

        document_path = args[1]
        verbose = "--verbose" in args or "-v" in args

        return scan(document_path, verbose=verbose)

    elif args[0] == "clean":
        if len(args) < 2:
            print("Error: clean command requires a document path", file=sys.stderr)
            print("Usage: python spytext.py clean <document>", file=sys.stderr)
            return 5

        document_path = args[1]
        verbose = "--verbose" in args or "-v" in args

        # Parse --output flag
        output_path = None
        if "--output" in args or "-o" in args:
            idx = args.index("--output") if "--output" in args else args.index("-o")
            if idx + 1 < len(args):
                output_path = args[idx + 1]
            else:
                print("Error: --output requires a file path", file=sys.stderr)
                return 5

        # Parse --strategy flag
        strategy = "strip"
        if "--strategy" in args:
            idx = args.index("--strategy")
            if idx + 1 < len(args):
                strategy = args[idx + 1]
                if strategy not in ["strip", "flag", "preserve"]:
                    print(f"Error: Invalid strategy '{strategy}'. Use: strip/flag/preserve", file=sys.stderr)
                    return 5
            else:
                print("Error: --strategy requires a value (strip/flag/preserve)", file=sys.stderr)
                return 5

        return clean(document_path, output_path=output_path, strategy=strategy, verbose=verbose)

    else:
        print(f"Error: Unknown command '{args[0]}'", file=sys.stderr)
        print("Run 'python spytext.py --help' for usage information", file=sys.stderr)
        return 5


if __name__ == "__main__":
    sys.exit(main())
