# One-shot migration + seed job. Build context: repository root.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY database/requirements.txt database/requirements.txt
RUN pip install --no-cache-dir -r database/requirements.txt

COPY alembic.ini .
COPY database/alembic database/alembic
COPY database/seeds database/seeds
COPY scripts/seed.py scripts/seed_api_gateway.py scripts/seed_bank_data.py scripts/

CMD ["sh", "-c", "alembic upgrade head && python scripts/seed.py"]
