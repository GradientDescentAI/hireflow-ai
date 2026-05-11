"""
Dev launcher — loads .env then starts uvicorn.
Run: python start_api.py
"""
import os
import sys

# Load .env before anything else imports os.environ
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)

# Make sure packages/ is importable
sys.path.insert(0, os.path.dirname(__file__))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "apps.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["apps/api", "packages"],
    )
