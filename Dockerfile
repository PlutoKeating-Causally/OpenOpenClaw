FROM node:20-alpine AS builder
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --production

COPY frontend/ ./
RUN npm run build --prefix ./

RUN mkdir -p /app/data /app/data/exports /app/data/temp

RUN mkdir -p /root/.openclaw

COPY --from=builder /app/frontend/dist /app/frontend/dist

ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["sh", "-c", "mkdir -p /app/static && cp -r /app/frontend/dist/* /app/static/ && uvicorn main:app --host 0.0.0.0 --port 8080 --app-dir /app"]
