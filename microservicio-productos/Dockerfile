FROM python:3.13-slim

WORKDIR /app
# Install dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
ENV DB_URI=$DB_URI 
COPY . .

EXPOSE 8000

CMD ["gunicorn", "--bind=0.0.0.0:8000", "products:app"] 