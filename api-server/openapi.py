import tomllib

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

version = None


def load_version():
    global version
    if version is None:
        with open("pyproject.toml", "rb") as f:
            version = tomllib.load(f)["tool"]["poetry"]["version"]
    return version


def custom_openapi(app: FastAPI) -> None:
    openapi_schema = get_openapi(
        title="raspi0125-api-server",
        version=load_version(),
        description="raspi0125のWebHookを記録するAPIサーバ",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
