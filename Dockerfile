# Use the official Debian slim image as a base
FROM debian:stable-slim

# Install dependencies
RUN apt-get update && \
    apt-get install -y \
    python3 \
    python3-pip \
    libgl1 libglib2.0-0 \
    python3-venv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/autotag/

ENV VIRTUAL_ENV=venv

# Create a virtual environment and install dependencies
RUN python3 -m venv venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy and install dependencies into the container
COPY requirements.txt /usr/autotag/
RUN pip install --no-cache-dir -r requirements.txt 

# Copy sources and resources
COPY config.json /usr/autotag/
COPY src/ /usr/autotag/src/

ENTRYPOINT ["/usr/autotag/venv/bin/python3", "/usr/autotag/src/main.py"]


# docker build --rm -t pdfix-autotag-textract . 
# docker run -it  -v $(pwd):/usr/pdfix -w /usr/pdfix autotag-textract-arm64 autotag -i input.pdf -o output.pdf
