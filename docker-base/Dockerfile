
FROM ubuntu:xenial-20170619

RUN apt-get update -y
RUN apt-get install -y \
    software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update -y 

# Install R dependencies
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 51716619E084DAB9 && \
    echo "deb http://cran.rstudio.com/bin/linux/ubuntu xenial/" | tee -a /etc/apt/sources.list && \
    apt-get update -y && \
    apt-get -y install r-base r-base-dev
RUN echo "r <- getOption('repos'); r['CRAN'] <- 'http://cran.us.r-project.org'; options(repos = r);" > ~/.Rprofile && \
    Rscript -e "source(\"https://bioconductor.org/biocLite.R\"); biocLite(\"rhdf5\")"

# Preparing for yarn install
RUN apt-get install -y curl apt-transport-https build-essential && \
    curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - && \
    echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list && \
    apt-get update -y

# Install Nodejs/npm
RUN curl -sL https://deb.nodesource.com/setup_10.x -o nodesource_setup.sh && \
    bash nodesource_setup.sh && \
    apt-get install -y nodejs && rm nodesource_setup.sh 

# Install vim
# Install python and its related packages
# Install postgresql minimal set binaries and headers
RUN apt-get install -y vim python3.6 libpq-dev python3.6-dev python3.6-venv supervisor redis-server yarn

RUN mkdir /install && python3.6 -m venv /install/python
ENV PATH=/install/python/bin:$PATH

# Install supervisor
RUN mkdir -p /var/log/supervisor && mkdir -p /var/run

# Install base versions of all python libs
COPY requirements.txt /install/taiga/
RUN pip install pip==21.1.2
RUN pip install -r /install/taiga/requirements.txt
