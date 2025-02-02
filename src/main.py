from fastapi import FastAPI
from uvicorn import run

from src.API.routes import router

app = FastAPI()
app.include_router(router)
if __name__ == "__main__":
    run("main:app", host="localhost", port=8000, reload=True)