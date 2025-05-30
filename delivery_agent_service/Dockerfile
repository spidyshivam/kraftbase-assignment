# Use a lightweight Python base image
FROM python:3.13.3

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .


EXPOSE 8002 

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
