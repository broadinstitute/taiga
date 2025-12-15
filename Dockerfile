FROM debian:trixie

# Set environment to non-interactive
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies for pyenv and Python builds
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libffi-dev \
    liblzma-dev \
    libatomic1 \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

# Install pyenv
ENV PYENV_ROOT=/root/.pyenv
ENV PATH=$PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH
RUN curl https://pyenv.run | bash

# Install Python 3.9.15 via pyenv
ENV PYTHON_VERSION=3.9.15
RUN pyenv install ${PYTHON_VERSION} && \
    pyenv global ${PYTHON_VERSION} && \
    pyenv rehash

RUN pip install supervisor==4.3.0

COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

COPY flask setup_env.sh autoapp.py pyproject.toml README.md taiga2 /install/taiga/
WORKDIR /install/taiga

# should we build the JS inside the docker image or outside?
# Let's assume outside for now. That means that taiga2/static/js/react_frontend.js
# is getting bundled in along with the python code and we don't need the following

#COPY react_frontend /install/taiga/react_frontend/
# Install frontend javascript dependencies
#RUN cd /install/taiga/react_frontend && yarn install

#RUN cd /install/taiga/react_frontend && ./node_modules/.bin/webpack

# Set celery as being able to run as root => Can find a better way
ENV C_FORCE_ROOT=true
# Set where celery can find the settings
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Configure supervisor

EXPOSE 8080

CMD ["/usr/bin/supervisord"]

