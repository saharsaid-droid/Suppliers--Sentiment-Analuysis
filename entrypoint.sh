#!/bin/bash

# هذه هي الخطوة التي تهيئ قاعدة بيانات SQLite تلقائيًا
airflow db upgrade

# هذه الخطوة تنشئ المستخدم (سيتم تجاهلها إذا كان موجودًا بالفعل)
airflow users create \
    --username admin \
    --password admin \
    --firstname Sahar \
    --lastname Admin \
    --role Admin \
    --email sahar21325@gmail.com || true

# هذه هي الخطوة الأخيرة التي تشغل واجهة الويب
exec airflow webserver