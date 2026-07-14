from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class URLTrackRequest(BaseModel):
    url: str
    sample_limit: Optional[int] = 15

class URLTrackResponse(BaseModel):
    url: str
    history: List[Dict[str, Any]]
    analysis: Optional[Dict[str, Any]] = None

class TopicSearchRequest(BaseModel):
    query: str
    domains: List[str]
    milestones: Dict[str, str]  # dict mapping period key to YYYYMMDD date string

class TopicSearchResponse(BaseModel):
    query: str
    results: Dict[str, List[Dict[str, Any]]]
    analysis: Optional[Dict[str, Any]] = None
