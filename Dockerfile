FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*


RUN pip install poetry

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

COPY . .

RUN poetry install --no-interaction --no-ansi

CMD ["poetry", "run", "python", "src/__main__"]