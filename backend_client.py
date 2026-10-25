import json
from urllib import request

VISION_BACKEND = "http://127.0.0.1:8000"

def recognize_with_backend(image_path, hint="", cuisine=""):
    from llm import image_data_url
    payload = json.dumps({"image_data_url": image_data_url(image_path), "hint": hint, "cuisine": cuisine}).encode()
    req = request.Request(VISION_BACKEND + "/recognize", data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with request.urlopen(req, timeout=90) as response:
        return json.loads(response.read().decode())

def calculate_with_backend(ingredients, servings=1):
    payload = json.dumps({"ingredients": ingredients, "servings": servings}).encode()
    req = request.Request(VISION_BACKEND + "/calculate", data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode())
