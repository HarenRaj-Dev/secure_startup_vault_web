from vault import create_app

# Create the app instance using the factory pattern
app = create_app()

# Export the app for Vercel WSGI handler
# This is required for Vercel serverless functions to work

if __name__ == "__main__":
    # College projects usually run on port 5000
    app.run(debug=True, port=5000)


    