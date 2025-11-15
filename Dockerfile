FROM apache/airflow:2.10.2-python3.10

ENV PORT=8080
WORKDIR /opt/airflow
COPY requirements.txt .

RUN pip install  --upgrade pip
RUN pip install --no-cache-dir   -r requirements.txt  

# copy DAG file
COPY dags/ /opt/airflow/dags/

# copy scripts file
COPY scripts/ /opt/airflow/scripts/
