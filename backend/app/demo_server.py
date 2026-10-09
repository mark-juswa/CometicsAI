"""Serve this facade on Kaggle; never expose app.main directly to the internet."""
import os
from app.main import app as private_app
from app.demo_gateway import create_gateway

app = create_gateway(private_app, os.environ.get("AI_BACKEND_API_KEY", ""))
