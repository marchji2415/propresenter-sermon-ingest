# Start from official Node 20 slim image
FROM node:20-slim

# Install Python 3, pip, and system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside container
WORKDIR /app

# Copy python requirements first to leverage Docker build cache
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

# Copy Next.js package files
COPY web_app/package*.json ./web_app/

# Install Next.js npm dependencies
WORKDIR /app/web_app
RUN npm ci

# Copy the rest of the workspace files
WORKDIR /app
COPY . .

# Build the Next.js application for production
WORKDIR /app/web_app
RUN npm run build

# Expose Next.js server port
EXPOSE 3000

# Environment variables
ENV PORT=3000
ENV PYTHON_PATH=python3
ENV NODE_ENV=production

# Start Next.js dev or prod server
CMD ["npm", "run", "start"]
