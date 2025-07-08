from flask import Flask, request, jsonify
import requests
import io
import time
from werkzeug.datastructures import FileStorage

app = Flask(__name__)

@app.route('/')
def home():
    return '✅ ClickScan Flask Middleware is running!'

@app.route('/ocr/<endpoint>', methods=['POST'])
def ocr_proxy(endpoint):
    start = time.time()
    print(f"📥 OCR request received for endpoint: {endpoint}")

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
        # Construct full ClickScan API URL
        target_url = f'https://clickscan.terralogic.com/ocr/{endpoint}/'

        response = requests.post(
            target_url,
            files=files,
            headers={'Accept': 'application/json'}
        )

        elapsed = time.time() - start
        print(f"✅ Forwarded to ClickScan in {elapsed:.2f} seconds")

        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({
                'error': f'ClickScan OCR failed for endpoint {endpoint}',
                'detail': response.text
            }), response.status_code

    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Exception: {str(e)} after {elapsed:.2f} seconds")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
