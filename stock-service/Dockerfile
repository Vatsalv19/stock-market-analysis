FROM python:3.11-slim

WORKDIR /app

# Copy requirements FIRST (Docker caching trick)
# If requirements don't change, Docker skips reinstalling
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the actual code
COPY main.py .

# Expose port 8000 (where FastAPI runs)
EXPOSE 8000

# Run the FastAPI app using uvicorn server
# --host 0.0.0.0 means accept connections from outside the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]