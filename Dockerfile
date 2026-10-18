FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY service ./service
RUN useradd --uid 1001 --create-home appuser && chgrp -R 0 /app && chmod -R g=u /app
USER 1001
EXPOSE 8080
CMD ["gunicorn", "--bind=0.0.0.0:8080", "--workers=1", "--access-logfile=-", "--error-logfile=-", "service:app"]
