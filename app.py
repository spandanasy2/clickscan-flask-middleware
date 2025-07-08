from flask import Flask, request, jsonify
import requests
import io
from werkzeug.datastructures import FileStorage

app = Flask(__name__)

@app.route('/')
def home():
    return '✅ ClickScan Flask Middleware is running!'

@app.route('/ocr', methods=['POST'])
def ocr():
    if not request.data:
        return jsonify({'error': 'No file content received'}), 400

    # Reconstruct a fake file from the raw binary stream
    file = FileStorage(
        stream=io.BytesIO(request.data),
        filename="uploaded.pdf",
        content_type="application/pdf"
    )

    # Prepare the multipart/form-data payload
    files = {
        'file': (file.filename, file.stream, file.content_type)
    }

    try:
        # Forward the file to ClickScan OCR API
        response = requests.post(
            'https://clickscan.terralogic.com/ocr/gettext/',
            files=files,
            headers={'Accept': 'application/json'}
        )

        # Return the OCR response
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({
                'error': 'ClickScan OCR failed',
                'detail': response.text
            }), response.status_code

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
