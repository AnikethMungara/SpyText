#!/usr/bin/env python3
"""
SpyText Executable Entry Point
Simplified interface for standalone executable.
"""

import sys
import yaml
from pathlib import Path

from src.ingest import DocumentLoader
from src.extract import PDFExtractor
from src.extract.docx_extractor import DOCXExtractor
from src.detect import VisibilityAnalyzer, VisibilityStatus, RiskAggregator, RiskLevel


def load_config() -> dict:
    """Load configuration from settings.yaml."""
    config_path = Path(__file__).parent / "config" / "settings.yaml"
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}


def scan_document(file_path: str) -> int:
    """
    Scan document and return simplified exit code.

    Exit codes:
        1 = SAFE (no issues)
        2 = SUSPICIOUS (with location details)
        3 = SUSPICIOUS (unable to locate source)
    """
    config = load_config()

    try:
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

        # Analyze visibility
        analyzer = VisibilityAnalyzer(config)
        for span in spans:
            span.visibility_status = analyzer.analyze(span)
            span.contrast_ratio = analyzer.get_contrast_ratio(span)

        # Aggregate risk
        aggregator = RiskAggregator(config)
        risk_report = aggregator.analyze(spans)

        # Count hidden text (invisible or suspicious = hidden)
        hidden_spans = [s for s in spans if s.visibility_status in
                       [VisibilityStatus.SUSPICIOUS, VisibilityStatus.INVISIBLE]]

        hidden_count = len(hidden_spans)

        # SAFE: No hidden text detected
        if hidden_count == 0 and not risk_report.prompt_injection_detected:
            print("SAFE")
            print(f"Document: {file_path}")
            print("Status: No hidden text detected")
            print(f"Total spans analyzed: {len(spans)}")
            return 1

        # SUSPICIOUS: Hidden text found with locations
        problem_spans = hidden_spans

        if problem_spans:
            print("SUSPICIOUS")
            print(f"Document: {file_path}")
            print(f"Reason: Hidden text detected")

            # Calculate risk score (0-100)
            invisible_count = sum(1 for s in problem_spans if s.visibility_status == VisibilityStatus.INVISIBLE)
            suspicious_count = sum(1 for s in problem_spans if s.visibility_status == VisibilityStatus.SUSPICIOUS)

            risk_score = calculate_risk_score(
                invisible_count,
                suspicious_count,
                len(spans),
                risk_report.prompt_injection_detected
            )
            print(f"Risk Score: {risk_score}/100")
            print(f"Hidden spans: {hidden_count} out of {len(spans)} total")

            # Show locations by page
            print("\nHidden text locations:")

            # Group by page
            pages_with_issues = {}
            for span in problem_spans:
                page = span.page_number
                if page not in pages_with_issues:
                    pages_with_issues[page] = []
                pages_with_issues[page].append(span)

            # Display all pages with issues (up to 10)
            for page_num in sorted(pages_with_issues.keys())[:10]:
                page_spans = pages_with_issues[page_num]
                count = len(page_spans)

                # Determine severity
                has_invisible = any(s.visibility_status == VisibilityStatus.INVISIBLE for s in page_spans)
                severity = "INVISIBLE" if has_invisible else "LOW CONTRAST"

                print(f"  Page {page_num}: {count} hidden span(s) [{severity}]")

                # Show first example
                example = page_spans[0]
                preview = example.text[:50] + "..." if len(example.text) > 50 else example.text
                print(f"    Text: '{preview}'")

                # Show why it's hidden
                reasons = []
                if example.contrast_ratio and example.contrast_ratio < 1.5:
                    reasons.append(f"nearly invisible (contrast: {example.contrast_ratio:.2f}:1)")
                elif example.contrast_ratio and example.contrast_ratio < 3.0:
                    reasons.append(f"low contrast ({example.contrast_ratio:.2f}:1)")

                if example.font_size and example.font_size < 1.0:
                    reasons.append(f"microscopic ({example.font_size:.1f}pt)")
                elif example.font_size and example.font_size < 4.0:
                    reasons.append(f"very small ({example.font_size:.1f}pt)")

                if reasons:
                    print(f"    Why: {', '.join(reasons)}")

            if len(pages_with_issues) > 10:
                print(f"  ... and {len(pages_with_issues) - 10} more pages")

            # Prompt injection warning
            if risk_report.prompt_injection_detected:
                print("\n[!] WARNING: Possible attack patterns detected!")
                print(f"    Found {len(risk_report.prompt_injection_patterns)} suspicious pattern(s)")
                for pattern in risk_report.prompt_injection_patterns[:3]:
                    print(f"    - '{pattern}'")

            return 2

        # SUSPICIOUS: Unknown location (edge case)
        print("SUSPICIOUS")
        print(f"Document: {file_path}")
        print(f"Reason: Unable to locate hidden content")

        risk_score = calculate_risk_score(0, 0, len(spans), risk_report.prompt_injection_detected)
        print(f"Risk Score: {risk_score}/100")
        print("\nRecommendation: Manual review required")

        return 3

    except FileNotFoundError:
        print(f"ERROR: File not found: {file_path}", file=sys.stderr)
        return 3
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 3


def calculate_risk_score(invisible: int, suspicious: int, total: int, injection: bool) -> int:
    """
    Calculate risk score from 0-100.

    Factors:
        - Invisible text: 50 points base + 5 per span
        - Suspicious text: 20 points base + 2 per span
        - Prompt injection: 40 points
        - Percentage of problematic spans
    """
    score = 0

    # Invisible text is high risk
    if invisible > 0:
        score += 50
        score += min(invisible * 5, 30)  # Cap at 80 from invisible

    # Suspicious text is moderate risk
    if suspicious > 0:
        score += 20
        score += min(suspicious * 2, 20)  # Cap at 40 from suspicious

    # Prompt injection is critical
    if injection:
        score += 40

    # Percentage factor
    if total > 0:
        problematic_ratio = (invisible + suspicious) / total
        score += int(problematic_ratio * 20)

    return min(score, 100)  # Cap at 100


def main():
    """Main entry point for executable."""
    args = sys.argv[1:]

    # Simple usage: spytext --scan <file>
    if len(args) >= 2 and args[0] == "--scan":
        file_path = args[1]
        exit_code = scan_document(file_path)
        sys.exit(exit_code)

    # Show usage
    print("SpyText - Document Security Scanner")
    print()
    print("Supported formats: PDF, DOCX (Microsoft Word)")
    print()
    print("Usage:")
    print("  spytext --scan <file_path>")
    print()
    print("Exit Codes:")
    print("  1 = SAFE (no issues detected)")
    print("  2 = SUSPICIOUS (issues found with locations)")
    print("  3 = SUSPICIOUS (unable to locate or error)")
    print()
    print("Examples:")
    print("  spytext --scan ./documents/report.pdf")
    print("  spytext --scan ./documents/document.docx")

    sys.exit(0)


if __name__ == "__main__":
    main()
