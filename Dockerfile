FROM python:3.12-slim
WORKDIR /app
COPY server.py /app/server.py
COPY public /app/public
EXPOSE 8080
CMD ["python", "server.py", "--host", "0.0.0.0", "--port", "8080"]
