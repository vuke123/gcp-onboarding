FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
COPY schema.py .
COPY .env.yaml .
CMD ["python", "main.py"]
