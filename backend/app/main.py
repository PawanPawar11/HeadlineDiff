from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import URLTrackRequest, URLTrackResponse, TopicSearchRequest, TopicSearchResponse
from app import scraper
from app import analyzer
from typing import Dict, List, Any

app = FastAPI(title="HeadlineDiff API", description="Backend API for tracking historical news headline edits and topic narrative shifts.")

# Configure CORS to allow the React development server to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "ok", "gemini_enabled": analyzer.api_key is not None}

@app.post("/api/track-url", response_model=URLTrackResponse)
def track_url(payload: URLTrackRequest):
    """
    Track and compare the historical headline versions of a single article URL.
    """
    url = payload.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty.")
        
    try:
        print(f"Tracking URL: {url} with limit {payload.sample_limit}")
        history = scraper.track_url_history(url, sample_limit=payload.sample_limit)
        
        if not history:
            return URLTrackResponse(url=url, history=[], analysis=None)
            
        # Analyze the changes if we found history and have multiple versions
        analysis = None
        if len(history) >= 1:
            analysis = analyzer.analyze_headline_evolution(history)
            
        return URLTrackResponse(url=url, history=history, analysis=analysis)
    except Exception as e:
        print(f"Error tracking URL {url}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to track URL: {str(e)}")

@app.post("/api/search-topic", response_model=TopicSearchResponse)
def search_topic(payload: TopicSearchRequest):
    """
    Search news section archives near specific milestone dates for headlines matching a topic.
    """
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    if not payload.domains:
        raise HTTPException(status_code=400, detail="At least one domain must be selected.")
        
    try:
        results: Dict[str, List[Dict[str, Any]]] = {}
        
        # Iterate through milestones and scrape articles
        for period, date_str in payload.milestones.items():
            print(f"Scraping topic '{query}' for period '{period}' (date: {date_str})")
            period_results = []
            for domain in payload.domains:
                domain_results = scraper.scrape_topic_headlines_from_sections(domain, date_str, query)
                period_results.extend(domain_results)
            results[period] = period_results
            
        # Run AI analysis on the accumulated headlines by period
        analysis = analyzer.analyze_topic_drift(results)
        
        return TopicSearchResponse(query=query, results=results, analysis=analysis)
    except Exception as e:
        print(f"Error searching topic {query}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search topic: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
