# FROM python:3.9-slim

# WORKDIR /app

# # System dependencies
# RUN apt-get update && apt-get install -y \
#     gcc \
#     g++ \
#     && rm -rf /var/lib/apt/lists/*

# # Install pip packages with cache
# ENV PIP_CACHE_DIR=/tmp/pipcache

# # Copy only the requirements file first to leverage Docker caching
# COPY requirements.txt .

# # Install dependencies and cache pip packages
# RUN pip install --upgrade pip && \
#     pip install --prefer-binary -r requirements.txt

# # Copy the rest of the application (after installing dependencies)
# COPY . .

# # Debug: Make sure api exists
# RUN ls -la /app/api

# # Set environment variables for Python
# EXPOSE 5000
# ENV PYTHONUNBUFFERED=1
# ENV PYTHONPATH=/app

# # Entry point to run the app
# CMD ["python", "api/app.py"]
# FROM python:3.9-slim

# WORKDIR /app

# # System dependencies
# RUN apt-get update && apt-get install -y \
#     gcc \
#     g++ \
#     && rm -rf /var/lib/apt/lists/*

# # Install pip packages with cache
# ENV PIP_CACHE_DIR=/tmp/pipcache

# # Copy only the requirements file first to leverage Docker caching
# COPY requirements.txt .

# # Install dependencies and cache pip packages
# RUN pip install --upgrade pip && \
#     pip install --prefer-binary -r requirements.txt

# # Install langchain (added line)
# RUN pip install langchain

# # Install langchain_openai (added line)
# RUN pip install langchain_openai

# # Copy the rest of the application (after installing dependencies)
# COPY . .

# # Debug: Make sure api exists
# RUN ls -la /app/api

# # Set environment variables for Python
# EXPOSE 5000
# ENV PYTHONUNBUFFERED=1
# ENV PYTHONPATH=/app

# # Entry point to run the app
# CMD ["python", "api/app.py"]
FROM python:3.9-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install pip packages with cache
ENV PIP_CACHE_DIR=/tmp/pipcache

# Copy only the requirements file first to leverage Docker caching
COPY requirements.txt .

# Install dependencies and cache pip packages in a single RUN command
RUN pip install --upgrade pip && \
    pip install --prefer-binary -r requirements.txt && \
    pip install langchain langchain_openai

# Copy the rest of the application (after installing dependencies)
COPY . .

# Debug: Make sure api exists
RUN ls -la /app/api

# Set environment variables for Python
EXPOSE 5000
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Entry point to run the app
CMD ["python", "api/app.py"]
