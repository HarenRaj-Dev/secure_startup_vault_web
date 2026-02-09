import os
import sys

# Ensure the project root is in the Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from vault import create_app
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create the app instance using the factory pattern
app = create_app()

# Export the app for Vercel WSGI handler
# This is required for Vercel serverless functions to work

if __name__ == "__main__":
    # College projects usually run on port 5000
    app.run(debug=True, port=5000)


    