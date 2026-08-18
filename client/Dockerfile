FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    python3-tk \
    libx11-6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -ms /bin/bash apprunner
    
WORKDIR /app
COPY . /app 

USER apprunner
CMD ["python3", "main.py"]