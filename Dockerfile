# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Added --no-cache-dir to keep image size small
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Check if config exists, otherwise copy example (optional fallback, but we usually mount config)
# COPY example_config.json config.json

# Define environment variable
ENV RUN_CONTINUOUSLY=true
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "main.py"]
