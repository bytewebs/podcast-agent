FROM apache/airflow:2.8.0

# Switch to root to install system dependencies
USER root
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Switch back to airflow user
USER airflow

# Install Python dependencies
COPY requirements.airflow.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
RUN pip install --no-cache-dir pydub
