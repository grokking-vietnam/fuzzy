FROM python:3.9-bullseye AS base

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1

FROM base AS python-deps

# Install poetry and compilation dependencies
RUN apt-get update && apt-get install gcc wget -y --no-install-recommends
RUN pip install --upgrade pip
RUN pip install poetry

# Install python dependencies in /.venv
COPY pyproject.toml .
COPY poetry.lock .
RUN poetry config virtualenvs.in-project true
RUN poetry install

FROM base AS runtime

# Copy virtual env from python-deps stage
COPY --from=python-deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH"

# Create and switch to a new user
RUN useradd --create-home milkrun
WORKDIR /home/milkrun
USER milkrun

# Install application into container
COPY .env .
COPY *.py .

ENTRYPOINT ["python", "r2_syncer.py"]
