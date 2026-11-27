"""RTL CSS audit check - flags physical CSS properties on RTL pages."""

import re
from typing import Any, Dict, List


# Physical CSS properties that should use logical equivalents on RTL pages
PHYSICAL_PROPERTIES: List[str] = [
    "margin-left",
    "margin-right",
    "margin-top",
    "margin-bottom",
    "padding-left",
    "padding-right",
    "padding-top",
    "padding-bottom",
    "border-left",
    "border-right",
    "border-top",
    "border-bottom",
    "text-align",
    "float",
]


def _find_rtl_declaration(html: str) -> bool:
    """Check if HTML declares dir='rtl' or dir=\"rtl\"."""
    # Match dir="rtl" or dir='rtl' anywhere in HTML
    # Look for dir= attribute followed by rtl value
    return bool(re.search(r'\bdir\s*=\s*["\']rtl["\']', html, re.IGNORECASE))


def _find_physical_properties(html: str, dir_rtl: bool) -> List[Dict[str, Any]]:
    """Find physical CSS property declarations in style blocks or inline styles.

    Returns violations when dir_rtl is True.
    Returns informational warnings when dir_rtl is False.
    """
    violations: List[Dict[str, Any]] = []

    if not dir_rtl:
        # On LTR-only pages, return informational warnings
        return _find_informational_warnings(html)

    # Parse style blocks for physical properties
    style_blocks = re.findall(r'<style[^>]*>(.*?)</style>', html, re.DOTALL | re.IGNORECASE)

    for block in style_blocks:
        for physical in PHYSICAL_PROPERTIES:
            # Match property: value patterns within CSS
            matches = re.findall(
                rf'{re.escape(physical)}\s*:\s*[^;]*;?',
                block,
                re.IGNORECASE
            )
            for match in matches:
                # Extract the value portion
                value_match = re.search(
                    rf'{re.escape(physical)}\s*:\s*([^;]*)',
                    match,
                    re.IGNORECASE
                )
                value = value_match.group(1).strip() if value_match else "unknown"

                violations.append({
                    "property": physical,
                    "element": "style-block",
                    "value": value,
                    "severity": "violation",
                })

    # Also check inline style attributes
    inline_matches = re.findall(
        r'(\w[\w-]*)\s*=\s*["\']([^"\']*)["\']',
        html
    )
    for prop, value in inline_matches:
        if prop in PHYSICAL_PROPERTIES:
            violations.append({
                "property": prop,
                "element": "inline-style",
                "value": value,
                "severity": "violation",
            })

    return violations


def _find_informational_warnings(html: str) -> List[Dict[str, Any]]:
    """On LTR-only pages, return informational warnings about properties that would break if RTL is added."""
    warnings: List[Dict[str, Any]] = []

    for physical in PHYSICAL_PROPERTIES:
        # Simple check for property presence in style blocks or inline
        if re.search(rf'{re.escape(physical)}\s*:', html, re.IGNORECASE):
            warnings.append({
                "property": physical,
                "element": "style-block-or-inline",
                "value": "present",
                "severity": "informational",
            })

    return warnings


def audit_rtl_css(html: str, dir_rtl: bool = False, include_ltr_info: bool = True) -> Dict[str, Any]:
    """Audit CSS for physical properties on RTL pages.

    Returns a dict with:
    - violations: list of dicts with property, element, value, severity
    - score: integer score out of 24 (or 20 if no RTL declared)
    - max_score: maximum possible score
    - has_rtl: whether dir="rtl" is declared
    - section: "Internationalization"
    """
    has_rtl = _find_rtl_declaration(html)

    violations = _find_physical_properties(html, dir_rtl)

    # If LTR-only and include_ltr_info, add informational warnings
    if not dir_rtl and include_ltr_info:
        info_warnings = _find_informational_warnings(html)
        # Combine: informational warnings don't count against score but are reported
        for warning in info_warnings:
            violations.append({
                "property": warning["property"],
                "element": warning["element"],
                "value": warning["value"],
                "severity": "informational",
            })

    # Calculate score
    # Base score: 20 for core design + 4 for Internationalization section
    # Each violation (severity=violation) subtracts 1 point from max
    max_score = 24 if has_rtl else 20
    violation_count = sum(1 for v in violations if v["severity"] == "violation")
    score = max(0, max_score - violation_count)

    return {
        "violations": violations,
        "score": score,
        "max_score": max_score,
        "has_rtl": has_rtl,
        "section": "Internationalization",
    }
