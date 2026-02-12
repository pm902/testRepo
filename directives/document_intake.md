# Directive: Document Intake Frontend

## Objective
Browser-based intake form that allows Lake International users to upload supplier PDF documents with metadata, and push them into SmartSuite (Documents table) for downstream processing.

## Context
This is Step 1 of the document conversion pipeline. Users receive supplier PDFs by email, rename them per company protocol, then submit them via this intake form. After submission, the data flows into Make.com scenarios for processing via Unstructured.io.

## Inputs
User provides via the web form:
1. **Product** (dropdown): Bevaloid / Calcium Propionate / Citric Acid / Citric Acid Anhydrous / Peptan
2. **Type** (dropdown): Allergen / COA / GMO / Prodn Flow / SDS / Other
3. **Supplier** (dropdown): Bakery / Ensign / Health Nutrition / XX / YY
4. **Filename** (text): The renamed filename per company protocol
5. **PDF Document** (file upload): The supplier PDF file

## Tools / Scripts
- `execution/app.py` — Flask web server, serves the form and handles submissions
- `execution/smartsuite_client.py` — SmartSuite API integration (create record, upload file)
- `execution/templates/intake.html` — The browser-based intake form

## Outputs
- A new record in SmartSuite "Documents" table containing all metadata fields + attached PDF
- Success/error feedback displayed to the user in the browser

## Configuration
Environment variables required in `.env`:
- `SMARTSUITE_API_KEY` — SmartSuite API key
- `SMARTSUITE_WORKSPACE_ID` — SmartSuite workspace ID
- `SMARTSUITE_TABLE_ID` — SmartSuite table ID for the Documents table
- `FLASK_SECRET_KEY` — Secret key for Flask session security

## Field Mapping (Form → SmartSuite)
The SmartSuite field IDs must be configured in `.env` or discovered via the SmartSuite API. The mapping is:
- Product → SmartSuite field (configured in smartsuite_client.py)
- Type → SmartSuite field
- Supplier → SmartSuite field
- Filename → SmartSuite field
- PDF Document → SmartSuite file attachment

## Edge Cases & Learnings
- Only PDF files are accepted. The form validates file type before submission.
- Maximum file size: 25MB (configurable).
- All fields are required — no submission without complete metadata.
- If SmartSuite API fails, the error is displayed to the user with a clear message.
- ACCURACY IS PARAMOUNT: no data is guessed or assumed. Every field must be explicitly provided by the user.

## Running
```bash
cd execution
pip install -r ../requirements.txt
python app.py
```
Then open http://localhost:5000 in browser.
