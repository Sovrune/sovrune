FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir .
ENV SOVRUNE_HOST=0.0.0.0 SOVRUNE_PORT=8787
EXPOSE 8787
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8787/healthz')"
CMD ["sovrune", "serve", "--host", "0.0.0.0"]
