# Use Python official image as base
FROM python:3.11

# Set the working directory inside the container
WORKDIR /app

# Copy the application files
COPY . /app

# Copy env
COPY .env /app/.env

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn requests python-dotenv

# Expose the application port
EXPOSE 8000

# Default command to run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
