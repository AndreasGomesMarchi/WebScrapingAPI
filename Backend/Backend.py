from fastapi import FastAPI, HTTPException
from WebScrapingAPI.EUA.UniversityMIT import scrape_mit

app = FastAPI(
    title="Student Exchange API",
    description="API com dados de universidades para intercâmbio estudantil.",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/universities/mit")
def get_mit():
    try:
        university = scrape_mit()
        return university
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))