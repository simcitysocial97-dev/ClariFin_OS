"""FastAPI REST API for Personal Finance Tracker - THIN FAÇADE.

This is the main API entry point. All implementation has been moved
to the app/ subpackage. This file maintains backward compatibility.

Run: python src/api.py
API Docs: http://localhost:8000/docs
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import and create the application
from app.factory import create_app

app = create_app()

# Run Server (for development)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
