FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
# We copy just the requirements.txt first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY ./app ./app
COPY ./data ./data

# Ensure the DB initialization is run during build/run if needed
# Better to run it on startup for persistency, but we can pre-build the local db
RUN python -m app.rag

# Expose port
EXPOSE 8000

# Run the FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
