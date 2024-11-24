FROM ubuntu:22.04

# Install dependencies
RUN apt update
RUN apt -y install dirmngr \
    ca-certificates \
    software-properties-common \
    gnupg \
    gnupg2 \
    apt-transport-https \
    curl \
    wget \
    pigz \
    cron 

RUN curl -fSsL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor | tee /usr/share/keyrings/postgresql.gpg > /dev/null
RUN echo deb [arch=amd64,arm64,ppc64el signed-by=/usr/share/keyrings/postgresql.gpg] http://apt.postgresql.org/pub/repos/apt/ jammy-pgdg main | tee -a /etc/apt/sources.list.d/postgresql.list
RUN apt update

RUN mkdir /app
RUN mkdir /scripts
COPY scripts /scripts
COPY app /app
RUN cd /app && chmod +x *.sh
WORKDIR /app

# ENTRYPOINT [ "/app/entrypoint.sh" ]
ENTRYPOINT [ "/usr/bin/python3", "/app/entrypoint.py" ]
