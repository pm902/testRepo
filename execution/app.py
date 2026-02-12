"""
Flask web application for the Lake International Document Intake process.

Serves a browser-based form where users upload supplier PDF documents
with metadata, which are then pushed into SmartSuite.

Usage:
    python app.py
    Then open http://localhost:5000
"""

import os
import tempfile

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

from smartsuite_client import SmartSuiteClient

# Load environment variables from .env at project root
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25MB max upload

# Dropdown options — single source of truth
PRODUCTS = ["Bevaloid", "Calcium Propionate", "Citric Acid", "Citric Acid Anhydrous", "Peptan"]
DOC_TYPES = ["Allergen", "COA", "GMO", "Prodn Flow", "SDS", "Other"]
SUPPLIERS = ["Bakery", "Ensign", "Health Nutrition", "XX", "YY"]

client = SmartSuiteClient()


@app.route("/", methods=["GET"])
def intake_form():
    """Serve the document intake form."""
    return render_template(
        "intake.html",
        products=PRODUCTS,
        doc_types=DOC_TYPES,
        suppliers=SUPPLIERS,
    )


@app.route("/submit", methods=["POST"])
def submit():
    """Handle form submission: validate, save to SmartSuite."""
    # Collect form data
    product = request.form.get("product", "").strip()
    doc_type = request.form.get("doc_type", "").strip()
    supplier = request.form.get("supplier", "").strip()
    filename = request.form.get("filename", "").strip()
    pdf_file = request.files.get("pdf_document")

    # Validate all fields present
    errors = []
    if not product or product not in PRODUCTS:
        errors.append("Please select a valid Product.")
    if not doc_type or doc_type not in DOC_TYPES:
        errors.append("Please select a valid Document Type.")
    if not supplier or supplier not in SUPPLIERS:
        errors.append("Please select a valid Supplier.")
    if not filename:
        errors.append("Please enter a Filename.")
    if not pdf_file or pdf_file.filename == "":
        errors.append("Please attach a PDF document.")
    elif not pdf_file.filename.lower().endswith(".pdf"):
        errors.append("Only PDF files are accepted.")

    if errors:
        for error in errors:
            flash(error, "error")
        return redirect(url_for("intake_form"))

    # Check SmartSuite configuration
    missing_config = client.validate_config()
    if missing_config:
        flash(
            f"SmartSuite configuration incomplete. Missing: {', '.join(missing_config)}. "
            "Please check your .env file.",
            "error",
        )
        return redirect(url_for("intake_form"))

    # Save uploaded file to temp location, then submit
    tmp_dir = os.path.join(os.path.dirname(__file__), "..", ".tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=tmp_dir, suffix=".pdf", delete=False
        ) as tmp:
            pdf_file.save(tmp)
            tmp_path = tmp.name

        result = client.submit_document(
            product=product,
            doc_type=doc_type,
            supplier=supplier,
            filename=filename,
            file_path=tmp_path,
        )

        flash(
            f"Document submitted successfully. Record ID: {result['record_id']}",
            "success",
        )

    except Exception as e:
        flash(f"Submission failed: {str(e)}", "error")

    finally:
        # Clean up temp file
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    return redirect(url_for("intake_form"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
