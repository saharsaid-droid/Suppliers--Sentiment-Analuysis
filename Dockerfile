# =================================================================
# Dockerfile النهائي لمشروعك (مناسب لـ Azure App Service)
# =================================================================

# 1. البدء من صورة Airflow الرسمية
FROM apache/airflow:2.10.2-python3.10

# 2. تحديد متغيرات البيئة لـ Airflow (مهم للتخزين الدائم)
# هذا يخبر Airflow أين يضع ملفاته داخل الحاوية
ENV AIRFLOW_HOME=/home/airflow
ENV AIRFLOW__CORE__DAGS_FOLDER=${AIRFLOW_HOME}/dags
ENV AIRFLOW__CORE__PLUGINS_FOLDER=${AIRFLOW_HOME}/plugins
ENV AIRFLOW__LOGGING__BASE_LOG_FOLDER=${AIRFLOW_HOME}/logs

# 3. إنشاء مستخدم مخصص (أفضل من الناحية الأمنية)
# بدلاً من تشغيل كل شيء كمستخدم root
USER root
RUN useradd -ms /bin/bash -d ${AIRFLOW_HOME} airflow && \
    chown -R airflow: ${AIRFLOW_HOME}

# 4. التبديل إلى المستخدم الجديد
USER airflow
WORKDIR ${AIRFLOW_HOME}

# 5. نسخ وتثبيت المكتبات
# نستخدم --chown لضمان أن المستخدم الجديد يمتلك هذه الملفات
COPY --chown=airflow:airflow requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# 6. نسخ ملفات المشروع
# نستخدم --chown هنا أيضًا
COPY --chown=airflow:airflow dags/ ${AIRFLOW__CORE__DAGS_FOLDER}/
COPY --chown=airflow:airflow plugins/ ${AIRFLOW__CORE__PLUGINS_FOLDER}/
COPY --chown=airflow:airflow scripts/ ${AIRFLOW_HOME}/scripts/
COPY --chown=airflow:airflow Data/ ${AIRFLOW_HOME}/project/Data/
# لقد اتفقنا على عدم نسخ الموديل، لذلك السطر التالي محذوف
# COPY --chown=airflow:airflow model/ ${AIRFLOW_HOME}/project/model/

# 7. نسخ ملف entrypoint
COPY --chown=airflow:airflow entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 8. تحديد المنفذ ونقطة الدخول والأمر الافتراضي
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

