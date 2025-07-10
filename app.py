from flask import Flask, request, Response
import requests
import io
import time
import re
import json
from werkzeug.datastructures import FileStorage

app = Flask(__name__)

def extract_sow_fields(raw_text):
    def extract(pattern):
        match = re.search(pattern, raw_text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    return {
        "project_title": extract(r"Project Title:\s*(.+)"),
        "client": extract(r"Client:\s*(.+)"),
        "service_provider": extract(r"Service Provider:\s*(.+)"),
        "prepared_date": extract(r"Prepared Date:\s*(.+)"),
        "start_date": extract(r"Project Kickoff[:\s]*([A-Za-z0-9 ,]+)"),
        "end_date": extract(r"(Go[\s\-]?Live Date)[:\s]*([A-Za-z0-9 ,]+)"),
        "total_fee": extract(r"Total Project Fee[:\s₹]*([0-9,]+)")
    }

@app.route('/')
def home():
    return '✅ ClickScan Flask Middleware is running!'

@app.route('/ocr/<endpoint>', methods=['POST'])
def ocr_proxy(endpoint):
    start = time.time()
    print(f"📥 OCR request received for endpoint: {endpoint}")

    if not request.data:
        return Response('{"error": "No file content received"}', status=400, mimetype='application/json')

    # Detect content type
    content_type = request.headers.get('Content-Type', '').lower()
    if 'image/png' in content_type:
        file_type = 'image/png'
        filename = 'uploaded.png'
    elif 'image/jpeg' in content_type or 'image/jpg' in content_type:
        file_type = 'image/jpeg'
        filename = 'uploaded.jpg'
    else:
        file_type = 'application/pdf'
        filename = 'uploaded.pdf'

    file = FileStorage(
        stream=io.BytesIO(request.data),
        filename=filename,
        content_type=file_type
    )

    files = {
        'file': (file.filename, file.stream, file.content_type)
    }

    try:
        if endpoint == 'sow':
            # Forward to /ocr/gettext
            print("🔁 Forwarding to /ocr/gettext for SOW parsing...")
            response = requests.post(
                'https://clickscanstg.terralogic.com/ocr/gettext/',
                files=files,
                headers={'Accept': 'application/json'}
            )
            if response.status_code != 200:
                return Response(response.content, status=response.status_code, mimetype='application/json')

            # Parse the raw text
            raw_text = response.text.strip('"')
            sow_data = extract_sow_fields(raw_text)
            print("✅ Extracted SOW fields:", sow_data)
            return Response(json.dumps({"document_type": "SOW", "parsedData": sow_data, "content": raw_text}),
                            status=200, mimetype='application/json')

        else:
            # Forward to original endpoint
            target_url = f'https://clickscanstg.terralogic.com/ocr/{endpoint}/'
            response = requests.post(
                target_url,
                files=files,
                headers={'Accept': 'application/json'}
            )
            elapsed = time.time() - start
            print(f"✅ Forwarded to ClickScan in {elapsed:.2f} seconds")
            return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))

    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Exception occurred: {e} after {elapsed:.2f} seconds")
        return Response(f'{{"error": "{str(e)}"}}', status=500, mimetype='application/json')

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
