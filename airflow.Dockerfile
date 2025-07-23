FROM apache/airflow:2.8.0

USER airflow
COPY requirements.airflow.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
