FROM apache/airflow:2.10.2-python3.10

WORKDIR /opt/airflow
COPY requirements.txt .

RUN pip install  --upgrade pip
RUN pip install --no-cache-dir   -r requirements.txt