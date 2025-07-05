from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "✅ AQI Backend is alive!"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting app...")
    uvicorn.run("main:app", host="0.0.0.0", port=10000)

