# Use the official Debian slim image as a base
FROM debian:stable-slim

# Install dependencies
RUN apt-get update && \
    apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    libgl1 libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/autotag/


# Create a virtual environment and install dependencies
ENV VIRTUAL_ENV=venv
RUN python3 -m venv venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
COPY requirements.txt /usr/autotag/
RUN pip install --no-cache-dir -r requirements.txt


# Copy sources and resources
COPY config.json /usr/autotag/
COPY src/ /usr/autotag/src/


ENTRYPOINT ["/usr/autotag/venv/bin/python3", "/usr/autotag/src/main.py"]
