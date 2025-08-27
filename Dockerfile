FROM ubuntu:24.04

# Install dependencies
RUN apt update && apt dist-upgrade -y
RUN apt -y install \
    dirmngr \
    ca-certificates \
    gnupg \
    gnupg2 \
    apt-transport-https \
    curl \
    wget \
    pigz \
    python3 \
    python3-venv \
    vim \
    cron

RUN curl -fSsL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor | tee /usr/share/keyrings/postgresql.gpg > /dev/null
RUN echo deb [arch=amd64,arm64,ppc64el signed-by=/usr/share/keyrings/postgresql.gpg] http://apt.postgresql.org/pub/repos/apt/ noble-pgdg main | tee -a /etc/apt/sources.list.d/postgresql.list
RUN apt update && apt clean

# Create a virtual environment to avoid installing Python packages at the system level
RUN python3 -m venv /venv && /venv/bin/pip install --upgrade pip
ENV PATH="/venv/bin:$PATH"

RUN mkdir /app
RUN mkdir /scripts
COPY scripts /scripts
COPY app /app
RUN cd /app && chmod +x *.sh
WORKDIR /app

# ENTRYPOINT [ "/app/entrypoint.sh" ]
ENTRYPOINT [ "/venv/bin/python", "/app/entrypoint.py" ]
