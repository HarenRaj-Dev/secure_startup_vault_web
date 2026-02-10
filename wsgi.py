"""
WSGI entry point for Vercel deployment.
Vercel's Python runtime looks for an application callable.
"""
from run import app
from werkzeug.middleware.proxy_fix import ProxyFix

# Apply ProxyFix to handle Vercel's proxy headers (HTTPS, etc.)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Export the Flask app instance for Vercel to use
application = app

# Alternative name that some tools look for
wsgi_app = app
