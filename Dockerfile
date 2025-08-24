FROM python:3.13-slim-bookworm

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "application.py"]
