from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from google.cloud import storage

from config import build_runtime_config
from utils import log_to_request_file

logger = logging.getLogger(__name__)


def upload_to_gcs(pdf_file: str, request_id: str, config: Optional[Dict[str, Any]] = None) -> str:
    """Upload report output to Google Cloud Storage and return public URL."""
    try:
        report_config = build_runtime_config(config)
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        bucket_name = os.getenv("GCS_REPORT_BUCKET", "generated-report-ai")
        make_public = os.getenv("GCS_MAKE_PUBLIC", "true").lower() == "true"

        storage_client = storage.Client(project=project_id or None)
        bucket = storage_client.bucket(bucket_name)

        language_folder = str(report_config.get("language", "english")).lower()
        blob_name = f"{language_folder}/{Path(pdf_file).name}"
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(pdf_file, content_type="application/pdf")
        if make_public:
            blob.make_public()

        public_url = blob.public_url
        message = f"Uploaded report to '{bucket_name}/{blob_name}'"
        logger.info(message)
        log_to_request_file(request_id, "uploading", message)
        return public_url
    except Exception as exc:
        message = f"Error uploading report to GCS: {exc}"
        logger.exception(message)
        log_to_request_file(request_id, "error", message)
        raise
