from flask import Flask, request, Response
import requests
import io
import time
import re
import json
from werkzeug.datastructures import FileStorage

app = Flask(__name__)

def extract_invoice_number(text):
    match = re.search(r'(Invoice|Inv|Bill) (Number|No)[:\s\-]*([A-Z0-9\-\/]+)', text, re.IGNORECASE)
    return match.group(3) if match else None

@app.route('/')
def home():
    return '✅ ClickScan Flask Middleware is running!'

@app.route('/ocr/<endpoint>', methods=['POST'])
def ocr_proxy(endpoint):
    start = time.time()
    print(f"\U0001F4E5 OCR request received for endpoint: {endpoint}")

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
        # Step 1: Call /ocr/invoice/
        target_url = f'https://clickscanstg.terralogic.com/ocr/{endpoint}/'
        response = requests.post(
            target_url,
            files=files,
            headers={'Accept': 'application/json'}
        )

        elapsed = time.time() - start
        print(f"✅ Forwarded to ClickScan in {elapsed:.2f} seconds")

        if response.status_code != 200:
            return Response(response.content, status=response.status_code, content_type='application/json')

        result = response.json()

        # Step 2: Fallback to /gettext/ if 'content' is missing
        if not result.get("content"):
            print("🔁 Fetching content from /ocr/gettext/ as fallback")
            response_text = requests.post(
                'https://clickscanstg.terralogic.com/ocr/gettext/',
                files=files,
                headers={'Accept': 'application/json'}
            )
            if response_text.status_code == 200:
                result["content"] = response_text.json().get("content", "")
            else:
                print("⚠️ Failed to fetch fallback content")

        raw_text = result.get("content", "")
        parsed_data = result.get("parsedData", {})

        if raw_text:
            invoice_number = extract_invoice_number(raw_text)
            if invoice_number:
                parsed_data["invoice_number"] = invoice_number
                print(f"🧾 Extracted Invoice Number: {invoice_number}")
            else:
                print("❌ No invoice number found in raw OCR content.")
        else:
            print("⚠️ Still no 'content' found in OCR response.")

        result["parsedData"] = parsed_data
        return Response(json.dumps(result), status=200, content_type='application/json')

    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Exception occurred: {e} after {elapsed:.2f} seconds")
        return Response(f'{{"error": "{str(e)}"}}', status=500, mimetype='application/json')

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
