"""
WSGI entry point for Vercel deployment.
Vercel's Python runtime looks for an application callable.
"""
from run import app

# Export the Flask app instance for Vercel to use
application = app

# Alternative name that some tools look for
wsgi_app = app
