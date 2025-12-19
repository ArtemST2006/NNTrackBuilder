FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*
COPY . .
RUN chmod +x ./alembic_upgrade.sh

CMD ["./alembic_upgrade.sh"]
