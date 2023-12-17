from fastapi import APIRouter, FastAPI

router = APIRouter()


@router.get("/")
async def root():
    return {"message": "Hello World"}

@router.get("/health/")
async def health():
    return {"health": "ok"}

def register_api(app: FastAPI) -> None:
    global router
    app.include_router(router, prefix="/api")
