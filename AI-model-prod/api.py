# api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import time
import logging

from predict import Predictor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PhoBERT Sentiment API")

# ================= Request/Response models =================
class CommentRequest(BaseModel):
    uid: str
    created_at: str
    updated_at: str
    rating: int
    comment: str
    deleted: bool
    attachment_uid: str
    dish_uid: str
    order_uid: str
    owner_id: int
    weight: float
    issue: Optional[str] = None

class CommentResponse(BaseModel):
    uid: str
    created_at: str
    updated_at: str
    rating: int
    comment: str
    deleted: bool
    attachment_uid: str
    dish_uid: str
    order_uid: str
    owner_id: int
    weight: float
    issue: Optional[str]

# ================= Load model =================
logger.info("Loading model...")
predictor = Predictor("models/phobert_multitask_best.pth")
logger.info("Model loaded!")

# ================= API Endpoints =================

@app.get("/health")
def health():
    """Kiểm tra service"""
    return {"status": "ok"}

@app.post("/predict", response_model=CommentResponse)
def predict(comment: CommentRequest):
    """
    Dự đoán weight và issue cho 1 comment
    Input: Object comment với weight=0, issue=null
    Output: Object comment đã gán weight và issue
    """
    start = time.time()
    
    # Dự đoán weight và issue từ comment text
    result = predictor.predict_combined(comment.comment)
    
    # Tạo response từ request, chỉ thay đổi weight và issue
    response = comment.model_dump()
    response['weight'] = result['final_weight']
    response['issue'] = result['issue']
    
    logger.info(f"Predicted uid={comment.uid} in {time.time() - start:.3f}s")
    
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)