from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

DEFAULT_SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "OFF"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "OFF"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "OFF"},
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "OFF"},
]

REPORT_CONFIG = {
    "primary_bank": "Kookmin Bank",
    "comparison_banks": ["Hana", "Woori", "Shinhan Bank"],
    "credit_card_product_type": "Premium Credit Cards",
    "language": "Korean",
    "demo_mode": True,
    "orientation": "landscape",
    "analysis_focus": [
        "Market Share and Growth",
        "Revenue and Profitability",
        "Customer Acquisition Cost",
        "Customer Lifetime Value",
        "Digital Transformation Impact",
        "Competitive Positioning",
    ],
    "performance_metrics": [
        "Card Issuance Volume",
        "Transaction Volume",
        "Revenue per Card",
        "Customer Retention Rate",
        "Digital Adoption Rate",
        "Market Share by Segment",
    ],
    "market_segments": [
        "High Net Worth Individuals",
        "Business Professionals",
        "Digital-First Customers",
        "Loyalty Program Members",
    ],
    "report_sections": [
        "Executive Summary",
        "Premium Credit Card Product Comparison",
        "Pricing and Fee Analysis",
        "Rewards and Benefits Comparison",
        "Digital Features and Mobile Banking",
        "Customer Service and Support",
        "Market Performance Metrics",
        "Recommendations and Next Steps",
    ],
    "strict_structure": False,
    "writing_style": {
        "tone": "Executive and Strategic",
        "formality_level": "High",
        "emphasis": ["Data-Driven Insights", "Strategic Implications", "ROI Impact"],
    },
    "model_id": "gemini-2.5-pro",
    "flash_model_id": "gemini-2.5-flash",
    "safety_settings": DEFAULT_SAFETY_SETTINGS,
}


def build_runtime_config(overrides: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return a defensive copy of default config with optional overrides applied."""
    merged = deepcopy(REPORT_CONFIG)
    if overrides:
        merged.update(dict(overrides))
    return merged
