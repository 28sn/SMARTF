FROM python:3.11-slim

# تثبيت مكتبات النظام المطلوبة لـ opencv و pyzbar
RUN apt-get update && \
    apt-get install -y libzbar0 libglib2.0-0 libsm6 libxrender1 libxext6 ffmpeg && \
    pip install --upgrade pip

# نسخ ملفات المشروع
WORKDIR /app
COPY . /app

# تثبيت مكتبات بايثون
RUN pip install -r requirements.txt

# فتح البورت اللي تستخدمه Render (مطلوب 10000)
ENV PORT 10000

# تشغيل التطبيق باستخدام gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
