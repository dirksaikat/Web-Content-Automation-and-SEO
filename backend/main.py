# main.py
from fastapi import FastAPI
from routes import router  # our routes live here

app = FastAPI(title="Content Generator")

# Plug in all routes from routes.py
app.include_router(router, tags=["web"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
