FROM python:3.7.4-buster

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY ./backend .

RUN sed -i "s/CELERY_BROKER_URL.*/CELERY_BROKER_URL = 'redis:\/\/redis:6379\/0'/g" /app/factories/configuration.py
RUN sed -i "s/CELERY_RESULT_BACKEND.*/CELERY_RESULT_BACKEND = 'redis:\/\/redis:6379\/0'/g" /app/factories/configuration.py

RUN sed -i "s/redis:\/\/localhost/redis:\/\/redis/g" /app/factories/celery_config.py

EXPOSE 5000
CMD ["python", "app.py", "-i", "0.0.0.0"]
