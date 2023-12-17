from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random

from .openapi import custom_openapi
from .api import register_api

app = FastAPI()

origins = ["http://localhost:3333"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_status() -> str:
    statuses = [
        "いや～お腹減ったなぁ",
        "そんなぁ",
        "ちなみにそれ、失礼ですよ",
        "ｳｰ",
        "うお～ChatGPT様～",
    ]
    return random.choice(statuses)

@app.get("/")
async def root():
    return {"currentStatus": get_status()}

register_api(app)
custom_openapi(app)
