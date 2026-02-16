import warnings
warnings.filterwarnings("ignore", message="Neither CUDA nor MPS are available")

from fastapi import FastAPI, File, UploadFile
import easyocr
import numpy as np
import cv2

app = FastAPI()
reader = easyocr.Reader(['en'])

@app.get("/")
def home():
    return {"message": "OCR API Running"}

@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    contents = await file.read()

    npimg = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    result = reader.readtext(img, detail=0)

    return {"ingredients": result}
