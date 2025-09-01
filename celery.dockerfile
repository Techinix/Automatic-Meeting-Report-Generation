FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        gcc \
        libcairo2 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libgdk-pixbuf-xlib-2.0-0 \
        libffi-dev \
        libxml2-dev \
        libxslt1-dev \
        graphviz-dev \
        libgraphviz-dev \
        shared-mime-info && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


RUN pip install --upgrade pip
COPY ./requirements.txt /app
RUN pip install -r requirements.txt

# copy project
COPY . /app

EXPOSE 8000



# Make scripts executable
RUN chmod +x start.sh start-dev.sh


CMD ["./start.sh"]
