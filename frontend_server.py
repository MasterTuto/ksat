from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# Montar arquivos estáticos
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")


@app.get("/")
async def read_index():
    return FileResponse("frontend/templates/index.html")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=3000)
