# Step 1: Start FROM an existing image (base image)
# We use official Python 3.11 slim (smaller size)
FROM python:3.11-slim

# Step 2: Set working directory INSIDE the container
# Like doing 'cd /app' inside the container
WORKDIR /app

# Step 3: COPY our code from Windows into the container
COPY app.py .

# Step 4: Tell Docker what command to run when container starts
CMD ["python", "app.py"]