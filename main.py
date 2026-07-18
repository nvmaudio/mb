import base64
import cv2
import numpy as np
import easyocr
import gc
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Khởi tạo Reader chỉ ĐÚNG MỘT LẦN khi start app
# Đặt quantize=True để nén model AI giúp giảm gần một nửa dung lượng RAM tiêu thụ
reader = easyocr.Reader(['en'], gpu=False, quantize=True) 

class OCRRequest(BaseModel):
    imgBase64: str

def preprocess(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)

    h, w = thresh.shape
    border_thickness = int(max(h, w) * 0.02)
    thresh[0:border_thickness, :] = 255
    thresh[h-border_thickness:h, :] = 255
    thresh[:, 0:border_thickness] = 255
    thresh[:, w-border_thickness:w] = 255

    inverted = cv2.bitwise_not(thresh)
    pts = np.argwhere(inverted > 0)
    
    if len(pts) > 0:
        y_min, x_min = pts.min(axis=0)
        y_max, x_max = pts.max(axis=0)
        cropped = thresh[y_min:y_max+1, x_min:x_max+1]
        final_img = cv2.copyMakeBorder(
            cropped, 15, 15, 15, 15, 
            cv2.BORDER_CONSTANT, 
            value=255
        )
    else:
        final_img = thresh

    img_resized = cv2.resize(
        final_img, 
        None, 
        fx=2, 
        fy=2, 
        interpolation=cv2.INTER_NEAREST
    )
    return img_resized

@app.post("/ocr")
async def ocr_api(data: OCRRequest):
    base64_string = data.imgBase64
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]
        
    try:
        img_bytes = base64.b64decode(base64_string)
        img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
    except Exception:
        return {"error": "Cấu trúc chuỗi Base64 không hợp lệ"}

    if img is None:
        return {"error": "Không thể decode được ảnh từ chuỗi Base64"}

    processed_img = preprocess(img)

    result = reader.readtext(
        processed_img, 
        detail=0, 
        allowlist='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    )

    text_combined = "".join(result).replace(" ", "").strip()

    # Ép buộc giải phóng bộ nhớ tạm ngay sau khi dùng xong
    del img, processed_img, result
    gc.collect()

    return {"text": text_combined}

@app.get("/")
def home():
    return {"status": "EasyOCR Server Ready"}