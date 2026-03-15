import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="Agentic AI POC",
    description="A POC demonstrating an autonomous AI agent with MLOps best practices.",
    version="1.0.0"
)

# Ensure the static directory exists
# We need to compute an absolute path to the static folder relative to the app module
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")

# Mount the static files correctly
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    """Serves the frontend UI."""
    index_path = os.path.join(static_dir, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="index.html not found.")
    return FileResponse(index_path)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    
@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint to interact with the Agentic AI.
    Eventually, this will route the message to the LangGraph agent.
    """
    try:
        from app.agent import get_agent_app
        from langchain_core.messages import HumanMessage
        
        # Invoke the LangGraph agent
        try:
            app_graph = get_agent_app()
            messages = [HumanMessage(content=request.message)]
            result = app_graph.invoke({"messages": messages})
            
            # Get the final response string from the agent
            agent_reply = result["messages"][-1].content
        except Exception as api_err:
            error_msg = str(api_err)
            if "401" in error_msg or "Authentication" in error_msg:
                agent_reply = "⚠️ Authentication Error: Your OpenRouter API Key is invalid or missing."
            else:
                agent_reply = f"⚠️ Agent Execution Error: {error_msg}"
                
        return ChatResponse(response=agent_reply)
    except Exception as e:
        # Instead of a 500 or 401 HTTP error, return a graceful UI string
        # This ensures the frontend doesn't break and can render the warning
        error_msg = str(e)
        if "401" in error_msg or "Authentication" in error_msg:
            return ChatResponse(response="⚠️ Authentication Error: Your OpenRouter API Key is invalid or missing.")
        return ChatResponse(response=f"⚠️ Server Error: {error_msg}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
