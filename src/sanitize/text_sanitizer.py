"""
Text sanitization for safe LLM processing.

Phase 5: IMPLEMENTED - Removes or flags invisible/suspicious text.
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional

from src.models import TextSpan
from src.detect import VisibilityStatus, RiskLevel


class SanitizationStrategy(Enum):
    """
    Strategy for handling problematic text.

    Values:
        STRIP: Remove invisible/suspicious text entirely
        FLAG: Keep text but add warning markers
        PRESERVE: Keep all text with metadata only
    """
    STRIP = "strip"
    FLAG = "flag"
    PRESERVE = "preserve"


@dataclass
class SanitizationReport:
    """
    Report of sanitization actions taken.

    Attributes:
        original_span_count: Number of spans before sanitization
        sanitized_span_count: Number of spans after sanitization
        removed_count: Number of spans removed
        flagged_count: Number of spans flagged
        strategy_used: Sanitization strategy applied
        removed_text_sample: Sample of removed text (for audit)
        safe_text: Sanitized text ready for LLM processing
    """
    original_span_count: int
    sanitized_span_count: int
    removed_count: int
    flagged_count: int
    strategy_used: SanitizationStrategy
    removed_text_sample: List[str]
    safe_text: str


class TextSanitizer:
    """
    Sanitizes text by removing or flagging invisible/suspicious content.

    Phase 5: IMPLEMENTED - Multiple sanitization strategies.
    """

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize text sanitizer.

        Args:
            config: Configuration dict from settings.yaml
        """
        self.config = config or {}

        # Get sanitization config
        sanitize_config = self.config.get('sanitization', {})
        self.default_strategy = SanitizationStrategy(
            sanitize_config.get('default_strategy', 'strip')
        )
        self.remove_invisible = sanitize_config.get('remove_invisible', True)
        self.remove_suspicious = sanitize_config.get('remove_suspicious', False)
        self.flag_prefix = sanitize_config.get('flag_prefix', '[SUSPICIOUS] ')

    def sanitize(
        self,
        spans: List[TextSpan],
        strategy: Optional[SanitizationStrategy] = None,
        risk_level: Optional[RiskLevel] = None
    ) -> SanitizationReport:
        """
        Sanitize text spans based on visibility status.

        Args:
            spans: List of TextSpan objects with visibility analysis
            strategy: Sanitization strategy (uses default if None)
            risk_level: Document risk level (for adaptive sanitization)

        Returns:
            SanitizationReport with sanitized text and metadata
        """
        if strategy is None:
            # Adaptive strategy based on risk level
            if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                strategy = SanitizationStrategy.STRIP
            elif risk_level == RiskLevel.MEDIUM:
                strategy = SanitizationStrategy.FLAG
            else:
                strategy = self.default_strategy

        # Apply sanitization strategy
        if strategy == SanitizationStrategy.STRIP:
            return self._sanitize_strip(spans)
        elif strategy == SanitizationStrategy.FLAG:
            return self._sanitize_flag(spans)
        else:  # PRESERVE
            return self._sanitize_preserve(spans)

    def _sanitize_strip(self, spans: List[TextSpan]) -> SanitizationReport:
        """
        Remove invisible and optionally suspicious text.

        Args:
            spans: Text spans to sanitize

        Returns:
            SanitizationReport with removed text
        """
        safe_spans = []
        removed_spans = []

        for span in spans:
            # Remove invisible text
            if span.visibility_status == VisibilityStatus.INVISIBLE:
                removed_spans.append(span)
                continue

            # Optionally remove suspicious text
            if self.remove_suspicious and span.visibility_status == VisibilityStatus.SUSPICIOUS:
                removed_spans.append(span)
                continue

            # Keep visible and (optionally) suspicious text
            safe_spans.append(span)

        # Build sanitized text
        safe_text = self._reconstruct_text(safe_spans)

        # Get removed text samples
        removed_text_sample = [s.text for s in removed_spans[:10]]

        return SanitizationReport(
            original_span_count=len(spans),
            sanitized_span_count=len(safe_spans),
            removed_count=len(removed_spans),
            flagged_count=0,
            strategy_used=SanitizationStrategy.STRIP,
            removed_text_sample=removed_text_sample,
            safe_text=safe_text
        )

    def _sanitize_flag(self, spans: List[TextSpan]) -> SanitizationReport:
        """
        Keep all text but add warning flags to suspicious content.

        Args:
            spans: Text spans to sanitize

        Returns:
            SanitizationReport with flagged text
        """
        processed_spans = []
        flagged_count = 0
        removed_count = 0
        removed_text_sample = []

        for span in spans:
            # Remove invisible text (too risky to keep)
            if span.visibility_status == VisibilityStatus.INVISIBLE:
                removed_count += 1
                removed_text_sample.append(span.text)
                continue

            # Flag suspicious text
            if span.visibility_status == VisibilityStatus.SUSPICIOUS:
                flagged_count += 1
                # Create flagged version
                flagged_span = span
                processed_spans.append((flagged_span, True))
            else:
                processed_spans.append((span, False))

        # Build text with flags
        text_parts = []
        for span, is_flagged in processed_spans:
            if is_flagged:
                text_parts.append(f"{self.flag_prefix}{span.text}")
            else:
                text_parts.append(span.text)

        safe_text = " ".join(text_parts)

        return SanitizationReport(
            original_span_count=len(spans),
            sanitized_span_count=len(processed_spans),
            removed_count=removed_count,
            flagged_count=flagged_count,
            strategy_used=SanitizationStrategy.FLAG,
            removed_text_sample=removed_text_sample[:10],
            safe_text=safe_text
        )

    def _sanitize_preserve(self, spans: List[TextSpan]) -> SanitizationReport:
        """
        Keep all text unchanged (for audit/analysis only).

        Args:
            spans: Text spans to preserve

        Returns:
            SanitizationReport with all original text
        """
        safe_text = self._reconstruct_text(spans)

        return SanitizationReport(
            original_span_count=len(spans),
            sanitized_span_count=len(spans),
            removed_count=0,
            flagged_count=0,
            strategy_used=SanitizationStrategy.PRESERVE,
            removed_text_sample=[],
            safe_text=safe_text
        )

    def _reconstruct_text(self, spans: List[TextSpan]) -> str:
        """
        Reconstruct text from spans with spacing.

        Args:
            spans: Text spans to reconstruct

        Returns:
            Reconstructed text string
        """
        if not spans:
            return ""

        # Sort by page and position
        sorted_spans = sorted(spans, key=lambda s: (s.page_number, s.bbox[1], s.bbox[0]))

        # Join with spaces (simple approach)
        return " ".join(s.text for s in sorted_spans)

    def get_safe_text(
        self,
        spans: List[TextSpan],
        strategy: Optional[SanitizationStrategy] = None,
        risk_level: Optional[RiskLevel] = None
    ) -> str:
        """
        Convenience method to get sanitized text directly.

        Args:
            spans: Text spans to sanitize
            strategy: Sanitization strategy
            risk_level: Document risk level

        Returns:
            Sanitized text string
        """
        report = self.sanitize(spans, strategy, risk_level)
        return report.safe_text
