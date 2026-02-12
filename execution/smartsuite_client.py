"""
SmartSuite API client for the Document Intake process.

Handles creating records and uploading file attachments
to the SmartSuite Documents table.

SmartSuite API docs: https://developers.smartsuite.com/
"""

import os
import requests


class SmartSuiteClient:
    """Client for interacting with the SmartSuite API."""

    BASE_URL = "https://app.smartsuite.com/api/v1"

    def __init__(self):
        self.api_key = os.environ.get("SMARTSUITE_API_KEY", "")
        self.workspace_id = os.environ.get("SMARTSUITE_WORKSPACE_ID", "")
        self.table_id = os.environ.get("SMARTSUITE_TABLE_ID", "")

        # SmartSuite field IDs — must be configured per your workspace.
        # Find these via SmartSuite API: GET /applications/{table_id}/fields
        self.field_ids = {
            "product": os.environ.get("SS_FIELD_PRODUCT", ""),
            "type": os.environ.get("SS_FIELD_TYPE", ""),
            "supplier": os.environ.get("SS_FIELD_SUPPLIER", ""),
            "filename": os.environ.get("SS_FIELD_FILENAME", ""),
            "document": os.environ.get("SS_FIELD_DOCUMENT", ""),
        }

    def _headers(self):
        return {
            "Authorization": f"Token {self.api_key}",
            "Account-Id": self.workspace_id,
            "Content-Type": "application/json",
        }

    def _file_headers(self):
        return {
            "Authorization": f"Token {self.api_key}",
            "Account-Id": self.workspace_id,
        }

    def validate_config(self):
        """Check that all required configuration is present."""
        missing = []
        if not self.api_key:
            missing.append("SMARTSUITE_API_KEY")
        if not self.workspace_id:
            missing.append("SMARTSUITE_WORKSPACE_ID")
        if not self.table_id:
            missing.append("SMARTSUITE_TABLE_ID")
        for name, field_id in self.field_ids.items():
            if not field_id:
                missing.append(f"SS_FIELD_{name.upper()}")
        return missing

    def create_record(self, product, doc_type, supplier, filename):
        """
        Create a new record in the SmartSuite Documents table.

        Returns the record ID on success, or raises an exception on failure.
        """
        url = f"{self.BASE_URL}/applications/{self.table_id}/records/"

        payload = {
            "title": filename,
            self.field_ids["product"]: product,
            self.field_ids["type"]: doc_type,
            self.field_ids["supplier"]: supplier,
            self.field_ids["filename"]: filename,
        }

        response = requests.post(url, json=payload, headers=self._headers(), timeout=30)
        if not response.ok:
            detail = response.text[:500]
            raise requests.HTTPError(
                f"{response.status_code} for {url}: {detail}", response=response
            )

        data = response.json()
        return data.get("id")

    def upload_file(self, record_id, field_id, file_path, file_name):
        """
        Upload a file attachment to an existing SmartSuite record.

        SmartSuite file upload is a two-step process:
        1. Upload the file to get a file reference
        2. Update the record to attach the file reference
        """
        # Step 1: Upload file
        upload_url = f"{self.BASE_URL}/files/"
        with open(file_path, "rb") as f:
            files = {"file": (file_name, f, "application/pdf")}
            response = requests.post(
                upload_url,
                files=files,
                headers=self._file_headers(),
                timeout=120,
            )
        if not response.ok:
            detail = response.text[:500]
            raise requests.HTTPError(
                f"File upload {response.status_code}: {detail}", response=response
            )
        file_data = response.json()

        # Step 2: Attach file to record
        record_url = (
            f"{self.BASE_URL}/applications/{self.table_id}/records/{record_id}/"
        )
        payload = {
            field_id: [file_data],
        }
        response = requests.patch(
            record_url, json=payload, headers=self._headers(), timeout=30
        )
        if not response.ok:
            detail = response.text[:500]
            raise requests.HTTPError(
                f"File attach {response.status_code}: {detail}", response=response
            )

        return file_data

    def submit_document(self, product, doc_type, supplier, filename, file_path):
        """
        Full intake submission: create record, then attach the PDF.

        Returns dict with record_id and file info on success.
        Raises requests.HTTPError on API failure.
        """
        record_id = self.create_record(product, doc_type, supplier, filename)

        file_info = self.upload_file(
            record_id=record_id,
            field_id=self.field_ids["document"],
            file_path=file_path,
            file_name=filename if filename.lower().endswith(".pdf") else f"{filename}.pdf",
        )

        return {
            "record_id": record_id,
            "file_info": file_info,
        }
