"""
Hugging Face Spaces Entry Point (Free Tier CPU Fallback Mode).
Runs FastAPI server in Gradio / Hugging Face Spaces environment.
"""
import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
