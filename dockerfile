FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN 

CMD ["python", "main.py"]
