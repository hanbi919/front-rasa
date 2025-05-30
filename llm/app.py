from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
# Assuming the original file is named hybrid_search_app.py
from main import HybridSearchApp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Hybrid Search API",
    description="API for hybrid search combining vector search and Qwen language model",
    version="1.0.0"
)

# Initialize the search app
search_app = HybridSearchApp()

# Request models


class SearchRequest(BaseModel):
    collection_name: str
    query_text: str
    similarity_threshold: Optional[float] = None
    default_limit: Optional[int] = None
    rerank_enabled: Optional[bool] = None

# Response model


class SearchResponse(BaseModel):
    mainService: str
    followQuestion: str
    qwenResponse: str
    searchResults: list


@app.post("/search", response_model=SearchResponse, summary="Perform hybrid search")
async def perform_search(request: SearchRequest):
    """
    Perform hybrid search with the following steps:
    1. Get embedding for the query
    2. Search in Milvus vector database
    3. Process and rerank results
    4. Generate response with Qwen language model
    
    Parameters:
    - collection_name: Name of the Milvus collection to search
    - query_text: The search query text
    - similarity_threshold: Optional threshold for result filtering (default: 0.5)
    - default_limit: Optional limit for number of results (default: 5)
    - rerank_enabled: Optional flag to enable/disable reranking (default: True)
    """
    try:
        # Update app parameters if provided in request
        if request.similarity_threshold is not None:
            search_app.similarity_threshold = request.similarity_threshold
        if request.default_limit is not None:
            search_app.default_limit = request.default_limit
        if request.rerank_enabled is not None:
            search_app.rerank_enabled = request.rerank_enabled

        # Perform the search
        result = search_app.hybrid_search(
            collection_name=request.collection_name,
            query_text=request.query_text
        )

        return result

    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/health", summary="Health check")
async def health_check():
    """Check if the service is healthy"""
    try:
        # Simple check by performing a small search
        test_result = search_app.hybrid_search(
            collection_name="optimized_excel",
            query_text="test"
        )
        return {"status": "healthy", "details": "Service is operational"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Service is unhealthy: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
