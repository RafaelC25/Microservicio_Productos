FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Asegurar permisos del directorio data
RUN mkdir -p /app/data && chmod -R a+rw /app/data

CMD ["python", "app.py"]