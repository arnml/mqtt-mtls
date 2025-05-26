FROM python:3.11-slim
RUN pip install paho-mqtt
COPY client.py /app/client.py
WORKDIR /app
CMD ["python", "client.py"]
