# Multi-stage build for frontend and backend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend-nextjs/package*.json ./
RUN npm install
COPY frontend-nextjs/ ./
RUN npm run build

# Backend stage
FROM mcr.microsoft.com/azure-functions/python:4-python3.11-slim AS backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set up the working directory
WORKDIR /home/site/wwwroot

# Copy Python requirements first for better caching
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code
COPY backend/ .

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/frontend/out ./static/

# Expose the port
EXPOSE 7071

# Start the Azure Functions host
CMD ["func", "start", "--host", "0.0.0.0"] 