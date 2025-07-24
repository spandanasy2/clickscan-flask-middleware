from flask import Flask, request, Response
import requests
import io
import time
from werkzeug.datastructures import FileStorage

app = Flask(__name__)

@app.route('/')
def home():
    return 'ClickScan Flask Middleware is running!'

@app.route('/ocr/<endpoint>', methods=['POST'])
def ocr_proxy(endpoint):
    start = time.time()
    print(f"OCR request received for endpoint: {endpoint}")

    if not request.data:
        return Response('{"error": "No file content received"}', status=400, mimetype='application/json')

    # Detect content type from headers
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

    # Wrap the incoming binary into a FileStorage object
    file = FileStorage(
        stream=io.BytesIO(request.data),
        filename=filename,
        content_type=file_type
    )

    files = {
        'file': (file.filename, file.stream, file.content_type)
    }

    try:
        # Construct full ClickScan API URL
        target_url = f'https://clickscanstg.terralogic.com/ocr/{endpoint}/'
        response = requests.post(
            target_url,
            files=files,
            headers={'Accept': 'application/json'}
        )

        elapsed = time.time() - start
        print(f"Forwarded to ClickScan in {elapsed:.2f} seconds")

        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))

    except Exception as e:
        elapsed = time.time() - start
        print(f"Exception occurred: {e} after {elapsed:.2f} seconds")
        return Response(f'{{"error": "{str(e)}"}}', status=500, mimetype='application/json')

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
