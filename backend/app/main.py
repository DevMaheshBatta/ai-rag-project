from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "working successfully 🚀"}

@app.get("/health")
def health():
    return {"status": "ok"}