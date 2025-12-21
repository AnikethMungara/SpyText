"""
Risk aggregation for document-level analysis.

Phase 4: IMPLEMENTED - Aggregates span-level visibility into document risk.
"""

import re
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Set

from src.models import TextSpan
from src.detect.visibility_analyzer import VisibilityStatus


class RiskLevel(Enum):
    """
    Document-level risk classification.

    Values:
        SAFE: No suspicious or invisible text detected
        LOW: Minor suspicious text, likely legitimate
        MEDIUM: Significant suspicious text or minor invisible text
        HIGH: Significant invisible text or prompt injection patterns
        CRITICAL: Severe invisible text with prompt injection indicators
    """
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskReport:
    """
    Document-level risk assessment report.

    Attributes:
        risk_level: Overall risk classification
        total_spans: Total text spans in document
        visible_count: Number of visible spans
        suspicious_count: Number of suspicious spans
        invisible_count: Number of invisible spans
        unknown_count: Number of spans with unknown visibility
        prompt_injection_detected: Whether prompt injection patterns found
        prompt_injection_patterns: List of detected attack patterns
        recommendations: List of recommended actions
        invisible_text_sample: Sample of invisible text (for review)
    """
    risk_level: RiskLevel
    total_spans: int
    visible_count: int
    suspicious_count: int
    invisible_count: int
    unknown_count: int
    prompt_injection_detected: bool
    prompt_injection_patterns: List[str]
    recommendations: List[str]
    invisible_text_sample: List[str]


class RiskAggregator:
    """
    Aggregates span-level visibility into document-level risk assessment.

    Phase 4: IMPLEMENTED - Multi-factor risk scoring with prompt injection detection.
    """

    # Prompt injection attack patterns (case-insensitive)
    PROMPT_INJECTION_PATTERNS = [
        r'\bignore\s+(previous|prior|above|all)\s+(instructions?|prompts?|commands?)\b',
        r'\bdisregard\s+(previous|prior|above|all)\s+(instructions?|prompts?|commands?)\b',
        r'\bforget\s+(everything|all|previous|prior|above)\b',
        r'\bsystem\s*:\s*',
        r'\bassistant\s*:\s*',
        r'\buser\s*:\s*',
        r'\byou\s+are\s+now\b',
        r'\bpretend\s+(to\s+be|you\s+are)\b',
        r'\bact\s+as\s+(if|a|an)\b',
        r'\brole\s*:\s*',
        r'\bnew\s+(instructions?|prompts?|commands?)\b',
        r'\boverride\s+(previous|settings?|instructions?)\b',
    ]

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize risk aggregator.

        Args:
            config: Configuration dict from settings.yaml
        """
        self.config = config or {}

        # Get risk thresholds from config
        risk_config = self.config.get('risk', {})
        self.suspicious_threshold = risk_config.get('suspicious_span_threshold', 5)
        self.invisible_threshold = risk_config.get('invisible_span_threshold', 1)
        self.check_llm_keywords = risk_config.get('check_llm_keywords', True)
        self.check_hidden_instructions = risk_config.get('check_hidden_instructions', True)

        # Compile regex patterns
        self.injection_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.PROMPT_INJECTION_PATTERNS
        ]

    def analyze(self, spans: List[TextSpan]) -> RiskReport:
        """
        Analyze document-level risk from text spans.

        Args:
            spans: List of TextSpan objects with visibility analysis

        Returns:
            RiskReport with document-level assessment
        """
        # Count visibility statuses
        visible_count = sum(1 for s in spans if s.visibility_status == VisibilityStatus.VISIBLE)
        suspicious_count = sum(1 for s in spans if s.visibility_status == VisibilityStatus.SUSPICIOUS)
        invisible_count = sum(1 for s in spans if s.visibility_status == VisibilityStatus.INVISIBLE)
        unknown_count = sum(1 for s in spans if s.visibility_status == VisibilityStatus.UNKNOWN)

        # Check for prompt injection patterns
        prompt_injection_detected = False
        prompt_injection_patterns = []

        if self.check_hidden_instructions:
            # Check invisible and suspicious text for injection patterns
            problem_spans = [s for s in spans if s.visibility_status in
                           [VisibilityStatus.INVISIBLE, VisibilityStatus.SUSPICIOUS]]

            injection_results = self._detect_prompt_injection(problem_spans)
            prompt_injection_detected = injection_results['detected']
            prompt_injection_patterns = injection_results['patterns']

        # Calculate risk level
        risk_level = self._calculate_risk_level(
            invisible_count,
            suspicious_count,
            len(spans),
            prompt_injection_detected
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            risk_level,
            invisible_count,
            suspicious_count,
            prompt_injection_detected
        )

        # Get sample of invisible text
        invisible_spans = [s for s in spans if s.visibility_status == VisibilityStatus.INVISIBLE]
        invisible_text_sample = [s.text for s in invisible_spans[:5]]

        return RiskReport(
            risk_level=risk_level,
            total_spans=len(spans),
            visible_count=visible_count,
            suspicious_count=suspicious_count,
            invisible_count=invisible_count,
            unknown_count=unknown_count,
            prompt_injection_detected=prompt_injection_detected,
            prompt_injection_patterns=prompt_injection_patterns,
            recommendations=recommendations,
            invisible_text_sample=invisible_text_sample
        )

    def _calculate_risk_level(
        self,
        invisible_count: int,
        suspicious_count: int,
        total_count: int,
        prompt_injection: bool
    ) -> RiskLevel:
        """
        Calculate document-level risk classification.

        Args:
            invisible_count: Number of invisible spans
            suspicious_count: Number of suspicious spans
            total_count: Total spans
            prompt_injection: Whether prompt injection detected

        Returns:
            RiskLevel classification
        """
        # CRITICAL: Prompt injection + invisible text
        if prompt_injection and invisible_count > 0:
            return RiskLevel.CRITICAL

        # HIGH: Significant invisible text or prompt injection alone
        if invisible_count >= self.invisible_threshold * 3:
            return RiskLevel.HIGH
        if prompt_injection:
            return RiskLevel.HIGH

        # MEDIUM: Any invisible text or significant suspicious text
        if invisible_count >= self.invisible_threshold:
            return RiskLevel.MEDIUM
        if suspicious_count >= self.suspicious_threshold * 2:
            return RiskLevel.MEDIUM

        # LOW: Minor suspicious text
        if suspicious_count >= self.suspicious_threshold:
            return RiskLevel.LOW

        # SAFE: No problematic text
        return RiskLevel.SAFE

    def _detect_prompt_injection(self, spans: List[TextSpan]) -> dict:
        """
        Detect prompt injection patterns in text spans.

        Args:
            spans: Text spans to analyze (typically invisible/suspicious)

        Returns:
            Dict with 'detected' bool and 'patterns' list
        """
        detected_patterns = set()

        for span in spans:
            text = span.text.lower()

            # Check against each pattern
            for pattern in self.injection_patterns:
                if pattern.search(text):
                    # Extract the matched pattern for reporting
                    match = pattern.search(text)
                    detected_patterns.add(match.group(0))

        return {
            'detected': len(detected_patterns) > 0,
            'patterns': sorted(list(detected_patterns))
        }

    def _generate_recommendations(
        self,
        risk_level: RiskLevel,
        invisible_count: int,
        suspicious_count: int,
        prompt_injection: bool
    ) -> List[str]:
        """
        Generate security recommendations based on risk assessment.

        Args:
            risk_level: Calculated risk level
            invisible_count: Number of invisible spans
            suspicious_count: Number of suspicious spans
            prompt_injection: Whether prompt injection detected

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if risk_level == RiskLevel.CRITICAL:
            recommendations.append("DO NOT process this document with LLMs")
            recommendations.append("Prompt injection attack detected in invisible text")
            recommendations.append("Manual security review required")
            recommendations.append("Consider reporting as malicious document")

        elif risk_level == RiskLevel.HIGH:
            if prompt_injection:
                recommendations.append("Block LLM processing - prompt injection detected")
                recommendations.append("Review detected patterns before proceeding")
            else:
                recommendations.append("Block LLM processing - excessive invisible text")
                recommendations.append(f"Found {invisible_count} invisible text spans")

            recommendations.append("Manual review strongly recommended")

        elif risk_level == RiskLevel.MEDIUM:
            if invisible_count > 0:
                recommendations.append("Warn user about invisible text before LLM processing")
                recommendations.append(f"Strip {invisible_count} invisible spans from output")
            if suspicious_count > 0:
                recommendations.append(f"Review {suspicious_count} suspicious spans for legitimacy")
            recommendations.append("Consider manual verification")

        elif risk_level == RiskLevel.LOW:
            recommendations.append("Safe to process with caution")
            recommendations.append(f"Monitor {suspicious_count} suspicious spans")
            recommendations.append("Likely legitimate low-contrast text")

        else:  # SAFE
            recommendations.append("Safe to process with LLMs")
            recommendations.append("No suspicious content detected")

        return recommendations

    def get_risk_color(self, risk_level: RiskLevel) -> str:
        """
        Get color code for rich console output.

        Args:
            risk_level: Risk level to colorize

        Returns:
            Rich color name
        """
        color_map = {
            RiskLevel.SAFE: "green",
            RiskLevel.LOW: "blue",
            RiskLevel.MEDIUM: "yellow",
            RiskLevel.HIGH: "red",
            RiskLevel.CRITICAL: "red bold"
        }
        return color_map.get(risk_level, "white")
