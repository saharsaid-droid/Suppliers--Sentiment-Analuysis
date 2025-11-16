# 1. اختيار الصورة الأساسية
FROM apache/airflow:2.10.2-python3.10

# 2. تثبيت المكتبات الإضافية
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# 3. نسخ ملفات المشروع إلى داخل الحاوية
COPY dags/ ${AIRFLOW_HOME}/dags/
COPY plugins/ ${AIRFLOW_HOME}/plugins/
COPY scripts/ ${AIRFLOW_HOME}/scripts/
COPY Data/ ${AIRFLOW_HOME}/project/Data/
COPY model/ ${AIRFLOW_HOME}/project/model/
COPY output/ ${AIRFLOW_HOME}/project/output/

# 4. إعطاء صلاحيات التنفيذ (اختياري)
RUN if [ -d "${AIRFLOW_HOME}/scripts" ]; then chmod +x ${AIRFLOW_HOME}/scripts/*.sh || true; fi

# 5. فتح المنفذ (Port)
EXPOSE 8080