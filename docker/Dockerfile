FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    R_ROOT=/usr/bin

RUN apt-get update && apt-get install -y --no-install-recommends \
    r-base-core \
    r-cran-jsonlite \
    r-cran-car \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
COPY r_engine ./r_engine

RUN pip install --no-cache-dir -e ".[figure,test]"

RUN useradd --create-home --uid 10001 researchstat
USER researchstat

CMD ["python", "-c", "import researchstat; print(researchstat.__version__)"]
