FROM python:3.7.4-buster

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["python", "app.py", "-i", "0.0.0.0"]
