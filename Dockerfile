# =================================================================
# Dockerfile النهائي (النسخة المصححة)
# =================================================================

# 1. البدء من صورة Airflow الرسمية
FROM apache/airflow:2.10.2-python3.10

# 2. تحديد متغيرات البيئة (لا يزال مهمًا)
ENV AIRFLOW_HOME=/home/airflow
ENV AIRFLOW__CORE__DAGS_FOLDER=${AIRFLOW_HOME}/dags
ENV AIRFLOW__CORE__PLUGINS_FOLDER=${AIRFLOW_HOME}/plugins
ENV AIRFLOW__LOGGING__BASE_LOG_FOLDER=${AIRFLOW_HOME}/logs

# --- (تم حذف الأوامر التي تسببت في الخطأ) ---
# المستخدم 'airflow' موجود بالفعل في الصورة الأساسية.

# 3. التبديل إلى المستخدم 'airflow' (مهم)
# هذا يضمن أن الأوامر التالية ستعمل بهذا المستخدم
USER airflow
WORKDIR ${AIRFLOW_HOME}

# 4. نسخ وتثبيت المكتبات
# لم نعد بحاجة إلى --chown لأننا بالفعل المستخدم الصحيح
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# 5. نسخ ملفات المشروع
COPY dags/ ${AIRFLOW__CORE__DAGS_FOLDER}/
COPY plugins/ ${AIRFLOW__CORE__PLUGINS_FOLDER}/
COPY scripts/ ${AIRFLOW_HOME}/scripts/
COPY Data/ ${AIRFLOW_HOME}/project/Data/

# 6. نسخ ملف entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 7. تحديد المنفذ ونقطة الدخول والأمر الافتراضي
EXPOSE 8080
ENTRYPOINT ["/entrypoint.sh"]
CMD ["webserver"]























# # ----------------------------------------------------------------
# # Dockerfile جديد ومُحسَّن لمشروعك
# # ----------------------------------------------------------------

# # 1. البدء من صورة Airflow الرسمية (هذا لم يتغير)
# FROM apache/airflow:2.10.2-python3.10

# # 2. تثبيت المكتبات الإضافية (هذا لم يتغير)
# COPY requirements.txt /requirements.txt
# RUN pip install --no-cache-dir -r /requirements.txt

# # 3. نسخ ملفات مشروعك (هذا لم يتغير)
# COPY dags/ ${AIRFLOW_HOME}/dags/
# COPY plugins/ ${AIRFLOW_HOME}/plugins/
# COPY scripts/ ${AIRFLOW_HOME}/scripts/
# COPY Data/ ${AIRFLOW_HOME}/project/Data/
# COPY model/ ${AIRFLOW_HOME}/project/model/
# COPY output/ ${AIRFLOW_HOME}/project/output/

# # --- التغييرات الجديدة تبدأ من هنا ---

# # 4. انسخ ملف التعليمات الجديد وامنحه صلاحية التنفيذ
# COPY entrypoint.sh /entrypoint.sh
# RUN chmod +x /entrypoint.sh

# # 5. حدد ملف التعليمات الجديد كنقطة الدخول (Entrypoint)
# ENTRYPOINT ["/entrypoint.sh"]

# # 6. حدد الأمر الافتراضي ليكون تشغيل واجهة الويب
# CMD ["webserver"]

# # --- انتهت التغييرات ---

# # 7. افتح المنفذ 8080 (هذا لم يتغير)
# EXPOSE 8080

