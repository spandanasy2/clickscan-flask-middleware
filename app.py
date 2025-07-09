from flask import Flask, request, Response
import requests
import io
import time
import re
import json
from werkzeug.datastructures import FileStorage

app = Flask(__name__)

# 🧾 Regex extractors
def extract_field(pattern, text):
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else None

def extract_invoice_number(text):
    return extract_field(r'(?:Invoice|Inv|Bill)\s*(?:Number|No)[\s:]*([A-Z0-9\-\/]+)', text)

def extract_date(text):
    return extract_field(r'Date\s*[:\-]?\s*([0-9]{1,2}[\s/-]?[A-Za-z]{3,9}[\s/-]?[0-9]{2,4})', text)

def extract_time(text):
    return extract_field(r'Time\s*[:\-]?\s*([0-9]{1,2}:[0-9]{2}(?:\s*[APMapm]{2})?)', text)

def extract_currency(text):
    return extract_field(r'\b(INR|USD|EUR|₹|\$|Rs)\b', text)

def extract_total_amount(text):
    return extract_field(r'Total\s+Amount\s*[:\-]?\s*(?:INR|USD|₹|Rs)?\s*([0-9.,]+)', text) or \
           extract_field(r'TOTAL\s*[:\-]?\s*(?:INR|USD|₹|Rs)?\s*([0-9.,]+)', text)

def extract_merchant_name(text):
    match = re.search(r'(?:from|by)\s+([A-Z][A-Z\s&]+(?:LTD|PRIVATE LIMITED|PVT LTD|INC|CORP)?)', text, re.IGNORECASE)
    return match.group(1).strip() if match else None

@app.route('/')
def home():
    return '✅ ClickScan Flask Middleware is running (GETTEXT only)!'

@app.route('/ocr/gettext', methods=['POST'])
def ocr_gettext_parser():
    start = time.time()
    print("📥 OCR request received for /ocr/gettext")

    if not request.data:
        return Response('{"error": "No file content received"}', status=400, mimetype='application/json')

    file = FileStorage(
        stream=io.BytesIO(request.data),
        filename="uploaded.pdf",
        content_type="application/pdf"
    )

    files = {
        'file': (file.filename, file.stream, file.content_type)
    }

    try:
        # 🔗 Call ClickScan's /ocr/gettext/
        target_url = 'https://clickscanstg.terralogic.com/ocr/gettext/'
        response = requests.post(
            target_url,
            files=files,
            headers={'Accept': 'application/json'}
        )

        elapsed = time.time() - start
        print(f"✅ Forwarded to ClickScan in {elapsed:.2f} seconds")

        if response.status_code != 200:
            return Response(response.content, status=response.status_code, content_type='application/json')

        raw_text = response.text.strip().strip('"').replace('\\n', '\n')

        print(f"📄 Raw text length: {len(raw_text)}")

        # 🧠 Extract fields from raw text
        parsed = {
            "merchant_name": extract_merchant_name(raw_text),
            "invoice_date": extract_date(raw_text),
            "invoice_time": extract_time(raw_text),
            "total_amount": extract_total_amount(raw_text),
            "currency_code": extract_currency(raw_text),
            "description": raw_text[:500],  # First 500 characters as fallback description
            "invoice_number": extract_invoice_number(raw_text)
        }

        print(f"🧾 Parsed data: {parsed}")

        response_payload = {
            "document_type": "Invoice",
            "content": raw_text,
            "parsedData": parsed
        }

        return Response(json.dumps(response_payload), status=200, content_type='application/json')

    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Exception occurred: {e} after {elapsed:.2f} seconds")
        return Response(f'{{"error": "{str(e)}"}}', status=500, mimetype='application/json')

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
