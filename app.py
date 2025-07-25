from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import requests
import time
from requests_toolbelt.multipart.encoder import MultipartEncoder

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "ClickScan FastAPI Middleware is running!"}

@app.post("/ocr/{endpoint}")
async def ocr_proxy(endpoint: str, request: Request):
    start = time.time()
    print(f"OCR request received for endpoint: {endpoint}")

    body = await request.body()
    if not body:
        return JSONResponse(content={"error": "No file content received"}, status_code=400)

    # Detect content type
    content_type = request.headers.get("content-type", "").lower()
    if "image/png" in content_type:
        file_type = "image/png"
        filename = "uploaded.png"
    elif "image/jpeg" in content_type or "image/jpg" in content_type:
        file_type = "image/jpeg"
        filename = "uploaded.jpg"
    else:
        file_type = "application/pdf"
        filename = "uploaded.pdf"

    try:
        multipart_data = MultipartEncoder(
            fields={"file": (filename, body, file_type)}
        )

        target_url = f"https://clickscanstg.terralogic.com/ocr/{endpoint}/"
        response = requests.post(
            target_url,
            data=multipart_data,
            headers={
                "Content-Type": multipart_data.content_type,
                "Accept": "application/json"
            }
        )

        elapsed = time.time() - start
        print(f"✅ Forwarded to ClickScan in {elapsed:.2f} seconds")

        return Response(content=response.content, status_code=response.status_code, media_type=response.headers.get("Content-Type"))

    except Exception as e:
        elapsed = time.time() - start
        print(f"Exception occurred: {e} after {elapsed:.2f} seconds")
        return JSONResponse(content={"error": str(e)}, status_code=500)