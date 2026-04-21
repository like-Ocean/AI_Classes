FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PIP_NO_CACHE_DIR=1 \
	PIP_DISABLE_PIP_VERSION_CHECK=1

COPY requirements.txt .

RUN pip install --upgrade pip && \
	pip install --index-url https://download.pytorch.org/whl/cpu \
	--extra-index-url https://pypi.org/simple \
	-r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
