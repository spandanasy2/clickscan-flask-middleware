from flask import Flask, request, jsonify
import requests
import io
import time
from werkzeug.datastructures import FileStorage

app = Flask(__name__)

@app.route('/')
def home():
    return '✅ ClickScan Flask Middleware is running!'

@app.route('/ocr/invoice', methods=['POST'])
def ocr_invoice():
    start = time.time()
    print("📥 OCR Invoice request received")

    if not request.data:
        return jsonify({'error': 'No file content received'}), 400

    file = FileStorage(
        stream=io.BytesIO(request.data),
        filename="uploaded.pdf",
        content_type="application/pdf"
    )

    files = {
        'file': (file.filename, file.stream, file.content_type)
    }

    try:
        # 🔗 Call the ClickScan structured invoice API
        target_url = 'https://clickscanstg.terralogic.com/ocr/invoice/'
        response = requests.post(
            target_url,
            files=files,
            headers={'Accept': 'application/json'}
        )

        elapsed = time.time() - start
        print(f"✅ OCR Invoice processed in {elapsed:.2f} seconds")

        if response.status_code == 200:
            raw = response.json()

            # 🧠 Extract fields from response (with defaults if missing)
            structured_data = {
                'merchant_name': raw.get('merchant_name', ''),
                'invoice_date': raw.get('date', ''),
                'invoice_time': raw.get('time', ''),
                'total_amount': raw.get('total_amount', ''),
                'currency_code': raw.get('currency', ''),
                'description': raw.get('description', ''),
                'invoice_number': raw.get('invoice_number', '')
            }

            return jsonify({
                'document_type': 'Invoice',
                'parsedData': structured_data
            })
        else:
            return jsonify({
                'error': 'ClickScan OCR failed',
                'status_code': response.status_code,
                'detail': response.text
            }), response.status_code

    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Exception occurred: {e} after {elapsed:.2f} seconds")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)
