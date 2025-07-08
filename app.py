from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return 'ClickScan Flask Middleware is running!'

@app.route('/ocr', methods=['POST'])
def ocr():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    files = {
        'file': (file.filename, file.read(), file.content_type)
    }

    try:
        response = requests.post(
            'https://clickscan.terralogic.com/ocr/gettext/',
            files=files,
            headers={'Accept': 'application/json'}
        )

        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'ClickScan OCR failed', 'detail': response.text}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
