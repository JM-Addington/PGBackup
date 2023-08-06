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
    pigz \
    pv

RUN sleep 3s

RUN curl -fSsL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor | tee /usr/share/keyrings/postgresql.gpg > /dev/null
RUN echo deb [arch=amd64,arm64,ppc64el signed-by=/usr/share/keyrings/postgresql.gpg] http://apt.postgresql.org/pub/repos/apt/ jammy-pgdg main | tee -a /etc/apt/sources.list.d/postgresql.list
RUN sleep 3s
RUN apt update
RUN apt -y install postgresql-client-15
RUN sleep 3s

RUN mkdir /app
COPY app /app
RUN cd /app && chmod +x *.sh

ENTRYPOINT [ "/app/entrypoint.sh" ]
