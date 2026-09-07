FROM python:3.12-slim

WORKDIR /app

# Copied and installed before the rest of the code so Docker's build
# cache can reuse this layer whenever only application code changes,
# not requirements.txt.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "monsterforge.ui.app:app", "--host", "0.0.0.0", "--port", "8000"]
