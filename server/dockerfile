
FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y gcc make && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . /app
RUN gcc -o server main.c

EXPOSE 8080

CMD ["./server"]