FROM ubuntu:xenial-20170619

RUN apt-get update -y
RUN apt-get install -y \
    software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update -y 

# Install R dependencies
RUN gpg --keyserver keyserver.ubuntu.com --recv-key E084DAB9 && \ 
    gpg -a --export E084DAB9 | apt-key add - && \
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

# Use the tar to get the source code of taiga
COPY taiga2 /install/taiga/taiga2
COPY requirements.txt setup.py /install/taiga/
WORKDIR /install/taiga

RUN pip install -r requirements.txt

COPY react_frontend /install/taiga/react_frontend/
# Install frontend javascript dependencies
RUN cd /install/taiga/react_frontend && yarn install

RUN cd /install/taiga/react_frontend && ./node_modules/.bin/webpack

COPY flask setup_env.sh autoapp.py /install/taiga/
# Now we are using the right db, should use instead settings.cfg
#RUN python3.5 taiga2/create_test_db_sqlalchemy.py settings.cfg

# Build our frontend distribution
#RUN ln -s /usr/bin/nodejs /usr/bin/node
#RUN node_modules/.bin/webpack
#RUN export PATH="$(yarn global bin):$PATH"
#RUN yarn add webpack@2.2.1 --dev
# We build the production version TODO: Remove the exit 0
#RUN ./node_modules/.bin/webpack --config webpack.config.prod.js; exit 0

# Set celery as being able to run as root => Can find a better way
ENV C_FORCE_ROOT=true
# Set where celery can find the settings
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Configure supervisor
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 8080

CMD ["/usr/bin/supervisord"]

