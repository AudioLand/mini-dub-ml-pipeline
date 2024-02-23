import uvicorn
from fastapi import FastAPI

from controllers.generate import dub_router

app = FastAPI()

app.include_router(dub_router)


@app.get("/healthcheck")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    print("main started")
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
