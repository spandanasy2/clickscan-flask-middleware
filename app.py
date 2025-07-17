from flask import Flask, request, Response
import requests
import io
import time
import logging
import re
from werkzeug.datastructures import FileStorage
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("clickscan-middleware")


@app.route('/')
def home():
    return 'ClickScan Flask Middleware is running!'

# Health check endpoint
@app.route('/healthz')
def health():
    return Response('{"status": "ok"}', status=200, mimetype='application/json')


@app.route('/ocr/<endpoint>', methods=['POST'])
def ocr_proxy(endpoint):
    start = time.time()
    logger.info(f"OCR request received for endpoint: {endpoint}")

    # Endpoint validation: only allow alphanumeric, dash, underscore
    if not re.match(r'^[\w\-]+$', endpoint):
        logger.warning(f"Invalid endpoint: {endpoint}")
        return Response('{"error": "Invalid endpoint name."}', status=400, mimetype='application/json')

    # File size limit (e.g., 10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    if request.content_length and request.content_length > MAX_FILE_SIZE:
        logger.warning(f"File too large: {request.content_length} bytes")
        return Response('{"error": "File too large. Max 10MB allowed."}', status=413, mimetype='application/json')

    # Accept both raw data and multipart/form-data
    if request.files and 'file' in request.files:
        file = request.files['file']
        file_type = file.content_type
        filename = file.filename
    elif request.data:
        # Detect file type
        content_type = request.headers.get('Content-Type', '').lower()
        if 'image/png' in content_type:
            file_type = 'image/png'
            filename = 'uploaded.png'
        elif 'image/jpeg' in content_type or 'image/jpg' in content_type:
            file_type = 'image/jpeg'
            filename = 'uploaded.jpg'
        elif 'application/pdf' in content_type:
            file_type = 'application/pdf'
            filename = 'uploaded.pdf'
        else:
            logger.warning(f"Unsupported file type: {content_type}")
            return Response('{"error": "Unsupported file type. Only PNG, JPEG, and PDF are allowed."}', status=415, mimetype='application/json')

        file = FileStorage(
            stream=io.BytesIO(request.data),
            filename=filename,
            content_type=file_type
        )
    else:
        logger.warning("No file content received")
        return Response('{"error": "No file content received"}', status=400, mimetype='application/json')

    files = {
        'file': (file.filename, file.stream, file.content_type)
    }

    try:
        #Forward to the actual ClickScan endpoint directly
        target_url = f'https://clickscanstg.terralogic.com/ocr/{endpoint}/'
        response = requests.post(
            target_url,
            files=files,
            headers={'Accept': 'application/json'}
        )

        elapsed = time.time() - start
        logger.info(f"Forwarded to ClickScan /{endpoint}/ in {elapsed:.2f} seconds")

        return Response(response.content, status=response.status_code,
                        content_type=response.headers.get('Content-Type', 'application/json'))

    except Exception as e:
        elapsed = time.time() - start
        logger.error(f"Exception occurred: {e} after {elapsed:.2f} seconds")
        return Response(f'{{"error": "{str(e)}"}}', status=500, mimetype='application/json')

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
