from __future__ import annotations

import logging
import os
import platform
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import markdown
import pdfkit
from markdown.extensions.toc import TocExtension

from config import build_runtime_config
from utils import log_to_request_file

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = Path("reports")
TEMPLATES_DIR = Path("templates")
DEFAULT_WKHTMLTOPDF_PATH = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "report"


def configure_pdfkit() -> Optional[pdfkit.configuration]:
    """Configure pdfkit with platform-specific wkhtmltopdf binary if available."""
    if platform.system() != "Windows":
        return None

    wkhtmltopdf_path = os.environ.get("WKHTMLTOPDF_PATH", DEFAULT_WKHTMLTOPDF_PATH)
    if not os.path.exists(wkhtmltopdf_path):
        raise EnvironmentError(
            f"wkhtmltopdf not found at '{wkhtmltopdf_path}'. Set WKHTMLTOPDF_PATH."
        )
    return pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)


def validate_orientation(orientation: str) -> str:
    valid_orientations = {"landscape", "portrait"}
    normalized = orientation.lower()
    if normalized not in valid_orientations:
        raise ValueError(
            f"Invalid orientation: {orientation}. Must be one of: {', '.join(sorted(valid_orientations))}"
        )
    return normalized


def _build_markdown_document(title: str, sections_content: List[str], references: List[str]) -> str:
    parts = [f"# {title}", "", "[TOC]", ""]
    parts.extend(section for section in sections_content)
    if references:
        parts.extend(["", "## References", ""])
        parts.extend(references)
    return "\n\n".join(parts).strip() + "\n"


def _render_html_from_markdown(markdown_content: str) -> str:
    html_content = markdown.markdown(
        markdown_content,
        extensions=[
            "tables",
            "fenced_code",
            "md_in_html",
            TocExtension(
                marker="[TOC]",
                title="Table of Contents",
                anchorlink=False,
                baselevel=1,
                toc_depth=3,
            ),
        ],
    )
    return re.sub(r"<h2", '<div class="section-break"></div><h2', html_content)


def _load_html_template(orientation: str, request_id: str) -> str:
    template_name = "report_template_portrait.html" if orientation == "portrait" else "report_template.html"
    template_path = TEMPLATES_DIR / template_name
    try:
        return template_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        message = f"Template file '{template_path}' not found. Using fallback template."
        logger.warning(message)
        log_to_request_file(request_id, "warning", message)
        return (
            "<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Report</title>"
            "<style>body{font-family:Arial,sans-serif;line-height:1.6}"
            "table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:8px}"
            "th{background:#f2f2f2}</style></head><body>{{content}}</body></html>"
        )


def _apply_template(template: str, html_content: str) -> str:
    escaped_template = template.replace("{", "{{").replace("}", "}}")
    escaped_template = escaped_template.replace("{{content}}", "{content}")
    return escaped_template.format(content=html_content)


def save_report_files(
    title: str,
    sections_content: List[str],
    references: List[str],
    request_id: str,
    config: Optional[Dict[str, Any]] = None,
) -> str:
    """Save report as Markdown, HTML and PDF; return the PDF path (or HTML fallback)."""
    report_config = build_runtime_config(config)

    try:
        orientation = validate_orientation(report_config.get("orientation", "landscape"))
    except ValueError as exc:
        message = f"{exc}. Defaulting to landscape."
        logger.warning(message)
        log_to_request_file(request_id, "warning", message)
        orientation = "landscape"

    language = str(report_config.get("language", "english")).lower()
    output_dir = DEFAULT_OUTPUT_DIR / language
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug_title = _slugify(title)
    file_stem = f"{timestamp}_{request_id}_{slug_title}"
    markdown_file = output_dir / f"{file_stem}.md"
    html_file = output_dir / f"{file_stem}.html"
    pdf_file = output_dir / f"{file_stem}.pdf"

    markdown_content = _build_markdown_document(title, sections_content, references)
    html_content = _render_html_from_markdown(markdown_content)
    html_template = _load_html_template(orientation, request_id)
    html_document = _apply_template(html_template, html_content)

    markdown_file.write_text(markdown_content, encoding="utf-8")
    html_file.write_text(html_document, encoding="utf-8")
    log_to_request_file(request_id, "saving", f"Saved Markdown: {markdown_file}")
    log_to_request_file(request_id, "saving", f"Saved HTML: {html_file}")

    pdf_options = {
        "page-size": "A4",
        "orientation": orientation.capitalize(),
        "margin-top": "0.5in",
        "margin-right": "0.5in",
        "margin-bottom": "0.5in",
        "margin-left": "0.5in",
        "encoding": "UTF-8",
        "no-outline": None,
        "enable-local-file-access": None,
        "footer-right": "[page] / [topage]",
        "footer-font-size": "7",
    }

    try:
        pdf_configuration = configure_pdfkit()
        pdfkit.from_string(
            html_document,
            str(pdf_file),
            options=pdf_options,
            configuration=pdf_configuration,
        )
        log_to_request_file(request_id, "saving", f"Saved PDF: {pdf_file}")
        return str(pdf_file)
    except Exception as exc:
        message = f"PDF generation failed: {exc}. Falling back to HTML."
        logger.exception(message)
        log_to_request_file(request_id, "error", message)
        return str(html_file)
