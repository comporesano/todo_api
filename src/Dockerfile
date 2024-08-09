FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev gcc

COPY ./src/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./src .

RUN pip install alembic

RUN pip install pytest httpx

CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app"]
