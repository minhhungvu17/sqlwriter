FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps for Postgres client libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Install Node.js for building webcomponent
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

# Install local vanna from repo (instead of PyPI)
COPY ./vanna /app/vanna

# Build webcomponent before installing Python package
WORKDIR /app/vanna/frontends/webcomponent
RUN npm install && npm run build
WORKDIR /app

RUN pip install --no-cache-dir -e /app/vanna[fastapi,openai,postgres,chromadb]

# Install remaining Python dependencies
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application
COPY . /app

# Default port
ENV PORT=8001
EXPOSE 8001

# Run
CMD ["python", "main.py"]

