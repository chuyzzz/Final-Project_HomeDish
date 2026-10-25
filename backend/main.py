from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from agents.recognizer import recognize_data_url
from config import Budget, BudgetExceeded
from tools.nutrition import compute

app = FastAPI(title="HomeDish Vision Backend", version="1.0.0")

class RecognitionRequest(BaseModel):
    image_data_url: str = Field(min_length=32)
    hint: str = ""
    cuisine: str = ""

class CalculationRequest(BaseModel):
    ingredients: list[dict]
    servings: int = Field(default=1, ge=1, le=100)

@app.get("/health")
def health():
    return {"status": "ok", "service": "vision+nutrition", "model": "gpt_luna", "data_source": "bundled USDA table"}

@app.post("/calculate")
def calculate(request: CalculationRequest):
    try:
        return compute(request.ingredients, request.servings)
    except (KeyError, TypeError, ValueError) as error:
        raise HTTPException(status_code=422, detail=f"Invalid nutrition input: {error}") from error

@app.post("/recognize")
def recognize(request: RecognitionRequest):
    if not request.image_data_url.startswith("data:image/"):
        raise HTTPException(status_code=400, detail="image_data_url must be an image data URL")
    try:
        result = recognize_data_url(request.image_data_url, request.hint, request.cuisine, Budget())
        return result.model_dump()
    except BudgetExceeded as error:
        raise HTTPException(status_code=429, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Vision recognition failed: {error}") from error
