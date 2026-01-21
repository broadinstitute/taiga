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

# Install Python 3.10 via pyenv
ENV PYTHON_VERSION=3.10.19
RUN pyenv install ${PYTHON_VERSION} && \
    pyenv global ${PYTHON_VERSION} && \
    pyenv rehash

RUN pip install poetry

COPY flask setup_env.sh autoapp.py pyproject.toml README.md /install/taiga/
copy taiga2 /install/taiga/taiga2
WORKDIR /install/taiga

# Create virtual enviornment in /install/taiga/.venv so that it's in a known path
RUN python -m venv .venv
# "activate" it
ENV VIRTUAL_ENV=/install/taiga/.venv
ENV PATH=$VIRTUAL_ENV/bin:$PATH
# now poetry will always use the current activated virtual env
RUN poetry install 

#RUN bash -c 'ln -s `poetry env info --path` /install/venv'
#ENV PATH=/install/venv/bin:$PATH
#RUN ls /install/venv/bin
#RUN pytest

# Set celery as being able to run as root => Can find a better way?
ENV C_FORCE_ROOT=true
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

EXPOSE 8080

