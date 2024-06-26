FROM python:3.12


RUN pip install poetry

COPY . /code
WORKDIR /code

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

ENV PYTHONPATH=/code/src

CMD ["uvicorn", "src.exhibit.app:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
