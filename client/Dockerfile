FROM python:3.9-slim
RUN useradd -ms /bin/bash apprunner
WORKDIR /app
COPY . /app
USER apprunner
CMD ["python3", "main.py"]