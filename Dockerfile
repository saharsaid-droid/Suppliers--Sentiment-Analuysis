# استخدم الصورة الرسمية
FROM apache/airflow:2.10.2-python3.10

# اضبط مسار العمل
WORKDIR /opt/airflow

# فتح البورت للويب سيرفر
ENV PORT=8080
EXPOSE 8080

# نسخ ملفات المتطلبات
COPY requirements.txt .

# تثبيت الباكيجات
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# نسخ DAGs و Scripts
COPY dags/ /opt/airflow/dags/
COPY scripts/ /opt/airflow/scripts/

# تأكد أن السكريبتات قابلة للتنفيذ
RUN chmod +x /opt/airflow/scripts/*.sh

# CMD لتشغيل Airflow
# Webserver في الخلفية & Scheduler foreground
CMD ["bash", "-c", "airflow webserver --port 8080 & exec airflow scheduler"]

