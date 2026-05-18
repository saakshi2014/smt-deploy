FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/requirements.txt

RUN pip install --no-cache-dir -r backend/requirements.txt

COPY . .

ENV FLASK_APP=backend/app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app/backend

EXPOSE 5000

CMD ["python", "backend/app.py"]