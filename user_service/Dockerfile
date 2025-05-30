# Use a lightweight Python base image
FROM python:3.13.3-alpine3.21

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose the port your FastAPI application runs on
EXPOSE 8000 

# Command to run your FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 
