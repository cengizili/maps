FROM ubuntu:18.04
FROM python:3.10-slim

#=======================================
# Install Python and Basic Python Tools
#=======================================
RUN apt-get update
RUN apt-get -o Acquire::Check-Valid-Until=false -o Acquire::Check-Date=false update
RUN apt-get install -y python3 python3-pip python3-setuptools python3-dev 
RUN alias python=python3
RUN echo "alias python=python3" >> ~/.bashrc

#=================================
# Install Bash Command Line Tools
#=================================
RUN apt-get -qy --no-install-recommends install \
    sudo \
    unzip \
    wget \
    curl \
    libxi6 \
    libgconf-2-4 \
    vim \
    xvfb \
    lsof \
    procps \
  && rm -rf /var/lib/apt/lists/*

#================
# Install Chrome
#================
RUN curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list && \
    apt-get -yqq update && \
    apt-get -yqq install google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

#=================
# Install Firefox
#=================
RUN apt-get -qy --no-install-recommends install \
     $(apt-cache depends firefox | grep Depends | sed "s/.*ends:\ //" | tr '\n' ' ') \
  && rm -rf /var/lib/apt/lists/* \
  && cd /tmp \
  && wget --no-check-certificate -O firefox-esr.tar.bz2 \
    'https://download.mozilla.org/?product=firefox-esr-latest&os=linux64&lang=en-US' \
  && tar -xjf firefox-esr.tar.bz2 -C /opt/ \
  && ln -s /opt/firefox/firefox /usr/bin/firefox \
  && rm -f /tmp/firefox-esr.tar.bz2

#===========================
# Configure Virtual Display
#===========================
RUN set -e
RUN echo "Starting X virtual framebuffer (Xvfb) in background..."
RUN Xvfb -ac :99 -screen 0 1280x1024x16 > /dev/null 2>&1 &
RUN export DISPLAY=:99
RUN exec "$@"

#=====================
# Download WebDrivers
#=====================

RUN wget https://chromedriver.storage.googleapis.com/112.0.5615.28/chromedriver_linux64.zip
RUN unzip chromedriver_linux64.zip
RUN chmod +x chromedriver
RUN mv chromedriver /usr/local/bin/

# Use the official lightweight Python image.
# https://hub.docker.com/_/python

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True
 
ENV VIRTUAL_ENV=/home/cengizclickbank/katchy/sbase_env
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

# Install production dependencies.
COPY requirements.txt .
RUN pip install -r requirements.txt

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
CMD gunicorn --bind :5000 --workers 1 --threads 8 --timeout 0 main:app