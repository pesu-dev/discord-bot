FROM python:3.12-slim-bookworm

COPY src /src
COPY README.md /README.md
RUN pip install -r src/requirements.txt
WORKDIR /src
CMD ["python", "application.py"]
